// Dedicated streaming proxy for the narration SSE stream (WS-STREAM consumer #1).
//
// ARCHITECTURE (WS2-locked): the narration stream must traverse App Runner, not
// the cloudflared `aimez.ai` path that buffers SSE. So this route's upstream is
// an App Runner base URL from ORCAST_STREAM_BASE (NOT ORCAST_API_BASE, which is
// the cloudflared host used by the generic /api/be proxy for everything else).
//
// It injects X-ORCAST-Key server-side (the key never reaches the browser) and
// pipes `resp.body` straight through with streaming headers — never
// `await resp.text()`, which would buffer. The non-stream API stays on /api/be.
//
// App Router gotcha: this folder is `narrate-stream` with NO leading underscore;
// a leading underscore would make it a private folder and the route would 404.

import { NextRequest } from "next/server";

// Node.js runtime (not edge): edge has a 25s TTFB gate and no maxDuration knob.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const STREAM_BASE = process.env.ORCAST_STREAM_BASE ?? "";
const API_KEY = process.env.ORCAST_API_KEY ?? "";

// WS6 B1: this route bypasses the generic /api/be proxy (App Runner lane), so it
// must enforce its own abuse bounds BEFORE injecting the key. Best-effort,
// in-memory, per-process (mirrors the /api/be limiter posture). The backend
// stream route additionally enforces the per-session turn quota.
const RATE_LIMIT_PER_MIN = Number(process.env.ORCAST_STREAM_RATE_PER_MIN ?? "12");
const MAX_CONCURRENT_PER_IP = Number(process.env.ORCAST_STREAM_MAX_CONCURRENT_PER_IP ?? "3");
const RATE_WINDOW_MS = 60_000;

const rateBuckets = new Map<string, { count: number; resetAt: number }>();
const inFlight = new Map<string, number>();

function clientIp(req: NextRequest): string {
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) return fwd.split(",")[0].trim();
  return req.headers.get("x-real-ip") ?? "unknown";
}

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const bucket = rateBuckets.get(ip);
  if (!bucket || now >= bucket.resetAt) {
    rateBuckets.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return false;
  }
  bucket.count += 1;
  return bucket.count > RATE_LIMIT_PER_MIN;
}

export async function POST(req: NextRequest): Promise<Response> {
  if (!STREAM_BASE) {
    return new Response(JSON.stringify({ error: "ORCAST_STREAM_BASE not configured" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Abuse bounds first — before the key is injected or any upstream call is made.
  const ip = clientIp(req);
  if (isRateLimited(ip)) {
    return new Response(JSON.stringify({ error: "Rate limit exceeded" }), {
      status: 429,
      headers: { "Content-Type": "application/json" },
    });
  }
  const active = inFlight.get(ip) ?? 0;
  if (active >= MAX_CONCURRENT_PER_IP) {
    return new Response(JSON.stringify({ error: "Too many concurrent streams" }), {
      status: 429,
      headers: { "Content-Type": "application/json" },
    });
  }
  inFlight.set(ip, active + 1);
  let released = false;
  // Release the per-IP concurrency slot exactly once: on stream end, on client
  // disconnect, or on an upstream error.
  const releaseSlot = () => {
    if (released) return;
    released = true;
    const n = (inFlight.get(ip) ?? 1) - 1;
    if (n <= 0) inFlight.delete(ip);
    else inFlight.set(ip, n);
  };
  req.signal.addEventListener("abort", releaseSlot, { once: true });

  const upstream = `${STREAM_BASE.replace(/\/$/, "")}/api/interactions/narrate/stream`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (API_KEY) headers["X-ORCAST-Key"] = API_KEY;

  let resp: Response;
  try {
    resp = await fetch(upstream, {
      method: "POST",
      headers,
      body: await req.text(),
      cache: "no-store",
      // Propagate a client disconnect upstream so a mid-stream turn-abort cancels
      // the backend generator.
      signal: req.signal,
    });
  } catch (err) {
    releaseSlot();
    return new Response(JSON.stringify({ error: "upstream_unreachable" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!resp.body) {
    releaseSlot();
    return new Response(resp.body, { status: resp.status });
  }

  // Pass resp.body straight through with streaming headers, releasing the
  // concurrency slot when the stream closes (identity transform; flush on end).
  const release = new TransformStream({
    flush() {
      releaseSlot();
    },
  });
  return new Response(resp.body.pipeThrough(release), {
    status: resp.status,
    headers: {
      "Content-Type": resp.headers.get("Content-Type") ?? "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

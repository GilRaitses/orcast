// WS2 throwaway probe — CANDIDATE dedicated Next.js stream route.
//
// PURPOSE
//   Method #1 of the WS2 shortlist (dedicated_next_stream_route). Proves whether
//   Vercel + the Next route handler pass an SSE byte stream through unbuffered,
//   by piping the upstream `resp.body` instead of `await resp.text()` (the
//   confirmed buffer at web/app/api/be/[...path]/route.ts:176).
//
// STATUS: SCRATCH CANDIDATE. This file is NOT installed under web/app. To run
//   the Step-3 benchmark, O0 copies it to web/app/api/__streamprobe/route.ts on
//   a THROWAWAY Vercel preview branch, measures, then deletes it. It is never
//   merged to main and never touches the generic /api/be convergence file.
//
// CONTRAST WITH THE PROD PROXY (web/app/api/be/[...path]/route.ts)
//   - That route does `const body = await resp.text()` (line 176) then returns a
//     buffered NextResponse — nothing streams. This candidate returns
//     `resp.body` directly with streaming headers.
//   - This candidate skips auth/allow-list/rate-limit on purpose: it is a
//     throwaway transport probe, not a production route. The real /narrate/stream
//     path will add `api/interactions/narrate(/stream)` to the public allow-list
//     (route.ts:59-69) per WS1 R3.
//
// WIRING (Step 3, O0 only): point UPSTREAM at the cloudflared probe backend, e.g.
//   UPSTREAM = `${process.env.ORCAST_API_BASE}/__stream_probe`
//   (ORCAST_API_BASE = https://orcast-api.aimez.ai)

import { NextRequest } from "next/server";

// Node.js runtime (NOT edge): edge has a 25s TTFB gate + 300s cap and no
// maxDuration knob. Node.js + Fluid Compute default 300s is ample for a ~5.5s
// reply. (WS1 R2.)
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const API_BASE = process.env.ORCAST_API_BASE ?? "";

async function proxyStream(req: NextRequest): Promise<Response> {
  if (!API_BASE) {
    return new Response(JSON.stringify({ error: "ORCAST_API_BASE not configured" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Forward query params (count, interval) to the uvicorn probe.
  const upstream = new URL(`${API_BASE.replace(/\/$/, "")}/__stream_probe`);
  req.nextUrl.searchParams.forEach((v, k) => upstream.searchParams.set(k, v));

  const init: RequestInit = {
    method: req.method,
    headers: { Accept: "text/event-stream" },
    cache: "no-store",
    // Propagate client disconnect upstream so a mid-stream abort cancels the
    // backend generator (the real path will do the same for turn-abort).
    signal: req.signal,
  };
  if (req.method === "POST") {
    init.body = await req.text();
    (init.headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const resp = await fetch(upstream.toString(), init);

  // THE FIX: pass resp.body straight through. Do NOT call resp.text()/json().
  return new Response(resp.body, {
    status: resp.status,
    headers: {
      "Content-Type": resp.headers.get("Content-Type") ?? "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

export async function GET(req: NextRequest): Promise<Response> {
  return proxyStream(req);
}

export async function POST(req: NextRequest): Promise<Response> {
  return proxyStream(req);
}

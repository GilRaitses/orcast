// WS4 step-0 throwaway: dedicated Next stream route -> App Runner upstream.
// Tests whether Vercel passes an SSE byte stream through unbuffered via
// resp.body passthrough. Upstream = ${ORCAST_API_BASE}/__stream_probe.
import { NextRequest } from "next/server";

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

  const upstream = new URL(`${API_BASE.replace(/\/$/, "")}/__stream_probe`);
  req.nextUrl.searchParams.forEach((v, k) => upstream.searchParams.set(k, v));

  const init: RequestInit = {
    method: req.method,
    headers: { Accept: "text/event-stream" },
    cache: "no-store",
    signal: req.signal,
  };
  if (req.method === "POST") {
    init.body = await req.text();
    (init.headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const resp = await fetch(upstream.toString(), init);

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

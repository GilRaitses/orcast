import { NextRequest, NextResponse } from "next/server";
import { resolveReviewer, reviewerProxyHeaders } from "@/lib/agentAuth";

export const dynamic = "force-dynamic";

const API_BASE = process.env.ORCAST_API_BASE ?? "";
const API_KEY = process.env.ORCAST_API_KEY ?? "";

/** Keyed surface planner proxy — WorkOS session or X-ORCAST-Agent-Key; injects X-ORCAST-Key. */
export async function POST(req: NextRequest) {
  if (!API_BASE || !API_KEY) {
    return NextResponse.json({ error: "ORCAST_API_BASE or ORCAST_API_KEY not configured" }, { status: 500 });
  }

  const reviewer = await resolveReviewer(req);
  if (!reviewer) {
    return NextResponse.json({ error: "Authentication required" }, { status: 401 });
  }

  const body = await req.text();
  const target = `${API_BASE.replace(/\/$/, "")}/api/interactions/plan`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-ORCAST-Key": API_KEY,
    ...reviewerProxyHeaders(reviewer),
  };

  const resp = await fetch(target, { method: "POST", headers, body, cache: "no-store" });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": resp.headers.get("Content-Type") ?? "application/json" },
  });
}

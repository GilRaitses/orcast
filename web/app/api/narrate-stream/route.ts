// TEMP DIAGNOSTIC (WS7): isolate config-vs-code for the 500. Reverted after probe.
import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function POST(req: NextRequest): Promise<Response> {
  try {
    const hasBase = Boolean(process.env.ORCAST_STREAM_BASE);
    const hasKey = Boolean(process.env.ORCAST_API_KEY);
    let bodyLen = -1;
    try {
      bodyLen = (await req.text()).length;
    } catch {
      bodyLen = -2;
    }
    return new Response(
      JSON.stringify({
        diag: true,
        hasBase,
        baseTail: (process.env.ORCAST_STREAM_BASE ?? "").slice(-18),
        hasKey,
        signalType: typeof (req as unknown as { signal?: unknown }).signal,
        bodyLen,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ diag: true, error: String((err as Error)?.message ?? err) }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
}

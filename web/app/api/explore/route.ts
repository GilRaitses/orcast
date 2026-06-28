import { NextRequest, NextResponse } from "next/server";
import { generateText } from "ai";
import { createGateway } from "@ai-sdk/gateway";

const API_BASE = process.env.ORCAST_API_BASE ?? "";
const GATEWAY_KEY = process.env.AI_GATEWAY_API_KEY ?? "";
const DEFAULT_MODEL =
  process.env.ORCAST_EXPLORE_GATEWAY_MODEL ?? "anthropic/claude-haiku-4.5";

const SYSTEM_PROMPT = `You are the ORCAST Exploration Guide. You help users navigate gates, provenance, and map context.

Rules (never break these):
1. You are NOT a forecast oracle. You explain what the gates and provenance already show.
2. Use ONLY facts from the JSON tool outputs. If data is missing, say you don't know.
3. Always be clear that the forecast is modeled, not a direct observation, and that it is a likelihood, not a certainty. Do not discuss model promotion or the difference between effective and raw confidence.
4. Link users to /gates for gate details and to the map for provenance.
5. Never suggest approving moderation, promotion, or writing decision records.
6. Keep replies under 250 words, plain language, 2-4 short paragraphs.
7. End with a "Navigate" bullet list of deep links (labels from context).`;

export const dynamic = "force-dynamic";

function gatewayEnabled(): boolean {
  return Boolean(GATEWAY_KEY && API_BASE);
}

export async function GET() {
  const models = (process.env.ORCAST_EXPLORE_GATEWAY_MODELS ?? DEFAULT_MODEL)
    .split(",")
    .map((m) => m.trim())
    .filter(Boolean);
  return NextResponse.json({
    status: "success",
    ai_gateway_enabled: gatewayEnabled(),
    models,
    default_model: models[0] ?? DEFAULT_MODEL,
    narration_path: gatewayEnabled() ? "vercel_ai_gateway" : "app_runner_bedrock",
  });
}

export async function POST(req: NextRequest) {
  if (!gatewayEnabled()) {
    return NextResponse.json(
      { error: "AI Gateway not configured (AI_GATEWAY_API_KEY + ORCAST_API_BASE required)" },
      { status: 503 }
    );
  }

  const body = await req.json();
  const sessionId = body.session_id as string | undefined;
  const message = (body.message as string | undefined)?.trim();
  const modelId = (body.model as string | undefined)?.trim() || DEFAULT_MODEL;

  if (!sessionId || !message) {
    return NextResponse.json({ error: "session_id and message required" }, { status: 400 });
  }

  const prepareRes = await fetch(`${API_BASE}/api/explore/prepare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      viewport: body.viewport,
      focus: body.focus,
    }),
    cache: "no-store",
  });

  if (!prepareRes.ok) {
    const detail = await prepareRes.text();
    return NextResponse.json(
      { error: "prepare failed", detail: detail.slice(0, 500) },
      { status: prepareRes.status }
    );
  }

  const prepared = await prepareRes.json();
  const userContent = `User question:\n${message}\n\nTool JSON (cite only these facts):\n${JSON.stringify(
    prepared.context,
    null,
    2
  )}`;

  const gw = createGateway({ apiKey: GATEWAY_KEY });
  let text: string;
  try {
    ({ text } = await generateText({
      model: gw(modelId),
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: userContent }],
      maxOutputTokens: 700,
      temperature: 0.3,
    }));
  } catch (err) {
    const message = err instanceof Error ? err.message : "AI Gateway generation failed";
    return NextResponse.json({ error: "gateway generation failed", detail: message.slice(0, 500) }, { status: 502 });
  }

  const turnRes = await fetch(`${API_BASE}/api/explore/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      viewport: body.viewport,
      focus: body.focus,
      gateway_reply: text,
      gateway_model: modelId,
    }),
    cache: "no-store",
  });

  if (!turnRes.ok) {
    const detail = await turnRes.text();
    return NextResponse.json(
      { error: "turn persist failed", detail: detail.slice(0, 500), reply: text, source: "ai_gateway" },
      { status: turnRes.status }
    );
  }

  const turn = await turnRes.json();
  return NextResponse.json({
    ...turn,
    source: turn.source ?? "ai_gateway",
    model: turn.model ?? modelId,
    narration_path: "vercel_ai_gateway",
  });
}

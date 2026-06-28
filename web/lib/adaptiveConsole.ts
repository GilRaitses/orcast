// Adaptive console turn driver. Every explore turn runs one round-trip through
// the public surface planner (plan ui_intent + dispatch skill_plan + narrate),
// reusing existing infra rather than a meta-orchestrator (HANDOFF_CHARTER B3).

import { postJSON } from "@/lib/api";
import type { ExploreSessionResponse } from "@/lib/api";
import type { PlanResponse } from "@/lib/uiIntent";
import type { SceneIntent } from "@/lib/sceneIntent";
import { enrichTurnContext } from "@/lib/intent/transducer";
import { readSseStream } from "@/lib/sseTransport";

// Inline public planner spec sent for anonymous-first turns. Only public T0/T1
// skills + public panels, so the backend public_route guard never has to reject
// and no keyed T2/T3 data is reachable without a signed-in reviewer.
export const PUBLIC_PLANNER_SPEC = {
  instructions:
    "You are the ORCAST public explore planner. Allocate read-only panels and " +
    "public skills for anonymous users. Prefer gates + provenance + trace " +
    "panels. When a map pin or hydrophone is selected, include map_viewport and " +
    "provenance/hydrophone panels. When the turn carries an orienting-question " +
    "branch (visiting, here-now, kayak, curious), surface the matching trip " +
    "panel (compare_places, local_area, connections_plan, kayak_plan, " +
    "sidequests) with its honesty label. Never request decision, dossier, or " +
    "moderation skills.",
  // All T0/public skills. The trip branches need fetch_environmental (kayak)
  // and fetch_live_hydrophones / fetch_verified_sightings (curious); without
  // them those skills are filtered out and the branch panels never surface.
  skills: [
    "fetch_gates",
    "fetch_hotspots",
    "fetch_provenance",
    "fetch_environmental",
    "fetch_live_hydrophones",
    "fetch_verified_sightings",
  ],
  version: "public-2",
  policy: {
    write_tools: false,
    planner_mode: true,
    allowed_deep_links: ["/gates", "/explore", "/glossary", "/"],
    allowed_panels: [
      "map_viewport",
      "explore_trace",
      "gates_summary",
      "provenance_pin",
      "provenance_graph",
      "hydrophone_signal",
      // Trips (anonymous-public): the orienting-question branches surface these.
      "compare_places",
      "local_area",
      "connections_plan",
      "kayak_plan",
      "sidequests",
    ],
  },
} as const;

export interface TurnContext {
  message: string;
  viewport?: { lat: number; lng: number; zoom?: number } | null;
  // `branch` carries the orienting-question selection (visiting / here-now /
  // kayak / curious) so the planner runs the trip branch; absent => keyword plan.
  focus?: { cell?: string; branch?: string } | null;
}

export async function ensureSession(current: string | null): Promise<string> {
  if (current) return current;
  const res = await postJSON<ExploreSessionResponse>("api/explore/sessions", {
    title: "Explore (adaptive console)",
  });
  return res.session_id;
}

// Phase 1 of a turn: plan only. Returns validated panels + grounded prepare
// context fast (~hundreds of ms) WITHOUT the ~5s Bedrock narration, so the
// caller can paint panels immediately. Narration is fetched separately via
// runAdaptiveNarration so first paint is never gated on the model.
export async function runAdaptiveTurn(
  sessionId: string,
  ctx: TurnContext,
): Promise<PlanResponse> {
  // Additive B.7 implicit-intent feed: fold the live camera's dwell focus into
  // the turn context. No-op when no Camera Director is registered, and never
  // overrides an explicit viewport/focus, so existing turn behavior is preserved.
  const enriched = enrichTurnContext(ctx);
  const body = {
    session_id: sessionId,
    message: enriched.message,
    agent: PUBLIC_PLANNER_SPEC,
    viewport: enriched.viewport ?? undefined,
    focus: enriched.focus ?? undefined,
    narrate: false,
  };
  const res = await fetch("/api/be/api/interactions/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`adaptive turn -> ${res.status}`);
  }
  return (await res.json()) as PlanResponse;
}

export interface NarrationResult {
  reply: string;
  source?: string;
  model?: string;
}

// Phase 2 of a turn: narration. Reuses the grounded context already returned by
// runAdaptiveTurn so the backend only runs the narration model (no skills or
// live source calls re-run). Called after panels render; its latency does not
// block first paint.
export async function runAdaptiveNarration(
  sessionId: string,
  ctx: TurnContext,
  plan: PlanResponse,
): Promise<NarrationResult> {
  const enriched = enrichTurnContext(ctx);
  const prep = plan.prepare;
  const body = {
    session_id: sessionId,
    message: enriched.message,
    agent: PUBLIC_PLANNER_SPEC,
    viewport: enriched.viewport ?? undefined,
    focus: enriched.focus ?? undefined,
    skill_plan: plan.ui_intent.skill_plan ?? [],
    context: prep.context ?? {},
    citations: prep.citations ?? [],
    deep_links: prep.deep_links ?? [],
    tools_used: prep.tools_used ?? [],
    gate_ids: prep.gate_ids ?? [],
    provenance_refs: prep.provenance_refs ?? [],
  };
  const res = await fetch("/api/be/api/interactions/narrate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`adaptive narration -> ${res.status}`);
  }
  const json = (await res.json()) as { reply?: string; source?: string; model?: string };
  return { reply: json.reply ?? "", source: json.source, model: json.model };
}

export interface NarrationMeta {
  interaction_id?: string;
  citations?: Array<Record<string, unknown>>;
  deep_links?: Array<Record<string, unknown>>;
  source?: string;
  model?: string;
}

export interface NarrationStreamHandlers {
  onMeta?: (meta: NarrationMeta) => void;
  onToken: (text: string) => void;
}

// Streaming variant of Phase 2. Reuses the same grounded context body as
// runAdaptiveNarration but reads incremental tokens over SSE from the dedicated
// /api/narrate-stream route (App Runner lane, Cloudflare-free). Resolves with the
// assembled reply on `done`; rejects on stream error so the caller can fall back
// to the non-streamed JSON path. Accepts an AbortSignal for turn cancellation.
export async function runAdaptiveNarrationStream(
  sessionId: string,
  ctx: TurnContext,
  plan: PlanResponse,
  handlers: NarrationStreamHandlers,
  signal?: AbortSignal,
): Promise<NarrationResult> {
  const enriched = enrichTurnContext(ctx);
  const prep = plan.prepare;
  const body = {
    session_id: sessionId,
    message: enriched.message,
    agent: PUBLIC_PLANNER_SPEC,
    viewport: enriched.viewport ?? undefined,
    focus: enriched.focus ?? undefined,
    skill_plan: plan.ui_intent.skill_plan ?? [],
    context: prep.context ?? {},
    citations: prep.citations ?? [],
    deep_links: prep.deep_links ?? [],
    tools_used: prep.tools_used ?? [],
    gate_ids: prep.gate_ids ?? [],
    provenance_refs: prep.provenance_refs ?? [],
  };

  let reply = "";
  let source: string | undefined;
  let model: string | undefined;

  await readSseStream(
    "/api/narrate-stream",
    body,
    {
      onMeta: (meta) => {
        const m = meta as NarrationMeta;
        source = m.source ?? source;
        model = m.model ?? model;
        handlers.onMeta?.(m);
      },
      onToken: (text) => {
        reply += text;
        handlers.onToken(text);
      },
      onDone: (data) => {
        const d = (data ?? {}) as { reply?: string; source?: string; model?: string };
        if (d.reply) reply = d.reply;
        source = d.source ?? source;
        model = d.model ?? model;
      },
    },
    signal,
  );

  return { reply, source, model };
}

// Lightweight client-side intent label for the scene -> turn bridge. The
// authoritative planning still happens server-side; this only seeds the message
// and focus so a click reads naturally in the trace.
export function intentToTurn(intent: SceneIntent): TurnContext {
  if (intent.type === "hydrophone") {
    return {
      message: `Show the hydrophone signal for ${intent.name ?? "this station"}.`,
      viewport: { lat: intent.lat, lng: intent.lng, zoom: 11 },
      focus: { cell: `${intent.lat},${intent.lng}` },
    };
  }
  return {
    message: `What does the forecast and provenance show at ${intent.lat.toFixed(3)}, ${intent.lng.toFixed(3)}?`,
    viewport: { lat: intent.lat, lng: intent.lng, zoom: 11 },
    focus: { cell: `${intent.lat},${intent.lng}` },
  };
}

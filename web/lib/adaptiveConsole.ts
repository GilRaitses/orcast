// Adaptive console turn driver. Every explore turn runs one round-trip through
// the public surface planner (plan ui_intent + dispatch skill_plan + narrate),
// reusing existing infra rather than a meta-orchestrator (HANDOFF_CHARTER B3).

import { postJSON } from "@/lib/api";
import type { ExploreSessionResponse } from "@/lib/api";
import type { PlanResponse } from "@/lib/uiIntent";
import type { SceneIntent } from "@/lib/sceneIntent";
import { enrichTurnContext } from "@/lib/intent/transducer";

// Inline public planner spec sent for anonymous-first turns. Only public T0/T1
// skills + public panels, so the backend public_route guard never has to reject
// and no keyed T2/T3 data is reachable without a signed-in reviewer.
export const PUBLIC_PLANNER_SPEC = {
  instructions:
    "You are the ORCAST public explore planner. Allocate read-only panels and " +
    "public skills for anonymous users. Prefer gates + provenance + trace " +
    "panels. When a map pin or hydrophone is selected, include map_viewport and " +
    "provenance/hydrophone panels. Never request decision, dossier, or " +
    "moderation skills.",
  skills: ["fetch_gates", "fetch_hotspots", "fetch_provenance"],
  version: "public-1",
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
    ],
  },
} as const;

export interface TurnContext {
  message: string;
  viewport?: { lat: number; lng: number; zoom?: number } | null;
  focus?: { cell: string } | null;
}

export async function ensureSession(current: string | null): Promise<string> {
  if (current) return current;
  const res = await postJSON<ExploreSessionResponse>("api/explore/sessions", {
    title: "Explore (adaptive console)",
  });
  return res.session_id;
}

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
    narrate: true,
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

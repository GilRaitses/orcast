import type { InteractionAnnotation, InteractionStep } from "@/lib/api";
import type { MapViewport } from "@/lib/viewport";

export interface UiIntentPanel {
  id: string;
  surface: "map" | "sidebar";
  priority?: number;
  props?: Record<string, unknown>;
  viewport?: { lat: number; lng: number; zoom?: number };
}

export interface UiIntent {
  version: string;
  planner_agent_id: string;
  skill_plan: string[];
  panels: UiIntentPanel[];
  deep_links?: Array<{ label: string; href: string }>;
  focus?: { cell: string };
}

export interface PlanPreparePayload {
  context: Record<string, unknown>;
  citations: Array<{ label: string; href: string }>;
  deep_links: Array<{ label: string; href: string }>;
  tools_used: string[];
  steps: InteractionStep[];
  annotations: InteractionAnnotation[];
}

export interface PlanResponse {
  status: string;
  ui_intent: UiIntent;
  resolved_spec_hash: string;
  managed_agent_id: string;
  agent_version: string;
  hydration_mode: string;
  prepare: PlanPreparePayload;
  reply?: string;
}

const PANEL_LABELS: Record<string, string> = {
  map_viewport: "Map viewport",
  explore_trace: "Interaction trace",
  gates_summary: "Fitness gates",
  provenance_pin: "Provenance pin",
  decisions_table: "Decision audit log",
  review_dossier: "Review dossier",
  moderation_queue: "Moderation queue",
  provenance_graph: "Metric provenance graph",
  hydrophone_signal: "Hydrophone signal",
  compare_places: "Compare places",
  local_area: "Local area",
  connections_plan: "Connection plan",
  kayak_plan: "Kayak window",
  sidequests: "Sidequests",
};

export function panelLabel(id: string): string {
  return PANEL_LABELS[id] ?? id.replace(/_/g, " ");
}

export function sortPanels(panels: UiIntentPanel[]): UiIntentPanel[] {
  return [...panels].sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99));
}

export function mapViewportFromIntent(intent: UiIntent): MapViewport | null {
  const mapPanel = intent.panels.find((p) => p.id === "map_viewport" && p.viewport);
  if (mapPanel?.viewport) {
    return {
      lat: mapPanel.viewport.lat,
      lng: mapPanel.viewport.lng,
      zoom: mapPanel.viewport.zoom ?? 10,
    };
  }
  if (intent.focus?.cell) {
    const [lat, lng] = intent.focus.cell.split(",").map((s) => parseFloat(s.trim()));
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      return { lat, lng, zoom: 10 };
    }
  }
  return null;
}

export function sidebarPanels(intent: UiIntent): UiIntentPanel[] {
  return sortPanels(intent.panels.filter((p) => p.surface === "sidebar"));
}

"use client";

import Link from "next/link";
import type { GatesResponse, ProvenanceResponse } from "@/lib/api";
import type { PlanPreparePayload } from "@/lib/uiIntent";
import { panelLabel, sidebarPanels, type UiIntent, type UiIntentPanel } from "@/lib/uiIntent";
import { ProvenanceGraphFromPrepare } from "@/app/components/ProvenanceGraph";
import OrchestratorTrace from "@/app/components/console/OrchestratorTrace";
import HydrophoneSignalPanel, {
  type HydrophoneSignalProps,
} from "@/app/components/console/HydrophoneSignalPanel";
import KayakPanel, { type KayakPanelProps } from "@/app/components/console/KayakPanel";
import SidequestPanel, {
  type SidequestPanelProps,
} from "@/app/components/console/SidequestPanel";
import GatedAction from "@/app/components/ui/GatedAction";

// Copy/visibility tier for the active surface. "public" is the anonymous home
// console and hides reviewer internals (raw agent ids, skill manifest, schema
// version, promotion and confidence internals). "reviewer" keeps the detail for
// the dedicated keyed surfaces.
type Audience = "public" | "reviewer";

interface ActiveSurfaceHostProps {
  uiIntent: UiIntent;
  prepare: PlanPreparePayload;
  reply?: string;
  signedIn?: boolean;
  audience?: Audience;
  onDeepLink?: (href: string) => void;
}

function pct(value: number | null | undefined): string {
  if (value == null) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function GatesSummaryPanel({
  gates,
  audience,
}: {
  gates?: GatesResponse;
  audience: Audience;
}) {
  if (!gates) {
    return <p className="muted">No gate context for this turn.</p>;
  }
  if (audience === "public") {
    return (
      <div className="console-metrics">
        <p className="muted" style={{ fontSize: "0.82rem", margin: 0 }}>
          This forecast is modeled, not a direct observation. It is a likelihood, not a certainty.
        </p>
        {gates.caveats && gates.caveats.length > 0 && (
          <p className="muted" style={{ fontSize: "0.78rem" }}>
            Conditions to keep in mind. {gates.caveats.join(". ")}
          </p>
        )}
      </div>
    );
  }
  const battery = gates.gates ?? {};
  const rows: Array<{ label: string; pass: boolean | null | undefined }> = [
    { label: "Cross-validation skill", pass: battery.cross_validation?.gate_pass },
    { label: "Time-rescaling GoF", pass: battery.time_rescaling?.pooled_pass_exp },
    { label: "PIT calibration", pass: battery.pit?.calibrated },
  ];
  return (
    <div className="console-metrics">
      <div className="console-metric-row">
        <span>Effective confidence</span>
        <strong>{pct(gates.effective_confidence ?? gates.confidence)}</strong>
      </div>
      <div className="console-metric-row">
        <span>Promotion</span>
        <span className={`badge ${gates.promoted ? "pass" : "warn"}`}>
          {gates.promoted ? "promoted" : "held"}
        </span>
      </div>
      <ul className="console-gate-list">
        {rows.map((r) => (
          <li key={r.label}>
            <span className={`gate-dot ${r.pass ? "ok" : r.pass === false ? "fail" : "unknown"}`} />
            {r.label}
          </li>
        ))}
      </ul>
      {gates.caveats && gates.caveats.length > 0 && (
        <p className="muted" style={{ fontSize: "0.78rem" }}>
          Conditions: {gates.caveats.join("; ")}
        </p>
      )}
    </div>
  );
}

function ProvenancePinPanel({
  provenance,
  signedIn,
}: {
  provenance?: ProvenanceResponse;
  signedIn: boolean;
}) {
  if (!provenance) {
    return <p className="muted">Click the scene or a map pin to ground provenance here.</p>;
  }
  const active = provenance.kernel_contributions.filter((k) => k.available);
  return (
    <div className="console-metrics">
      <div className="console-metric-row">
        <span>Intensity</span>
        <strong>{provenance.intensity?.toFixed(3) ?? "n/a"}</strong>
      </div>
      <div className="console-metric-row">
        <span>Confidence</span>
        <strong>{pct(provenance.effective_confidence ?? provenance.confidence)}</strong>
      </div>
      {active.length > 0 && (
        <ul className="console-gate-list">
          {active.slice(0, 4).map((k) => (
            <li key={k.kernel}>
              <span className={`gate-dot ${k.beats_null ? "ok" : "unknown"}`} />
              {k.kernel}
              {k.beats_null != null && (
                <span className="muted"> {k.beats_null ? "beats null" : "no signal"}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {provenance.trace_note && (
        <p className="muted" style={{ fontSize: "0.78rem" }}>
          {provenance.trace_note}
        </p>
      )}
      <div className="row" style={{ marginTop: "0.5rem" }}>
        <GatedAction
          label="Submit a sighting here"
          signedIn={signedIn}
          reason="Sign in to submit a sighting at this location"
          redirectTo="/explore"
        />
      </div>
    </div>
  );
}

type HonestyLabel = "measured" | "published" | "modeled" | "heuristic";

const LABEL_BADGE: Record<string, string> = {
  measured: "pass",
  published: "pass",
  modeled: "warn",
  heuristic: "caution",
};

function HonestyBadge({ label }: { label?: string | null }) {
  if (!label) {
    return <span className="badge unknown" title="No honesty label resolved">unknown</span>;
  }
  return (
    <span className={`badge ${LABEL_BADGE[label] ?? "unknown"}`} title={`Honesty label: ${label}`}>
      {label}
    </span>
  );
}

interface ConnectionLeg {
  leg?: string;
  from?: string | number | null;
  to?: string | number | null;
  label?: HonestyLabel | null;
  eta_minutes?: number | null;
  interval_minutes?: [number, number] | null;
  basis?: string | null;
}

interface ConnectionFeasibility {
  verdict?: string;
  reason?: string;
  sailing_departure?: string | null;
  arrival_estimate?: string | null;
  margin_minutes?: number | null;
  worst_case_margin_minutes?: number | null;
}

interface ConnectionPlan {
  mode?: string;
  composite_label?: HonestyLabel | null;
  freshness?: string | null;
  feasibility?: ConnectionFeasibility | null;
  legs?: ConnectionLeg[];
  honesty_notes?: string[];
}

const VERDICT_BADGE: Record<string, string> = {
  likely: "pass",
  tight: "caution",
  unlikely: "fail",
  unknown: "unknown",
};

function formatStamp(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function ConnectionsPlanPanel({ plan }: { plan?: ConnectionPlan | null }) {
  if (!plan) {
    return <p className="muted">No connection plan for this turn. Ask the console to make a sailing or flight.</p>;
  }
  const feas = plan.feasibility;
  const verdict = feas?.verdict ?? "unknown";
  const legs = plan.legs ?? [];
  const freshness = formatStamp(plan.freshness);
  return (
    <div className="console-metrics">
      <div className="console-metric-row">
        <span>Overall</span>
        <HonestyBadge label={plan.composite_label} />
      </div>
      <div className="console-metric-row">
        <span>Make the connection</span>
        <span className={`badge ${VERDICT_BADGE[verdict] ?? "unknown"}`}>{verdict}</span>
      </div>
      {feas?.reason && (
        <p className="muted" style={{ fontSize: "0.8rem", margin: "0.3rem 0 0" }}>
          {feas.reason}
        </p>
      )}
      <ul className="console-gate-list" style={{ gap: "0.4rem", marginTop: "0.4rem" }}>
        {legs.map((leg, i) => (
          <li
            key={`${leg.leg ?? "leg"}-${i}`}
            style={{ alignItems: "flex-start", flexDirection: "column", gap: "0.2rem" }}
          >
            <div className="row" style={{ gap: "0.5rem", alignItems: "center" }}>
              <HonestyBadge label={leg.label} />
              <strong style={{ fontSize: "0.84rem" }}>{leg.leg ?? "leg"}</strong>
            </div>
            <span className="muted" style={{ fontSize: "0.78rem" }}>
              {leg.from != null && leg.to != null ? `${leg.from} to ${leg.to}. ` : ""}
              {leg.eta_minutes != null
                ? `About ${Math.round(leg.eta_minutes)} min`
                : leg.leg === "drive"
                  ? "Drive estimate unknown"
                  : ""}
              {leg.interval_minutes
                ? `, range ${Math.round(leg.interval_minutes[0])} to ${Math.round(leg.interval_minutes[1])} min`
                : ""}
            </span>
          </li>
        ))}
      </ul>
      {freshness && (
        <p className="muted" style={{ fontSize: "0.76rem", marginTop: "0.4rem" }}>
          Freshest measured reading {freshness}.
        </p>
      )}
      {plan.honesty_notes && plan.honesty_notes.length > 0 && (
        <ul className="console-gate-list" style={{ marginTop: "0.3rem" }}>
          {plan.honesty_notes.map((note, i) => (
            <li key={i}>
              <span className="gate-dot unknown" />
              <span className="muted" style={{ fontSize: "0.76rem" }}>{note}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PlacesPanel({
  scope,
  prepare,
  audience,
}: {
  scope: "broad" | "focused";
  prepare: PlanPreparePayload;
  audience: Audience;
}) {
  const ctx = prepare.context as Record<string, unknown>;
  const hotspots = Array.isArray(ctx.hotspots) ? (ctx.hotspots as unknown[]) : [];
  return (
    <div className="console-metrics">
      <p className="muted" style={{ fontSize: "0.82rem", margin: 0 }}>
        {scope === "broad"
          ? "Comparing whale-viewing places across the archipelago."
          : "Local viewing zones and today's remaining sailings near you."}
      </p>
      <div className="console-metric-row" style={{ marginTop: "0.4rem" }}>
        <span>Forecast cells</span>
        <strong>{hotspots.length > 0 ? hotspots.length : "n/a"}</strong>
      </div>
      <p className="muted" style={{ fontSize: "0.76rem", marginTop: "0.3rem" }}>
        {audience === "public"
          ? "Today's forecast is modeled from recent patterns, not a live sighting feed. It is a likelihood, not a certainty."
          : "Forecast stays on the hotspot heuristic with its confidence gate. No model is promoted."}
      </p>
    </div>
  );
}

// ---- BSS studio panels (managed HUD skills). Honest NC attribution shown. ----

interface TagtoolsStepCtx {
  status?: string;
  title?: string;
  truth_label?: string;
  reproduces_h5_path?: string | null;
  summary?: Record<string, unknown>;
  attribution?: string;
  license?: string;
}

interface PosterVizCtx {
  status?: string;
  title?: string;
  render?: string;
  truth_label?: string;
  source_script?: string;
  box_key?: string;
  js_port_status?: string;
  attribution?: string;
  license?: string;
}

interface BehaviorCaptureCtx {
  status?: string;
  behavior?: string;
  dive_id?: number;
  max_depth_m?: number;
  dive_window_s?: number[];
  truth_label?: string;
  honesty?: string;
  stages?: Array<{ stage?: string; intent?: string; director_call?: string }>;
  attribution?: string;
  license?: string;
}

function AttributionLine({ license, attribution }: { license?: string; attribution?: string }) {
  if (!license && !attribution) return null;
  return (
    <p className="muted bsw-studio-attr" style={{ fontSize: "0.72rem", marginTop: "0.4rem" }}>
      {license ? `${license}. ` : ""}
      {attribution ?? ""}
    </p>
  );
}

function TagtoolsStepPanel({ ctx }: { ctx?: TagtoolsStepCtx }) {
  if (!ctx || ctx.status !== "success") {
    return <p className="muted">No tagtools step for this turn.</p>;
  }
  const summary = ctx.summary ?? {};
  return (
    <div className="console-metrics bsw-studio-panel">
      <div className="console-metric-row">
        <span>{ctx.title ?? "Tagtools step"}</span>
        <HonestyBadge label={ctx.truth_label} />
      </div>
      {ctx.reproduces_h5_path && (
        <p className="muted" style={{ fontSize: "0.78rem", margin: "0.2rem 0 0" }}>
          Reproduces {ctx.reproduces_h5_path}
        </p>
      )}
      <ul className="console-gate-list" style={{ marginTop: "0.4rem" }}>
        {Object.entries(summary)
          .slice(0, 6)
          .map(([k, v]) => (
            <li key={k}>
              <span className="gate-dot ok" />
              <span style={{ fontSize: "0.78rem" }}>
                {k.replace(/_/g, " ")} {typeof v === "object" ? JSON.stringify(v) : String(v)}
              </span>
            </li>
          ))}
      </ul>
      <AttributionLine license={ctx.license} attribution={ctx.attribution} />
    </div>
  );
}

function PosterVizPanel({ ctx }: { ctx?: PosterVizCtx }) {
  if (!ctx || ctx.status !== "success") {
    return <p className="muted">No poster visualization for this turn.</p>;
  }
  return (
    <div className="console-metrics bsw-studio-panel">
      <div className="console-metric-row">
        <span>{ctx.title ?? "Poster visualization"}</span>
        <HonestyBadge label={ctx.truth_label} />
      </div>
      <p className="muted" style={{ fontSize: "0.78rem", margin: "0.2rem 0 0" }}>
        Baked from {ctx.source_script ?? "R script"}, render {ctx.render ?? "baked"}.
        {ctx.js_port_status ? ` Interactive port ${ctx.js_port_status}.` : ""}
      </p>
      {ctx.box_key && (
        <p className="muted bsw-studio-box" style={{ fontSize: "0.72rem", marginTop: "0.3rem" }}>
          {ctx.box_key}
        </p>
      )}
      <AttributionLine license={ctx.license} attribution={ctx.attribution} />
    </div>
  );
}

function BehaviorCapturePanel({ ctx }: { ctx?: BehaviorCaptureCtx }) {
  if (!ctx || ctx.status !== "success") {
    return <p className="muted">No behavior capture for this turn.</p>;
  }
  const win = ctx.dive_window_s;
  return (
    <div className="console-metrics bsw-studio-panel">
      <div className="console-metric-row">
        <span>{ctx.behavior ?? "Behavior"}</span>
        <HonestyBadge label={ctx.truth_label} />
      </div>
      <p className="muted" style={{ fontSize: "0.78rem", margin: "0.2rem 0 0" }}>
        Dive {ctx.dive_id ?? "n/a"}
        {ctx.max_depth_m != null ? `, max depth ${ctx.max_depth_m} m` : ""}
        {win && win.length === 2 ? `, window ${win[0]} to ${win[1]} s` : ""}
      </p>
      <ul className="console-gate-list" style={{ marginTop: "0.4rem" }}>
        {(ctx.stages ?? []).map((s, i) => (
          <li key={`${s.stage ?? "stage"}-${i}`}>
            <span className="gate-dot ok" />
            <span style={{ fontSize: "0.78rem" }}>
              {s.stage?.replace(/_/g, " ")} {s.director_call ? `via ${s.director_call}` : ""}
            </span>
          </li>
        ))}
      </ul>
      {ctx.honesty && (
        <p className="muted" style={{ fontSize: "0.74rem", marginTop: "0.3rem" }}>
          {ctx.honesty}
        </p>
      )}
      <AttributionLine license={ctx.license} attribution={ctx.attribution} />
    </div>
  );
}

function renderPanel(
  panel: UiIntentPanel,
  prepare: PlanPreparePayload,
  reply: string | undefined,
  signedIn: boolean,
  audience: Audience,
) {
  const ctx = prepare.context as Record<string, unknown>;
  switch (panel.id) {
    case "tagtools_step":
      return <TagtoolsStepPanel ctx={ctx.run_tagtools_step as TagtoolsStepCtx | undefined} />;
    case "poster_viz":
      return <PosterVizPanel ctx={ctx.render_poster_viz as PosterVizCtx | undefined} />;
    case "behavior_capture":
      return <BehaviorCapturePanel ctx={ctx.capture_behavior as BehaviorCaptureCtx | undefined} />;
    case "gates_summary":
      return <GatesSummaryPanel gates={ctx.gates as GatesResponse | undefined} audience={audience} />;
    case "provenance_pin":
      return (
        <ProvenancePinPanel
          provenance={ctx.provenance as ProvenanceResponse | undefined}
          signedIn={signedIn}
        />
      );
    case "provenance_graph":
      return <ProvenanceGraphFromPrepare prepare={prepare} />;
    case "explore_trace":
      return <OrchestratorTrace steps={prepare.steps} reply={reply} audience={audience} />;
    case "hydrophone_signal":
      return (
        <HydrophoneSignalPanel
          props={panel.props as HydrophoneSignalProps | undefined}
          signedIn={signedIn}
        />
      );
    case "connections_plan":
      return (
        <ConnectionsPlanPanel
          plan={(panel.props as { plan?: ConnectionPlan | null } | undefined)?.plan}
        />
      );
    case "compare_places":
      return <PlacesPanel scope="broad" prepare={prepare} audience={audience} />;
    case "local_area":
      return <PlacesPanel scope="focused" prepare={prepare} audience={audience} />;
    case "kayak_plan":
      return <KayakPanel props={panel.props as KayakPanelProps | undefined} />;
    case "sidequests":
      return (
        <SidequestPanel
          props={panel.props as SidequestPanelProps | undefined}
          signedIn={signedIn}
          audience={audience}
        />
      );
    case "map_viewport":
      return (
        <p className="muted" style={{ fontSize: "0.82rem" }}>
          Camera focused on{" "}
          {panel.viewport
            ? `${panel.viewport.lat.toFixed(3)}, ${panel.viewport.lng.toFixed(3)}`
            : "the selected cell"}
          .
        </p>
      );
    default:
      return null;
  }
}

export default function ActiveSurfaceHost({
  uiIntent,
  prepare,
  reply,
  signedIn = false,
  audience = "reviewer",
  onDeepLink,
}: ActiveSurfaceHostProps) {
  const sidebar = sidebarPanels(uiIntent);

  return (
    <div className="card active-surface" data-demo="active-surface">
      {audience !== "public" && (
        <>
          <p className="cast-badge" style={{ marginBottom: "0.5rem" }}>
            Orchestrator · {uiIntent.planner_agent_id} · schema {uiIntent.version}
          </p>
          <p className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.75rem" }}>
            Active panels (skills: {uiIntent.skill_plan.join(", ") || "none"})
          </p>
        </>
      )}

      <div className="active-surface-panels">
        {sidebar.map((panel) => (
          <div key={panel.id} className="active-surface-panel console-card">
            <span className="console-panel-label">{panelLabel(panel.id)}</span>
            {renderPanel(panel, prepare, reply, signedIn, audience)}
          </div>
        ))}
      </div>

      {uiIntent.deep_links && uiIntent.deep_links.length > 0 && (
        <div className="row" style={{ flexWrap: "wrap", gap: "0.35rem", marginTop: "0.75rem" }}>
          {uiIntent.deep_links.map((d) =>
            onDeepLink ? (
              <button key={d.href} type="button" className="chip" onClick={() => onDeepLink(d.href)}>
                {d.label}
              </button>
            ) : (
              <Link key={d.href} href={d.href} className="chip">
                {d.label}
              </Link>
            )
          )}
        </div>
      )}
    </div>
  );
}

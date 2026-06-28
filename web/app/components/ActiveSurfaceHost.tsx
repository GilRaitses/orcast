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

interface ActiveSurfaceHostProps {
  uiIntent: UiIntent;
  prepare: PlanPreparePayload;
  reply?: string;
  signedIn?: boolean;
  onDeepLink?: (href: string) => void;
}

function pct(value: number | null | undefined): string {
  if (value == null) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function GatesSummaryPanel({ gates }: { gates?: GatesResponse }) {
  if (!gates) {
    return <p className="muted">No gate context for this turn.</p>;
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
}: {
  scope: "broad" | "focused";
  prepare: PlanPreparePayload;
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
        Forecast stays on the hotspot heuristic with its confidence gate. No model is promoted.
      </p>
    </div>
  );
}

function renderPanel(
  panel: UiIntentPanel,
  prepare: PlanPreparePayload,
  reply: string | undefined,
  signedIn: boolean,
) {
  const ctx = prepare.context as Record<string, unknown>;
  switch (panel.id) {
    case "gates_summary":
      return <GatesSummaryPanel gates={ctx.gates as GatesResponse | undefined} />;
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
      return <OrchestratorTrace steps={prepare.steps} reply={reply} />;
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
      return <PlacesPanel scope="broad" prepare={prepare} />;
    case "local_area":
      return <PlacesPanel scope="focused" prepare={prepare} />;
    case "kayak_plan":
      return <KayakPanel props={panel.props as KayakPanelProps | undefined} />;
    case "sidequests":
      return (
        <SidequestPanel
          props={panel.props as SidequestPanelProps | undefined}
          signedIn={signedIn}
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
  onDeepLink,
}: ActiveSurfaceHostProps) {
  const sidebar = sidebarPanels(uiIntent);

  return (
    <div className="card active-surface" data-demo="active-surface">
      <p className="cast-badge" style={{ marginBottom: "0.5rem" }}>
        Orchestrator · {uiIntent.planner_agent_id} · schema {uiIntent.version}
      </p>
      <p className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.75rem" }}>
        Active panels (skills: {uiIntent.skill_plan.join(", ") || "none"})
      </p>

      <div className="active-surface-panels">
        {sidebar.map((panel) => (
          <div key={panel.id} className="active-surface-panel console-card">
            <span className="console-panel-label">{panelLabel(panel.id)}</span>
            {renderPanel(panel, prepare, reply, signedIn)}
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

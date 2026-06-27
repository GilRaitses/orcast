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

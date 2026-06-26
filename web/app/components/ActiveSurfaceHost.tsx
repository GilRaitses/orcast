"use client";

import Link from "next/link";
import type { PlanPreparePayload } from "@/lib/uiIntent";
import { panelLabel, sidebarPanels, type UiIntent } from "@/lib/uiIntent";
import { ProvenanceGraphFromPrepare } from "@/app/components/ProvenanceGraph";

interface ActiveSurfaceHostProps {
  uiIntent: UiIntent;
  prepare: PlanPreparePayload;
  onDeepLink?: (href: string) => void;
}

function panelHref(id: string): string | null {
  switch (id) {
    case "gates_summary":
      return "/gates";
    case "decisions_table":
      return "/decisions";
    case "review_dossier":
      return "/review-dossier/latest";
    case "moderation_queue":
      return "/moderation";
    default:
      return null;
  }
}

export default function ActiveSurfaceHost({ uiIntent, prepare, onDeepLink }: ActiveSurfaceHostProps) {
  const sidebar = sidebarPanels(uiIntent);

  return (
    <div className="card active-surface" data-demo="active-surface">
      <p className="cast-badge" style={{ marginBottom: "0.5rem" }}>
        Surface planner · {uiIntent.planner_agent_id} · schema {uiIntent.version}
      </p>
      <p className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.75rem" }}>
        Active panels from keyed plan (skills: {uiIntent.skill_plan.join(", ")})
      </p>

      <div className="active-surface-panels">
        {sidebar.map((panel) => {
          const href = panelHref(panel.id);
          const emphasis = panel.props?.emphasis === "caution" ? "warn" : "pass";
          return (
            <div key={panel.id} className="active-surface-panel">
              <span className={`badge ${emphasis}`}>{panelLabel(panel.id)}</span>
              {href && (
                <Link href={href} className="chip" style={{ marginLeft: "0.5rem" }}>
                  Open →
                </Link>
              )}
              {panel.id === "explore_trace" && prepare.steps.length > 0 && (
                <details className="cast-trace" open style={{ marginTop: "0.5rem" }}>
                  <summary>Steps ({prepare.steps.length})</summary>
                  <ol>
                    {prepare.steps.map((step, j) => (
                      <li key={j}>
                        <code>{step.type}</code>
                        {step.skill ? ` · ${step.skill}` : ""}
                        {step.output_status ? ` · ${step.output_status}` : ""}
                      </li>
                    ))}
                  </ol>
                </details>
              )}
              {panel.id === "provenance_graph" && (
                <ProvenanceGraphFromPrepare prepare={prepare} />
              )}
            </div>
          );
        })}
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

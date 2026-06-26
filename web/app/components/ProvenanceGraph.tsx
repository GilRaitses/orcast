"use client";

import Link from "next/link";
import type { InteractionAnnotation, InteractionStep } from "@/lib/api";
import type { PlanPreparePayload } from "@/lib/uiIntent";

interface ProvenanceGraphProps {
  metric?: { label: string; value: string | number };
  steps: InteractionStep[];
  annotations: InteractionAnnotation[];
}

// One row per skill invocation: method node (M) with its grounding refs and status.
interface MethodNode {
  skill: string;
  output_status?: string;
  duration_ms?: number;
  grounding_refs: string[];
}

// One row per model annotation: claim node (C) with linked method, artifact, href.
interface ClaimNode {
  label: string;
  type: string;
  href?: string;
  artifact?: Record<string, unknown> | null;
  producing_skill?: string;
}

function buildMethodNodes(steps: InteractionStep[]): MethodNode[] {
  return steps
    .filter((s) => s.type === "skill_invocation" && s.skill)
    .map((s) => ({
      skill: s.skill!,
      output_status: s.output_status,
      duration_ms: s.duration_ms,
      grounding_refs: s.grounding_refs ?? [],
    }));
}

function buildClaimNodes(
  annotations: InteractionAnnotation[],
  steps: InteractionStep[],
): ClaimNode[] {
  // Map from skill name → annotation types it typically produces.
  const skillAnnotationMap: Record<string, string[]> = {
    fetch_gates: ["gate_citation"],
    fetch_provenance: ["provenance_citation"],
    fetch_decision_records: ["decision_citation"],
    fetch_review_dossier_summary: ["artifact_citation"],
    fetch_hotspots: ["deep_link"],
    fetch_supervisor_recommendation: ["artifact_citation"],
    fetch_pending_approval: ["artifact_citation"],
  };

  // Build reverse map: annotation type → first skill that produces it.
  const typeToSkill: Record<string, string> = {};
  for (const [skill, types] of Object.entries(skillAnnotationMap)) {
    const ran = steps.some((s) => s.type === "skill_invocation" && s.skill === skill);
    if (ran) {
      for (const t of types) {
        if (!typeToSkill[t]) typeToSkill[t] = skill;
      }
    }
  }

  return annotations.map((ann) => ({
    label: ann.label,
    type: ann.type,
    href: ann.href,
    artifact: ann.artifact,
    producing_skill: typeToSkill[ann.type],
  }));
}

function annotationEmphasis(type: string): string {
  if (type === "gate_citation") return "warn";
  if (type === "provenance_citation") return "pass";
  if (type === "decision_citation") return "pass";
  if (type === "artifact_citation") return "pass";
  return "";
}

function tierBadge(skill: string): string {
  const keyed = [
    "fetch_review_dossier_summary",
    "fetch_decision_records",
    "fetch_supervisor_recommendation",
    "fetch_pending_approval",
    "fetch_snapshot_manifest",
    "fetch_ingestion_status",
  ];
  const geo = ["fetch_provenance", "fetch_forecast_cell"];
  if (keyed.includes(skill)) return "T2/T3 keyed";
  if (geo.includes(skill)) return "T1 geo";
  return "T0 public";
}

export default function ProvenanceGraph({ metric, steps, annotations }: ProvenanceGraphProps) {
  const methods = buildMethodNodes(steps);
  const claims = buildClaimNodes(annotations, steps);
  const resolveStep = steps.find((s) => s.type === "resolve_agent");
  const hasData = methods.length > 0 || claims.length > 0;

  if (!hasData) return null;

  return (
    <div className="card provenance-graph" data-demo="provenance-graph" style={{ marginTop: "0.75rem" }}>
      <p className="cast-badge" style={{ marginBottom: "0.5rem" }}>
        Metric provenance graph
      </p>
      <p className="muted" style={{ fontSize: "0.82rem", marginBottom: "0.75rem" }}>
        Tools, transformations, and data origins that produced this output.{" "}
        <span className="badge fail" style={{ fontSize: "0.75rem" }}>no signal</span>
        {" "}= claim has no bound artifact (Maps grounding baseline: 85% uncited).
      </p>

      {/* Root: metric */}
      {metric && (
        <div className="pg-row pg-metric">
          <span className="pg-node-label">
            <code>{metric.label}</code>
            <span className="pg-value"> = {metric.value}</span>
          </span>
        </div>
      )}

      {/* Agent resolution */}
      {resolveStep && (
        <div className="pg-row pg-resolve" style={{ marginTop: "0.5rem" }}>
          <span className="muted" style={{ fontSize: "0.8rem" }}>
            Cast: <code>{resolveStep.managed_agent_id ?? "—"}</code>
            {" "}v{resolveStep.agent_version ?? "—"}
            {resolveStep.resolved_spec_hash && (
              <span className="pg-hash"> #{resolveStep.resolved_spec_hash.slice(0, 8)}</span>
            )}
          </span>
        </div>
      )}

      {/* Methods: skill invocations (M nodes) */}
      {methods.length > 0 && (
        <div className="pg-section" style={{ marginTop: "0.75rem" }}>
          <p className="pg-section-label muted" style={{ fontSize: "0.8rem", marginBottom: "0.35rem" }}>
            Methods (skills dispatched)
          </p>
          <div className="pg-method-list">
            {methods.map((m, i) => (
              <div key={i} className="pg-method-row">
                <code className="pg-skill">{m.skill}</code>
                <span className="badge" style={{ marginLeft: "0.4rem", fontSize: "0.72rem" }}>
                  {tierBadge(m.skill)}
                </span>
                <span
                  className={`badge ${m.output_status === "success" ? "pass" : "fail"}`}
                  style={{ marginLeft: "0.3rem", fontSize: "0.72rem" }}
                >
                  {m.output_status ?? "ran"}
                </span>
                {m.duration_ms !== undefined && (
                  <span className="muted" style={{ marginLeft: "0.4rem", fontSize: "0.72rem" }}>
                    {m.duration_ms}ms
                  </span>
                )}
                {m.grounding_refs.length > 0 && (
                  <span className="muted" style={{ marginLeft: "0.4rem", fontSize: "0.72rem" }}>
                    refs: {m.grounding_refs.join(", ")}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Claims: annotations (C nodes with experiment/artifact leaves) */}
      {claims.length > 0 && (
        <div className="pg-section" style={{ marginTop: "0.75rem" }}>
          <p className="pg-section-label muted" style={{ fontSize: "0.8rem", marginBottom: "0.35rem" }}>
            Claims (grounded annotations)
          </p>
          <div className="pg-claim-list">
            {claims.map((c, i) => {
              const hasArtifact = c.artifact && Object.keys(c.artifact).length > 0;
              const hasHref = !!c.href;
              const isBound = hasArtifact || hasHref;
              return (
                <div key={i} className="pg-claim-row">
                  <span className={`badge ${annotationEmphasis(c.type)}`} style={{ fontSize: "0.72rem" }}>
                    {c.type.replace(/_citation$/, "").replace(/_/g, " ")}
                  </span>
                  {c.producing_skill && (
                    <span className="muted" style={{ marginLeft: "0.35rem", fontSize: "0.72rem" }}>
                      via <code>{c.producing_skill}</code>
                    </span>
                  )}
                  {hasHref ? (
                    <Link href={c.href!} className="chip" style={{ marginLeft: "0.4rem", fontSize: "0.78rem" }}>
                      {c.label} →
                    </Link>
                  ) : (
                    <span style={{ marginLeft: "0.4rem", fontSize: "0.82rem" }}>{c.label}</span>
                  )}
                  {hasArtifact && (
                    <span className="muted" style={{ marginLeft: "0.35rem", fontSize: "0.72rem" }}>
                      artifact: {Object.entries(c.artifact!).map(([k, v]) => `${k}=${v}`).join(" ")}
                    </span>
                  )}
                  {!isBound && (
                    <span className="badge fail" style={{ marginLeft: "0.4rem", fontSize: "0.72rem" }}>
                      no signal
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* orcast vs Maps grounding contrast */}
      <div className="pg-contrast muted" style={{ marginTop: "0.75rem", fontSize: "0.78rem", borderTop: "1px solid var(--surface-2)", paddingTop: "0.5rem" }}>
        Maps grounding baseline (2026-06-24): 0/25 citations scientific · 85% of evidence claims uncited.
        orcast binds every claim to a skill, annotation type, and artifact reference.
      </div>
    </div>
  );
}

// Convenience wrapper used by ActiveSurfaceHost.
export function ProvenanceGraphFromPrepare({
  prepare,
  metric,
}: {
  prepare: PlanPreparePayload;
  metric?: { label: string; value: string | number };
}) {
  return (
    <ProvenanceGraph
      metric={metric}
      steps={prepare.steps}
      annotations={prepare.annotations}
    />
  );
}

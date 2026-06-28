"use client";

import type { InteractionStep } from "@/lib/api";

// Live "orchestrator-in-the-loop" sequence: resolve_agent -> plan_output ->
// skill_invocation x N -> model_output. This is both the user-facing trace and
// the WP2 audit artifact (ORCHESTRATOR_NARRATOR_FRAMEWORK.md sec 5).
type Audience = "public" | "reviewer";

const STEP_LABELS: Record<string, string> = {
  resolve_agent: "Resolve managed agent",
  plan_output: "Plan ui_intent",
  skill_invocation: "Dispatch skill",
  model_output: "Narrate reply",
};

// Public-facing trace labels. The reviewer labels carry internal vocabulary
// (managed agent, ui_intent) that the anonymous console must not expose.
const PUBLIC_STEP_LABELS: Record<string, string> = {
  resolve_agent: "Set up the guide",
  plan_output: "Plan the answer",
  skill_invocation: "Gather grounded data",
  model_output: "Write the reply",
};

function stepLabel(type: string, audience: Audience): string {
  if (audience === "public") {
    return PUBLIC_STEP_LABELS[type] ?? "Work the answer";
  }
  return STEP_LABELS[type] ?? type.replace(/_/g, " ");
}

function statusClass(status?: string): string {
  if (status === "error") return "trace-status error";
  if (status === "success" || status === "ok") return "trace-status ok";
  return "trace-status";
}

export default function OrchestratorTrace({
  steps,
  reply,
  audience = "reviewer",
}: {
  steps: InteractionStep[];
  reply?: string;
  audience?: Audience;
}) {
  const isPublic = audience === "public";
  const rendered: InteractionStep[] = [...steps];
  if (reply && !steps.some((s) => s.type === "model_output")) {
    rendered.push({ type: "model_output", output_status: "success" });
  }
  if (rendered.length === 0) {
    return <p className="muted">No steps yet. Ask a question or click the scene.</p>;
  }
  return (
    <ol className="orchestrator-trace" data-demo="orchestrator-trace">
      {rendered.map((step, i) => (
        <li key={i} className="trace-step">
          <span className="trace-index">{i + 1}</span>
          <div className="trace-body">
            <span className="trace-type">{stepLabel(step.type, audience)}</span>
            {!isPublic && step.skill && <code className="trace-skill">{step.skill}</code>}
            {!isPublic && step.managed_agent_id && (
              <span className="trace-meta">{step.managed_agent_id}</span>
            )}
            {step.output_status && (
              <span className={statusClass(step.output_status)}>{step.output_status}</span>
            )}
            {!isPublic && step.duration_ms != null && (
              <span className="trace-meta">{step.duration_ms}ms</span>
            )}
            {!isPublic && step.grounding_refs && step.grounding_refs.length > 0 && (
              <span className="trace-meta">refs: {step.grounding_refs.join(", ")}</span>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

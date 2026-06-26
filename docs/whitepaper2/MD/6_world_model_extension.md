# Section 6: Extension to world model systems

## The step-log as a world-model reasoning trace

The surface planner step-log that achieves $R_\text{uncited} = 0\%$ in Scenario 4 has the following structure:

```json
{
  "steps": [
    {"type": "resolve_agent", "managed_agent_id": "surface-planner-v1", "resolved_spec_hash": "..."},
    {"type": "skill_invocation", "skill": "fetch_gates", "output_status": "success", "grounding_refs": ["repr:level1_psth"]},
    {"type": "skill_invocation", "skill": "fetch_hotspots", "output_status": "success"},
    {"type": "plan_output", "skill_plan": ["fetch_gates", "fetch_provenance"], "panel_ids": ["gates_summary", "explore_trace"]},
    {"type": "model_output", "annotations": [{"type": "gate_citation", "href": "/gates"}]}
  ]
}
```

This is a planning trace. The agent received a query ("which gates block promotion?"), resolved an agent configuration, dispatched skills, and produced a plan. The step-log records every intermediate state: which skills ran, what their outputs were, and what the final plan consists of. When this trace is injected as RAG context, the model answers from the trace's artifact references rather than from world knowledge — hence $R_\text{uncited} = 0\%$.

This is structurally identical to what AMI Labs (Advanced Machine Intelligence) is building as world models. A JEPA-based world model [2301.08243] that perceives physical world state, predicts future states under actions, and plans action sequences produces exactly this kind of intermediate state trace: what was perceived, what was predicted, what action was planned, and what artifacts bound each step. The paper "Reasoning with Language Model is Planning with World Model" [2305.14992] explicitly frames LLM reasoning steps as world-state traces and evaluates their accuracy — the same evaluation problem $R_\text{uncited}$ formalizes for the evidence-binding dimension.

## Applying R_uncited to world model evaluation

For a world model that:
1. Perceives physical-world state from continuous sensors (cameras, LiDAR, hydrophones)
2. Predicts how the world will evolve under candidate actions
3. Plans and adapts action sequences based on predicted outcomes

The evaluation question $R_\text{uncited}$ answers is: when the world model makes a claim about the current state of the world, is that claim bound to the sensor observations that generated it?

**Concretely:** A world model that says "there are 12 pedestrians in the corridor" should have that claim bound to the camera observation that produced the count. A world model that says "turn left to avoid the high-stress zone" should have that claim bound to the stress field observation that produced the routing decision. If these claims are generated from the model's parametric knowledge rather than from bound sensor inputs, $R_\text{uncited}$ will be high even if the claims are factually correct.

The benchmark methodology is directly portable:

1. Run the world model on a physical-world query (pedestrian routing, orca encounter, manufacturing state).
2. Inject the world model's step-log (perception → prediction → plan trace) as RAG context to a language model.
3. Ask the language model a domain-specific question about the world model's domain.
4. Measure $R_\text{uncited}$.

If the world model's step-log contains complete, artifact-bound intermediate representations, $R_\text{uncited}$ will approach 0%. If the step-log is sparse or unstructured, $R_\text{uncited}$ will remain high. The metric thus provides a formal, reproducible evaluation primitive for world model evidence binding.

## Connection to AMI Labs research agenda

AMI Labs [LeCun, 2025] is building world models for physical-world reasoning focused on three pillars: understanding current physical state from sensors, predicting future states under actions, and planning action sequences. The evaluation challenge they face is exactly what $R_\text{uncited}$ addresses: how do you measure whether the world model's intermediate representations are grounded in their generating sensor evidence rather than in parametric knowledge?

The TRACE framework [2406.11460] constructs knowledge-grounded reasoning chains for RAG as "a series of logically connected knowledge triples" — a direct precedent for the step-log as a grounding mechanism. JEPA evaluation papers [2211.10831] examine whether learned representations focus on slow, stable features of the world — but do not measure whether the representations are traceable to their generating observations in the way $R_\text{uncited}$ does.

This paper provides the evaluation primitive that bridges orcast's domain-specific benchmark (marine science queries) to AMI's general world model agenda: run the 8-scenario benchmark with world model step-logs, measure $R_\text{uncited}$, and use the hierarchy to diagnose which context types bind claims.

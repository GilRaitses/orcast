# 6. Orchestrated managed agents with verified tools

The orcast Central Casting system uses a plan-then-execute architecture in which a surface planner cast role decides which panels and skills to open before any narration occurs, and a tier-verified manifest constrains which tools any cast role can invoke.

## Plan-then-execute and tier verification

When a request arrives at the keyed surface planner route, the surface-planner-v1 cast role emits a ui_intent object specifying the panels to open and a skill_plan listing which skills to run. The concierge then dispatches exactly those skills from the manifest. Skills not in the cast role's allowed list return a 400 tier_blocked response before any invocation occurs. The model narrates only after all skills complete; the model does not select tools dynamically during generation.

The ReAct architecture \cite{arxiv221003629} establishes the canonical plan-act-verify pattern: interleaving reasoning traces with deterministic action execution substantially reduces hallucination versus chain-of-thought alone, and constraining the action space to a defined tool set makes the verify step tractable. The tool selection hallucination literature confirms that LLMs produce incorrect tool choices and malformed parameters at measurable rates; internal representations can predict these failures before execution \cite{arxiv260105214}. The HaluAgent framework \cite{arxiv240611277} demonstrates that constraining tool selection to a structured, typed toolbox with a multi-stage pipeline enables reliable operation from smaller models. The APIGen pipeline \cite{arxiv240618518} establishes that tool-call verifiability is an engineering property that can be automated: pipeline-validated function calling produces datasets where the correctness of each tool call is checkable.

## Skill catalog tiers and cast roles

The skill catalog defines four tiers: T0 skills are public and usable on the public interactions route; T1 skills require a geographic viewport and run only when coordinates are present; T2 and T3 skills are keyed and blocked on the public route. Cast roles specify an explicit skill subset, model, and policy. Unknown skill IDs return 400. This manifest-based tier enforcement is the mechanism that makes skill dispatch verifiable and auditable.

Four cast roles are deployed in the pilot: explore-guide-v1 for public exploration guide narration using prepare-then-narrate; surface-planner-v1 for keyed surface planning that emits ui_intent panels; dossier-explainer-v1 for keyed dossier and gate explanation; and promotion-clerk-v1 for keyed supervisor recommendation and pending approval workflows.

## Step logs as training substrate

Every interaction step is persisted as JSONB on the exploration_turns table. This corpus of ordered step logs, resolve_agent entries, skill invocations with grounding references, and model output annotations constitutes the training substrate for future retrieval. Embedding-indexed retrieval over step logs (W-RAG, chartered in the next-phase charter) will enable step-log queries to map to related prior fits and provenance chains. The step log is not only an audit record; it is the data foundation for the system to improve its own grounding quality over time.

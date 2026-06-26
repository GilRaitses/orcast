# Section 5: The RAG lift hierarchy as a grounding architecture diagnostic

## The hierarchy

The 8-scenario results reveal a diagnostic structure in the relationship between context type and $R_\text{uncited}$:

```
Step-log (Scenario 4)     →  0%    (full grounding)
Hotspot data (Scenario 8) →  75%   (partial lift, -25pp from baseline)
Maps baseline             →  60-100% (varies by query type)
Gate context (Scenario 2) →  100%  (no lift)
```

This is not a ranking of how much data was injected — the step-log context is comparable in size to the gate context — but of how structurally aligned the injected context is with the science claims the model would otherwise generate.

## Why the hierarchy has this structure

**Full grounding (step-log):** The surface planner step-log contains the complete record of skills dispatched, panels selected, and artifacts referenced. The query "which gates block promotion" is fully answerable from the step-log without generating any science claims about orca ecology. The model answers from the step-log, not from world knowledge. Every claim in the output refers to an artifact (gate ID, skill name, panel label) that is present in the injected context. $R_\text{uncited}$ collapses to 0% because there are 0 scientific claims — not because scientific claims become cited.

**Partial grounding (hotspot data):** Hotspot probability data provides specific numerical claims that partially substitute for the model's generic science claims. But the model still generates ecology claims not covered by the hotspot data — about salmon corridors, historical behavior, acoustic monitoring — and these remain uncited. The lift corresponds exactly to the fraction of science claims that the hotspot data covers.

**No grounding (gate data):** Gate data tells the model about specific statistical tests and their outcomes. But the model's response to an orca-ecology query generates science claims about biological and ecological phenomena that gate data does not cover. The injected context is irrelevant to the science claims the model makes.

## The hierarchy as a diagnostic

The lift hierarchy tells a grounding architect which context types will reduce $R_\text{uncited}$ and by how much:

| Context type | Expected lift | Reason |
|--------------|--------------|--------|
| Complete reasoning trace / step-log | Full (→ 0%) | Transforms query to artifact-reference type |
| Structured domain data (hotspots, probabilities) | Partial (10-30pp) | Substitutes for some science claims |
| Narrow structured data (gate verdicts, provenance) | None to minimal | Doesn't cover generated science claims |
| Unstructured retrieval (place names, reviews) | None | Doesn't produce scientific citations |

This diagnostic is directly applicable to world model evaluation: run the 8-scenario benchmark on any world model's intermediate outputs and measure the hierarchy. If step-log injection yields 0% and other context types yield high uncited rates, the architecture has strong evidence binding. If no context type reduces the uncited rate, the model's claims are not architecture-traceable.

## Relation to RAG quality evaluation literature

The Ragas framework [2309.15217] measures faithfulness (whether claims are supported by retrieved context) separately from answer relevancy (whether the answer addresses the question). The hierarchy shows that these two properties are mediated by context type: step-log context achieves both simultaneously by eliminating science claims; hotspot data achieves faithfulness for the claims it covers while leaving other claims uncited. The eRAG approach [2404.13781] of evaluating each retrieved document individually against the LLM output would show the same pattern: only step-log documents are fully utilized by the model.

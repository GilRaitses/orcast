# Section 7: Limits and falsification

## Scope limits of the benchmark

**Domain specificity.** The current benchmark uses marine science queries (orca ecology, sighting check, whale watching trip planning). The science marker regex is tuned to this domain. Extension to other physical-world domains (manufacturing, clinical care, pedestrian routing) requires updating the marker set for that domain's scientific vocabulary.

**Model dependence.** The benchmark was run on gemini-3.5-flash (2026-06-24, Api-Revision 2026-05-20). Results may vary across models: a model with stronger domain-specific knowledge may generate fewer science claims (lower $|S_\text{sci}|$), while a more verbose model may generate more. Comparisons across models require fixing the query set.

**$R_\text{uncited}$ does not measure semantic accuracy.** A claim that is cited to a bound artifact but semantically wrong is not captured by $R_\text{uncited}$. The metric measures evidence binding, not factual correctness. Extension to factual accuracy requires a reference ground truth — which is the problem the Ragas and ALCE frameworks address.

**Step-log quality dependence.** Scenario 4 achieves 0% because the surface planner step-log is complete and structured. A sparse or malformed step-log would not achieve the same result. The metric measures the binding between context and claims; it does not validate the step-log's internal accuracy.

## Falsification conditions

| Claim | Falsifying condition |
|-------|---------------------|
| Step-log injection achieves $R_\text{uncited} = 0\%$ | A step-log-injected query produces scientific claims not covered by the step-log |
| The hierarchy is stable across query types | A different query set for Scenario 4 produces high $R_\text{uncited}$ |
| Gate context achieves no lift | A gate-injected query produces science claims that the gate data explicitly covers |
| $R_\text{uncited}$ diagnoses architecture quality | Two architecturally different systems produce identical $R_\text{uncited}$ hierarchies |

## Extension path

**Multi-domain validation.** Run the benchmark on pax (pedestrian routing), clinical care (Nabla domain), and manufacturing across the same RAG context types. If step-log injection consistently achieves $R_\text{uncited} \approx 0\%$ across domains, the metric is generalizable.

**Semantic accuracy addition.** Add a second metric measuring whether the claims that ARE cited are semantically accurate relative to the artifact. This requires human annotation or a reference oracle.

**World model evaluation.** Apply the benchmark to AMI-style world models: inject the world model's perception-prediction-planning trace as RAG context and measure whether the language model's claims about the physical world become evidence-bound. Negative result: if world model step-logs produce high $R_\text{uncited}$, the model's intermediate representations are not sufficiently artifact-bound.

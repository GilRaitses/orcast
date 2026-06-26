# W7 — Next-phase charter

Date: 2026-06-24
Wave set: W (Whitepaper)
Predecessor: W6 PDF build PASS (`docs/whitepaper/Build/Raitses_orcast_2026.pdf`, 560KB, 0 undefined refs)
Capstone: **H1** manual Devpost submit

## Purpose

Charter the three new wave sets and one existing wave set that the whitepaper's open gaps and extension paths motivate. These run after H1.

## Wave family IC8 (existing, chartered, planned)

Already chartered in [`docs/devpost/casting/IC8_NEXT_OBJECTIVES.md`](../devpost/casting/IC8_NEXT_OBJECTIVES.md).

**Scope:** J3 ASL promotion clerk, J4 LLM surface planner, J5 sighting-check cast role.
**Unblocked by:** IC7 deploy done; W3 prose (Section 5) identifies cast role extension as the systems growth path.
**Gate:** `ic6-gate` regression on new roles.

No registry change needed; IC8 is already in NEXT_OBJECTIVES. After W4 closes, add IC8 to registry as planned and point `next_wave_set: IC8` after H1.

## Wave family W-Eval (new)

**Purpose:** Field study testing hypothesis H1 — does displaying gates and integrity conditions increase steward trust relative to a confidence-smoothed baseline map?

**Design:**
- Comparison baseline: map with raw model confidence, no gates displayed, no integrity conditions
- Orcast condition: same map with effective confidence + integrity conditions + provenance modal
- Observer panel: structured group of shore-based observers (whale watch volunteers, researchers, stewards) in the San Juan Islands pilot region
- Primary outcome: calibrated trust measure (does perceived confidence track actual model skill?)
- Secondary outcome: provenance usability (can a user trace from map cell to kernel to data in one session?)

**Falsification:** if gate-bounded display does not improve trust calibration relative to smoothed confidence, H1 is not supported in this deployment.

**Prerequisite:** W3 prose (H1 hypothesis) complete; A5 video-complete (live demo path available for study onboarding).

**Charter file:** `docs/whitepaper/weval/W_EVAL_CHARTER.md` (to be written when W-Eval is scoped with a study coordinator).

**Registry:** add W-Eval to waves as family `WE`, type implement+verify.

## Wave family W-RAG (new)

**Purpose:** Embedding-indexed retrieval over the `interaction_steps` JSONB corpus in Postgres. Maps step-log queries to related prior fits and provenance chains. Uses E7 (uncited-evidence rate) as the acceptance metric: orcast's uncited rate must stay below the Maps baseline (85%) after retrieval augmentation.

**Design:**
- Index: dense embeddings of step-log annotation text, hybrid with BM25 over skill IDs and grounding_refs
- Retrieval: given a new interaction query, find prior step logs with similar skill invocation patterns and citation types
- Acceptance gate: `a-grounding` (`./tools/waves/run-gate.sh a-grounding`) must PASS after W-RAG ships

**Prerequisite:** Provenance graph deployed (A5); step logs accumulating in Postgres; W4 equations (E7 uncited rate formula) established as the metric.

**Dependency:** Semantic Scholar or equivalent embedding service for step-log text vectorization.

**Charter file:** `docs/whitepaper/wrag/W_RAG_CHARTER.md` (to be written when embedding infrastructure is scoped).

**Registry:** add W-RAG as family `WR`, type implement+verify.

## Wave family P1 (existing, planned)

**Purpose:** Adversarial probe surface against W3 prose claims, using the whitepaper-verified citations as the ground truth the probe must confirm or refute.

**Scope:**
- P1-A: Verify effort bias claims (Section 1) using the partial verdict table from SF-1
- P1-B: Verify gate policy claims (Section 2) against live `effective_confidence` gate behavior on prod
- P1-C: Verify provenance completeness claim (Section 5) — can a probe find a path from a displayed metric to source data without AWS console?
- P1-D: Verify grounding benchmark claim (Section 7) — re-run `maps_grounding_probe.py` and confirm 85% baseline holds at the next Gemini API revision

**Prerequisite:** W3 prose complete (claims fixed); A5 gate passing (prod accessible).

**Gate:** `p1-gate` (existing in `run-gate.sh`) plus new p1-whitepaper-doc-grep.sh that confirms P1 findings are incorporated into the whitepaper.

**Registry:** P1 already exists as family P, type probe, status planned. Activate after H1.

## Execution order (post-H1)

1. IC8 — J3/J4/J5 cast roles (unblocks richer surface planner narration)
2. P1 — adversarial probes against whitepaper claims (parallel with IC8)
3. W-Eval — field study scoping + recruitment (long lead time, start planning now)
4. W-RAG — embedding index (depends on step-log corpus size; run after 3 months of IC8 narrations)

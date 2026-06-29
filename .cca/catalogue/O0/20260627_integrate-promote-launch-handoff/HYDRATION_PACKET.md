# Hydration packet -- integrate / measure-on-served / promote rotation

Read in this order. Hydrate from files, not from any chat transcript linearly.

## 1. Governance / locks (read first)

1. `.cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md` (this lane; sections B, C, G)
2. `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (inherited forecast ML-ops locks)
3. `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B (the +0.144 bar, effort-bias)

## 2. What to act on (the ranked measured plan + patch-specs)

4. `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/SYNTHESIS_graduation.md` (sections 1-4; the sequence)
5. `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA5_shape_priors.md` (step 1 lever + patch-spec)
6. `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA2_hierarchical_nb.md` + `TA3_ais_effort.md` (step 2 baseline + patch-specs)
7. `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB4_onc_boundary_pass.md` (step 3 summer-count measurement)
8. `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB2_sst_front.md` + `TB5_salishseacast_currents.md` (step 4 conditional covariates)
9. `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/DE1_text_drift.md` + `DE2_method_drift.md` + `DE3_strategy_drift.md` (step 5 drift fixes)

## 3. Methodology / gate definition

10. `.cca/catalogue/O0/20260627_mlops/research/forward/G2_promotion_protocol.md` (the +0.144 bar + fold-stability + served gate)
11. `docs/methodology/FORECAST_KERNELS.md` (model form, effort-bias, kernels)
12. `docs/methodology/CALIBRATION_STUDIES.md` (the L0-L3 gate ladder)

## 4. Code surface to edit (single-editor, serialized)

13. `modeling/estimator.py` (TA5 smoothness penalty; TB2 aperiodic season-orthogonalized covariate support)
14. `modeling/fit_kernels.py` (TA5 + TA2 wiring; the `_maybe_write_s3` upload-disable handle)
15. `modeling/design.py`, `src/aws_backend/sources/*` (TA3 effort term; TB covariate joins)
16. `tools/waves/run-gate.sh` + `tools/waves/gates/mlops-gate.sh` (keep green at served confidence 0.0)

## 5. Machine-readable state + provenance

17. `.cca/catalogue/O0/20260627_mlops/wave_shape.yml` (`signal_modeling_graduation:` block -- status, synthesis, operator_gates)
18. `.cca/catalogue/O0/20260627_mlops/STEP_LOG.md` (the graduation TA/TB measured entry -- the full lineage)
19. `.cca/catalogue/O0/20260627_mlops/DECISION_RECORD.md` (prior adopted decisions, e.g. the bin-level timing gate)

## Repo map (orientation, do not deep-read)

- `.cca/catalogue/O0/20260627_mlops/` -- this lane's home (charters, dispatches, research/, step log).
- `research/signal_modeling/graduation/` -- the 13 lane docs + `SYNTHESIS_graduation.md` (the inputs).
- `modeling/` -- local-only fit pipeline (untracked except `studies/**` + `tide_harmonic.py`).
- `src/aws_backend/` -- ingest + sources + promotion supervisor.

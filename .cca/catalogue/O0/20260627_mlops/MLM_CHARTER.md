# MLM, covariate modeling waveset charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orcast-lane orchestrator
Home: `.cca/catalogue/O0/20260627_mlops/`
Family id: MLM (runs first; MLO is the production platform that follows)

Operationalizes the project's own methodology, `docs/methodology/FORECAST_KERNELS.md` and
`docs/methodology/CALIBRATION_STUDIES.md`, to bring the aggregated open-source weather and
wildlife covariates into the forecast through the leveled, gated study plan. It does not
invent a new model; it executes the existing LNP kernel design with honest go/no-go gates.

## Model (from FORECAST_KERNELS.md)

```
log lambda(x,t) = b0 + s_space(x) + k_tide + k_diel + k_lunar + k_season + k_salmon + log E(x,t)
```

Today only `k_diel` and `k_lunar` are fitted (NB2 GLM, `modeling/fit_kernels.py`). Effective
confidence is 0% (negative held-out CV skill, time-rescaling fails). This waveset adds the
remaining covariates level by level and only raises confidence when a gate passes.

## Locked honesty constraints

- Effort-bias design: temporal kernels are estimated from continuous acoustic detections
  (effort-stable), with an explicit `log E` offset. Visual sightings (OBIS, iNaturalist,
  community, the CAND set) are validation and `s_space` only, never the temporal-kernel heat.
- Never render sharper than the gates support. `effective_confidence` reflects held-out
  skill and is only promoted by a recorded human decision via the supervisor.
- Acoustic presence is not visual encounter. Keep them as honest layers; the acoustic-to-
  visible bridge stays an open decision.
- Coverage honesty: a level whose data coverage is insufficient (for example tide/season
  before full annual + lunar acoustic coverage) reports `withheld` with the reason, not a
  fabricated kernel.

## Literature-grounded covariate priority

Per FORECAST_KERNELS.md section 5 and the cited ecology (Olson et al. 2018, Salish Sea SRKW
sightings; Thornton et al. 2022 CSAS, SRKW summer distribution and habitat use):

- `k_salmon` (Chinook prey run timing): the strongest non-tidal driver, well supported.
- `k_tide` (flood/ebb foraging fronts at Haro Strait).
- `s_space` (bathymetry / channel habitat).
- `k_season` next; `k_diel` and `k_lunar` already fitted.
- NDBC weather (wind, waves, water temp) and AIS enter as detector-QC / effort terms at
  Level 0, not as animal kernels.

## Leveled waves (each a go/no-go on held-out data)

| Wave | Level | Study | Gate |
|------|-------|-------|------|
| M-L0 | 0 instrument | OrcaHello detector ROC/d' vs confirmed labels + per-station effort series | per-station effort known; detector ROC AUC with CI |
| M-L1 | 1 single-covariate | PSTH for `k_diel`, then `k_tide`, with phase-shuffle null | PSTH beats shuffled null (permutation p + effect size); shape consistent across stations |
| M-L2 | 2 joint temporal | joint LNP (tide + diel + lunar + season); lift coverage exclusion when clear | held-out Poisson log-likelihood beats climatology and best single-covariate; CV-stable; joint vs PSTH agree |
| M-L3 | 3 prey + space | add `k_salmon` (run-timing index + lag scan) and `s_space` (bathymetry + effort-corrected CAND sighting density) | held-out skill beats recent-detection-density baseline; calibration (reliability + PIT) within tolerance |

Each wave writes a study report under `modeling/studies/reports/` and, when it changes the
served fit, updates `data/models/fit_report.json` carrying `fit_plan_id`,
`dataset_snapshot_id`, and repr+run ids. No `effective_confidence` promotion without a
passing gate.

## Scaffolding (this charter delivers)

- `modeling/studies/common.py` data loaders + a `GateResult` contract + report writer.
- `modeling/studies/level0_detector.py`, `level1_psth.py`, `level2_joint.py`,
  `level3_prey_space.py`, each runnable and honest (degrade to `insufficient_data` rather
  than crash). They reuse the cached OrcaHello index from the CAND waveset
  (`.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json`) when the live
  API is rate-limited.
- `modeling/studies/run_studies.py` driver that runs L0..L3 and prints the gate ladder.

## Out of scope

- Promoting confidence without a passing gate + recorded human decision.
- Claiming acoustic equals visual encounter.
- The production platform (feature store, registry, scheduled retrain, monitoring): that is
  the MLO waveset (`MLO_CHARTER.md`).

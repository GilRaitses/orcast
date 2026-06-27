# Hydration packet, forecast ML-ops lane orchestrator

Ordered read list for the incoming thread. Read in order; do not read the chat transcript
linearly. Paths are repo-relative to `/Users/gilraitses/orcast` unless noted.

## 1. Governance / canon (read first)

- `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` (this rotation's authority doc)
- `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` (operator intent, PIML strategy,
  architecture critique, recommended literature)
- `.cca/STANDING_DECISIONS_REGISTER.md` (settled decisions, esp. SD-024 surgical commits, SD-006
  voice, SD-A10 honesty-model-limits-are-features)

## 2. Methodology (the modeling canon)

- `docs/methodology/FORECAST_KERNELS.md` (kernel model + effort-bias principle)
- `docs/methodology/CALIBRATION_STUDIES.md` (LNP/PSTH/GLM, the leveled gate plan)

## 3. This lane's charters + trace

- `.cca/catalogue/O0/20260627_mlops/MLM_CHARTER.md`, `MLO_CHARTER.md`, `wave_shape.yml`, `STEP_LOG.md`
  (the MLM/MLO charters and the running step log, including the L2 multi-station result)
- `.cca/catalogue/O0/20260627_wildlife-sources/WILDLIFE_SOURCES_REGISTER.md` (ranked sources to
  aggregate; the P0 order: multi-station acoustic, real Chinook index, held-out visual validation)
- `.cca/catalogue/O0/20260627_forecast-candidates/` (CAND set + the cached OrcaHello indexes)

## 4. Evidence / artifacts (latest verdicts)

- `modeling/studies/reports/level0_detector.json` (PASS, ROC AUC 0.879)
- `modeling/studies/reports/level1_psth_diel.json` (PASS)
- `modeling/studies/reports/level2_joint_temporal.json` (FAIL, single-station, tide fitted)
- `modeling/studies/reports/level2_multistation.json` (FAIL but skill +0.078; the frontier evidence)
- `modeling/studies/reports/level2_tide_coverage.json`, `level3_prey_space.json`, `salmon_lag.json`
- `data/models/fit_report.json` (local-only; the last S3 refit, tide fitted, confidence 0)

## 5. Code (the modeling + serving surface)

- `modeling/fit_kernels.py` (local), `design.py`, `estimator.py`, `bases.py`, `tide_phase.py`
  (contains `HarmonicTidalPhase`), `tide_harmonic.py` (tracked), `validation/`
- `modeling/studies/` (tracked: `common.py`, `level0..3`, `run_studies.py`, plus the heavy
  `level2_multistation.py` and `tide_coverage.py`)
- `src/aws_backend/ingest_timeseries.py` (`ingest_acoustic_history`, `ingest_acoustic_reviewed_outcomes`,
  `ingest_noaa_history`, `ingest_salmon`), `timeseries.py` (S3 + memory stores)
- `src/aws_backend/sources/` (`orcahello_history.py`, `salmon.py`, `noaa.py`, ...)
- `src/aws_backend/kernel_model/serve.py`, `routers/kernel.py`, `promotion/supervisor.py`,
  `routers/promotion.py`

## 6. Gates / registry / environments

- `tools/waves/run-gate.sh mlops-gate` (local; stdlib ladder + honesty guard)
- `docs/devpost/WAVES_REGISTRY.md` + `docs/devpost/waves.registry.yaml` (families MLM, MLO, WILDLIFE)
- Heavy fit/studies: `.venv-modeling/bin/python` (numpy/pandas/scipy/boto3). Stdlib ladder: system
  `python3`. AWS store: bucket + region in HANDOFF_CHARTER section B.4.

## 7. Repo map (orientation)

- `modeling/` offline fit + studies (pipeline local-only; studies + reports tracked).
  `src/aws_backend/` FastAPI backend, sources, ingest, serving, promotion. `docs/methodology/`
  modeling canon. `.cca/catalogue/O0/` waveset homes (this lane: `20260627_mlops/`; handoff:
  `20260627_mlops-handoff/`; sources: `20260627_wildlife-sources/`). `tools/` harnesses + gates.

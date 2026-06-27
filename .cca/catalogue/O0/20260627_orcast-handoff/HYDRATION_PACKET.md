# Hydration packet, orcast-lane orchestrator

Ordered read list for the incoming thread. Read in order; do not read the chat transcript
linearly. Paths are repo-relative to `/Users/gilraitses/orcast` unless noted.

## 1. Governance / canon (read first)

- `.cca/catalogue/O0/20260627_orcast-handoff/HANDOFF_CHARTER.md` (this rotation's authority doc)
- `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` (intent, PIML strategy, critique, literature)
- `.cca/STANDING_DECISIONS_REGISTER.md` (settled decisions of record)

## 2. Methodology (the modeling canon)

- `docs/methodology/FORECAST_KERNELS.md` (the kernel model + effort-bias principle)
- `docs/methodology/CALIBRATION_STUDIES.md` (LNP/PSTH/GLM, leveled gate plan)

## 3. This session's wavesets (charters + traces)

- `.cca/catalogue/O0/20260627_forecast-candidates/` (CAND: charter, wave_shape, candidate_targets.schema, candidates.targets.json, CAND_VERIFY, GAP_COVERAGE, STEP_LOG)
- `.cca/catalogue/O0/20260627_mlops/` (MLM + MLO charters, wave_shape, STEP_LOG)
- `.cca/catalogue/O0/20260627_bside-build/` (BSIDE charter, wave_shape, STEP_LOG)
- `.cca/catalogue/O0/20260627_demo-waveset/` (DEMO: W-STORY, charter, wave_shape, STEP_LOG)

## 4. Code (the modeling + API surface)

- `modeling/fit_kernels.py`, `modeling/design.py`, `modeling/estimator.py`, `modeling/bases.py`
- `modeling/studies/` (L0-L3 study ladder + `run_studies.py`)
- `src/aws_backend/kernel_model/serve.py`, `src/aws_backend/routers/kernel.py` (gates/provenance)
- `src/aws_backend/promotion/supervisor.py`, `src/aws_backend/routers/promotion.py`
- `src/aws_backend/routers/dtag.py` (whale-tagger B-API)
- `src/aws_backend/sources/` (obis, inaturalist, orcahello, orcahello_history, noaa, salmon, bathymetry, ndbc, ais), `src/aws_backend/covariates.py`, `src/aws_backend/geo_region.py`
- `tools/forecast_candidates/build_candidates.py`
- `web/app/components/AdaptiveExplore.tsx`, `ActiveSurfaceHost.tsx`, `console/OrchestratorTrace.tsx`, `ExploreGuidePanel.tsx`, `ProvenanceModal.tsx`

## 5. Evidence / artifacts

- `data/models/fit_report.json`, `fitted_kernels.json`, `promotion.json`, `fit_plan.json`, `snapshot_manifest.json`
- `modeling/studies/reports/level{0,1,2,3}_*.json` (latest gate verdicts)
- `.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json` (cached acoustic index)

## 6. Gates / registry / environments

- `docs/devpost/WAVES_REGISTRY.md` + `docs/devpost/waves.registry.yaml`
- `tools/waves/run-gate.sh` (gates: `mlops-gate`, `H0`, `I-suite`, ...)
- Local venv: `.venv` (python3.14, backend deps incl. python-multipart). `modeling/studies/` is stdlib (system `python3`).
- Deployed web: `https://orcast-h0.vercel.app`. Backend self-hosted at `orcast-api.aimez.ai` (co-tenant), App Runner rollback.

## 7. Repo map (orientation)

- `modeling/` offline fit + studies. `src/aws_backend/` FastAPI backend. `web/` Next.js console.
  `docs/methodology/` modeling canon. `docs/devpost/` registry + submission. `.cca/catalogue/O0/`
  waveset homes. `tools/` harnesses + gates.

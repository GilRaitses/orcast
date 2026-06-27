# MLO, production MLOps platform charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orcast-lane orchestrator
Home: `.cca/catalogue/O0/20260627_mlops/`
Family id: MLO (runs after MLM)

Builds the production MLOps platform around the MLM modeling waveset so the gated kernel fit
can be reproduced, scheduled, monitored, and served with honest confidence. Reuses the
reproducibility scaffolding already present in `data/models/` (`fit_plan`, snapshot manifest,
repr/run ids) and the promotion supervisor.

## Locked honesty constraints

- Same as MLM: no silent confidence inflation. Monitoring and retraining never promote a fit;
  promotion stays a recorded human decision through `src/aws_backend/promotion/supervisor.py`.
- Drift alerts surface honestly; a degraded covariate feed lowers coverage and can only widen
  uncertainty, never narrow it.

## Waves

| Wave | Scope | Exit bar |
|------|-------|----------|
| MLO-FEAT | versioned covariate/feature store: formalize the covariate library (NOAA tide/currents, salmon index, bathymetry, ephemeris) + Great Expectations freshness/coverage checks (extend `scripts/.../great_expectations_setup.py`) | feature snapshot is content-addressed; GE suite passes or reports coverage |
| MLO-REG | model registry + reproducibility: formalize `fit_plan_id`, `dataset_snapshot_id`, `snapshot_manifest.json`, `frozen_data` into a queryable registry | every served fit traces to a snapshot + plan + repr/run |
| MLO-SCHED | scheduled gated retrain: EventBridge -> Step Functions `FreezeSnapshot -> fit -> gate battery -> promotion supervisor -> register`, reusing `POST /api/orchestrator/run` | a scheduled run produces a fit_report and a supervisor recommendation without auto-promoting |
| MLO-MON | drift/monitoring: covariate coverage, detector ROC, calibration/PIT, data freshness | dashboards/alerts emit; no metric silently inflates confidence |
| MLO-CI | `mlops-gate` in `tools/waves/run-gate.sh` running the MLM study gates + `I-suite` | `./tools/waves/run-gate.sh mlops-gate` returns zero |

MLO-CI and the registry/feature-store contracts are deliverable now; the AWS scheduling and
monitoring infra (EventBridge, Step Functions, dashboards) are operator/deploy-gated.

## Integration points (existing)

- Fit + gates: `modeling/fit_kernels.py`, `data/models/{fit_report,fitted_kernels,promotion,fit_plan}.json`.
- Serving: `src/aws_backend/kernel_model/serve.py`; `GET /api/gates`, `GET /api/provenance`.
- Promotion: `src/aws_backend/routers/promotion.py` (`/api/orchestrator/run`, `/api/promotion/apply`), `promotion/supervisor.py`.
- Snapshots: `data/models/snapshot_manifest.json`, `frozen_data`.

## Out of scope

- Auto-promotion. pax surfaces. Any confidence change without a passing gate.

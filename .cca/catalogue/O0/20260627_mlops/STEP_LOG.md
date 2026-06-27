# STEP_LOG, MLOps wavesets (MLM + MLO)

All times America/New_York.

## 2026-06-27

- Chartered MLM (covariate modeling) and MLO (production platform) from
  `docs/methodology/FORECAST_KERNELS.md` and `CALIBRATION_STUDIES.md`, grounded in the cited
  ecology (Olson 2018; Thornton 2022; Chinook-tracking).
- Wrote `MLM_CHARTER.md`, `MLO_CHARTER.md`, `wave_shape.yml`.
- Scaffolding to follow: `modeling/studies/` (L0..L3 study scripts + gates), MLO-CI gate.

## 2026-06-27 (scaffolding executed)

- Built `modeling/studies/` (pure stdlib): `common.py`, `level0_detector.py`,
  `level1_psth.py`, `level2_joint.py`, `level3_prey_space.py`, `run_studies.py`. Reuses the
  cached OrcaHello index and the CAND set so it runs without the flaky live API.
- Ran the ladder (honest verdicts):
  - L0 detector: withheld (per-station effort + precision computed; ROC AUC needs scored feed).
  - L1 PSTH diel: PASS (modulation 1.79 beats the phase-shuffle null, p=0.0005, on 1359 cached detections).
  - L2 joint temporal: FAIL (held-out skill -0.018, time-rescaling KS fails, tide/season withheld by phase coverage). Confidence stays 0%.
  - L3 prey+space: withheld (s_space density precursor assembled from CAND; prey series + effort model + visual validation pending).
- MLO: delivered `tools/waves/gates/mlops-gate.sh` + wired `mlops-gate` into `run-gate.sh`.
  The gate runs the ladder and enforces the honesty guard (served confidence must not exceed
  what the gates earned). `./tools/waves/run-gate.sh mlops-gate` returns zero.
- MLO feature store / registry / scheduled retrain / monitoring remain chartered; the AWS
  infra (EventBridge, Step Functions, dashboards) is operator/deploy-gated.

## Open / awaiting operator

- M-L2 tide/season and M-L3 may stay `withheld` until acoustic history reaches full annual +
  lunar coverage; gates report this honestly.
- MLO scheduling/monitoring AWS infra is operator/deploy-gated.
- Commit/push only on explicit request.

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

## 2026-06-27 (MLM frontier parallel waves)

Dispatched three self-contained parallel subagent waves (orchestrator owns verification;
subagents wrote only their named surfaces, no commits).

- M-L0 (detector ROC/d', NOTES 6.2): re-pulled the OrcaHello reviewed outcomes live (403/SSL
  flake, succeeded with retries) into `orcahello_index.confidence.cache.json` (977 records;
  758 paired confidence+label: 423 confirmed, 335 false_positive). Extended
  `level0_detector.py` with a stdlib rank AUC (tie-averaged), 1000-sample bootstrap CI, and a
  log-linear-corrected d'. Verdict: **L0 PASS** — ROC AUC 0.879 (95% CI 0.856-0.902), d' 1.62.
  Detector is now characterized; effort portion was already satisfied.
- M-TIDE (PIML tide harmonic, NOTES 3.1/6.1): added `modeling/tide_harmonic.py` (M2/S2/N2/K1/O1
  least-squares model) and `modeling/studies/tide_coverage.py`. Fit to real NOAA harmonic
  current predictions (PUG1701/1702/1703, 50,112 samples), reconstruction R^2 0.970. Tide phase
  coverage over the acoustic timestamps rises to **1.000** vs the 0.42 baseline that excluded
  k_tide. The coverage exclusion that fails L2 is now liftable. The actual joint refit did NOT
  run: the AWS data store probe returned NoSuchBucket, so `data/models/fit_report.json` is
  unchanged and the L2 joint verdict stays **FAIL / confidence 0%** (honest). Joint refit with
  k_tide is pending AWS data access.
- M-L3 (salmon lag + s_space, NOTES 6.4): added `modeling/studies/salmon_lag.py` (daily presence
  vs run-timing lag scan over +/-30 d, circular-shift permutation null) and wired its summary
  into `level3_prey_space.py`. Source was the documented climatology fallback (live Albion/DART
  not reached), so the lag (best -30 d, r -0.10, p 0.33) is informational and **L3 stays
  WITHHELD** — cannot earn k_salmon credit on a placeholder feed.

Ladder after the waves: L0 PASS, L1 PASS (diel), L2 FAIL (frontier), L3 WITHHELD.
`./tools/waves/run-gate.sh mlops-gate` returns zero; honesty guard holds (served confidence 0.0
consistent with L2 fail). Effective confidence unchanged at 0%.

## Open / awaiting operator

- M-L2 off 0%: run the joint refit with the harmonic k_tide against the AWS timeseries store
  (NoSuchBucket locally this session); season still needs fuller annual coverage.
- M-L3 needs a real Chinook run-timing feed (Albion/DART) to replace the climatology placeholder.
- MLO scheduling/monitoring AWS infra is operator/deploy-gated.
- A confidence promotion still requires a passing gate + a recorded supervisor decision.

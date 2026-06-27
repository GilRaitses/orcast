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

## 2026-06-27 (L2 follow-up: harmonic k_tide refit, operator-approved)

- Resolved the AWS store access: the timeseries data is in bucket
  `198456344617-us-west-2-orcast-aws-backend-raw-payloads` (region us-west-2), not the config
  default `orcast-raw-payloads` (that mismatch was the M-TIDE NoSuchBucket). acoustic_detections
  has haro_strait; env_currents has pug1701/1702/1703.
- Integrated the harmonic tide into the fit pipeline (local-only modeling tree, like the rest of
  it): added `HarmonicTidalPhase` to `modeling/tide_phase.py` (drop-in for the TidalPhase
  interface, backed by `modeling/tide_harmonic.HarmonicTide`), and `modeling/fit_kernels.py` now
  prefers the harmonic phase when currents exist (reconstruction R^2 > 0.5), falling back to the
  onset-interpolation TidalPhase otherwise. Recorded `tide_model` + `tide_reconstruction_r2`.
- Refit against the real S3 store (production model-artifact upload disabled: a confidence change
  is a recorded supervisor decision, not a refit side effect). Result, honest:
  - `k_tide` NOW ENTERS the joint fit: covariates_fit = [diel, tide, lunar]; tide phase coverage
    0.42 -> 1.00 (harmonic R^2 0.847 on the pooled pug170x current series; 18,480 current records).
  - L2 still FAILS: held-out CV mean deviance skill -0.047 (slightly worse than the -0.018 without
    tide), time-rescaling KS still fails, confidence stays 0.0. Adding k_tide did not earn skill.
    Season still excluded (0.75 coverage).
  - Takeaway matches NOTES section 4: the single-station sparse-count regime, not the covariate
    list, is the binding constraint. The harmonic model removed the coverage blocker so k_tide is
    now a fair test; the data on one station does not support positive skill.
- Updated `modeling/studies/reports/level2_joint_temporal.json` (now shows tide fitted, season
  withheld) and fixed `level2_joint.py` to name the actual excluded covariate(s) rather than the
  stale "tide/season" string. mlops-gate stays green; honesty guard holds (served confidence 0.0).

## 2026-06-27 (multi-station experiment, WILDLIFE recommendation #1)

- Acted on the WILDLIFE register's top recommendation (fit OrcaHello on all in-region Orcasound
  nodes). The production acoustic_detections stream has only haro_strait (761); the cached
  OrcaHello index carries three more in-region nodes (orcasound_lab 1029, andrews_bay 265,
  north_san_juan_channel 34). Built `modeling/studies/level2_multistation.py`: combine the
  production haro_strait stream with the cached nodes into a local memory store (no production
  store write), add the S3 harmonic-tide currents + uptime, and run the standard joint fit.
- Result (EXPERIMENT, not promoted): 4 stations, 2089 detections. All four temporal kernels now
  fit (diel/tide/lunar/season, phase coverage 1.0 each). Held-out CV mean deviance skill flips
  POSITIVE: +0.078 (4/5 folds) vs the single-station baseline -0.047. This is the first time the
  model beats climatology out of sample, and it confirms the binding constraint was the
  single-station regime, not the covariate list.
- Still FAIL / confidence stays 0% (honest): time-rescaling pooled KS still fails (p=0.0), and the
  L1 cross-station consistency is now testable (4 stations) but NOT yet consistent (per-kernel PSTH
  correlations 0.14-0.34, below the 0.5 bar). The experiment's internal gate score would be 0.5,
  but it is explicitly unpromoted (write_outputs disabled, mixed-provenance spike train, no
  supervisor decision). `modeling/studies/reports/level2_multistation.json` records this.
- This study imports the heavy fit pipeline, so it runs under .venv-modeling and is NOT added to
  run_studies / mlops-gate (which stay pure stdlib). mlops-gate remains green; served confidence 0.0.

## Open / awaiting operator

- M-L2 to a real pass: ingest the additional Orcasound nodes into the production acoustic_detections
  stream (the experiment used the cached index), tighten per-station effort/log E so time-rescaling
  passes, and lift cross-station kernel consistency. Multi-station already flips held-out skill
  positive, so this is the path off 0% (a passing gate + a recorded supervisor decision would then
  promote confidence; not done here).
- M-L3 needs a real Chinook run-timing feed: validate the Albion/DART parsers in
  `src/aws_backend/sources/salmon.py` (both wired, both fall through to climatology today).
- The harmonic integration lives in the local modeling pipeline (untracked, like fit_kernels.py
  and design.py); only `tide_harmonic.py` and the study reports are tracked. Reproduce with
  `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2 PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels`.
- MLO scheduling/monitoring AWS infra is operator/deploy-gated.
- A confidence promotion still requires a passing gate + a recorded supervisor decision.

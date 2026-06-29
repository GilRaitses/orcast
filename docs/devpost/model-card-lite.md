# ORCAST Kernel Forecast Model Card Lite

## Model Details

- Model name: ORCAST kernel forecast
- Family: negative-binomial log-linear encounter-intensity model
- Current operational scope: temporal acoustic encounter intensity for the San Juan Islands pilot region
- Primary artifacts: `fitted_kernels.json`, `fit_report.json`, `fit_plan.json`, `snapshot_manifest.json`, `runs/{run_id}/manifest.json`

## Intended Use

The model supports public-facing confidence and provenance for orca encounter forecasts. It is designed for transparency, review, and field-planning context, not for operational navigation or safety-critical decisions.

## Current Evidence State

The current real-data fit is partial:

- Single acoustic station.
- OrcaHello/Orcasound detections are unreviewed candidates.
- Diel and lunar covariates are fitted.
- Tide is excluded from the joint fit when current records do not overlap acoustic detections.
- Season is excluded when annual phase coverage is incomplete.
- Level 0 detector characterization is recorded as planned, not complete.

## Metrics And Gates

Confidence comes from the gate policy in `modeling/fit_kernels.py`:

- Level 1 PSTH nulls.
- Time-blocked cross-validation vs climatology.
- Held-out PIT calibration.
- Time-rescaling goodness-of-fit, currently labeled in-sample unless upgraded.
- PSTH-vs-kernel consistency as a diagnostic, not a confidence gate.

Non-positive mean CV skill does not earn CV confidence.

## Caveats

Every confidence-bearing surface should include server-derived caveats from `/api/gates`, including detector status, station count, effort assumptions, excluded covariates, time-rescaling failures, and marginal or negative CV skill.

## Promotion Policy

Automated gates determine eligibility and raw confidence. Human promotion is a separate signed-off display authority step. WorkOS reviewer identity is server-stamped on decision records through the Vercel proxy.

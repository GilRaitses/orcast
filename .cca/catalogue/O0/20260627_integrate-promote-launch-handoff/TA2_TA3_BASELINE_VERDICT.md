# TA2 + TA3 clean-baseline verdict (step 2)

Orchestrator O0 (integrate / measure-on-served / promote). Date: 2026-06-27. Repo `main` at `9a00e15`.
Measured decision aid; nothing promotes. Served upload disabled (`_maybe_write_s3` no-op),
`write_outputs=False`. Default served fit byte-identical (all enablers OFF). `mlops-gate` green at
served confidence 0.0.

## What was integrated (serialized after step 1, single convergence-file editor)

TA2 (`TA2_hierarchical_nb.md` §4) -- opt-in, default OFF (`run_fit(baseline_enablers=True)` /
`ORCAST_BASELINE_ENABLERS=1`):
- `modeling/estimator.py`: `fit_glm(use_station_effects="partial_pool", pooling_tau=...)` -- a
  partial-pooling random station intercept as the MAP ridge `1/(tau^2 * nobs)` on all-station
  deviation dummies (global intercept unpenalized; the `nobs` factor gives `tau` its group-SD meaning
  under statsmodels' nobs-normalized `fit_regularized`). Plus `ridge_lambda` (flat nested-CV ridge on
  the Fourier coefs). FE remains the default (byte-identical).
- `modeling/fit_kernels.py`: nested-`block_cv` selection of `(tau, ridge)` (per outer fold for CV/PIT,
  single nested selection on the full data for the served coefficients); the cloglog presence
  COMPANION head (`report["presence_reframe"]`), kept strictly distinct from the NO-GO ZI/hurdle count
  upgrade; honest `baseline_enablers` report block with the FE contrast.

TA3 (`TA3_ais_effort.md` §8) -- AIS detectability folded into the `log E` offset (effort term, B.2; 0
added presence params):
- new `modeling/ais_noise.py`: `detectability_factor` / `log_detectability` -- `D = exp(-kappa*I_norm)`
  clipped to `[1e-2, 1]`; `kappa==0` / missing index / unknown station -> `D=1` (EXACT no-op); never
  fabricates AIS.
- `modeling/design.py` `build_design(noise_by_station=, ais_kappa=)`: multiplies the per-bin exposure
  by `D_ais` when active.
- `modeling/fit_kernels.py` `_station_intensity_fn`: adds `log D_ais` on the SAME integration grid
  (so the time-rescaling compensator does not accumulate hazard during heavy masking).
- defaults are a strict no-op; verified: with a synthetic index `D=exp(-1)=0.368` and exposure
  changes, with `kappa=0`/`None` the exposure is byte-identical.

## Measured served verdict (4-station served store, held-out 5-fold block_cv, NB2)

| Variant | mean skill | per-fold | folds>0 | worst fold | PIT (KS p) | confidence |
|---|---|---|---|---|---|---|
| FE baseline (OFF) | +0.0778 | -0.038, 0.065, 0.140, 0.066, 0.156 | 4/5 | **-0.038** | 0.364 | 0.49 |
| **TA2 enablers (ON)** | **+0.1547** | 0.046, 0.193, 0.242, 0.198, 0.093 | **5/5** | **+0.046** | 0.614 | 0.61 |

Nested selection: full-data `(tau=1.0, ridge=0.01)`; per-fold tau `[2,1,1,0.25,1]`, ridge `0.01` every
fold (stable). The partial pool's structural win is on the held-out/sparse station: an absent station's
all-zero dummy predicts at the population mean (`const`), removing the fixed-effect reference-coding
worst-fold swing (`-0.038 -> +0.046`, all folds now positive). The mild ridge raises the mean
(+0.078 -> +0.155, variance reduction) and improves calibration (PIT p 0.364 -> 0.614).

### Cloglog presence companion (TA2 PATCH-3, report-only)

| metric | value |
|---|---|
| folds log-loss beats per-effort climatology | 1/5 |
| log-loss skill vs climatology | -0.127 |
| Brier skill vs climatology | -0.001 |

Honest: the bin-level presence indicator carries NO skill over a per-effort presence climatology. The
companion is a diagnostic reported alongside the count gates; it does not feed the served intensity or
confidence, and it is NOT the NO-GO ZI/hurdle count upgrade.

### TA3 AIS effort -- NOT-MEASURED (data infeasible, wire landed as no-op)

The real Marine Cadastre AIS fetch + ingest is a separate operator-/deploy-gated step (TA3 §2) and was
NOT performed. The wire is landed and inert by default; `report["ais_effort"].active = false`,
`coverage = null`, `log E` remains flat under the current disjoint/constant `station_uptime`. The
detectability delta on served CV-skill is therefore NOT-MEASURED. When the operator ingests a
`us_side_partial` index and sets `ais_kappa > 0`, the same harness measures it (a clean baseline is
then judged against, not a covariate hunt).

## Honest reading

- The clean baseline (TA2 enablers) is itself fold-stable (5/5), calibrated (PIT p 0.61), and crosses
  0.6 confidence on the served store. Per charter B.4/step-2 TA2/TA3 are framed as ENABLERS, not the
  promoted lever (step 1's TA5 is), so this thread does NOT promote them. But the operator should note
  that the served 4-station fit clears the bar via variance reduction under EITHER regularizer (TA5
  smoothness +0.169 / conf 0.63, or TA2 partial-pool+ridge +0.155 / conf 0.61). They are not additive
  evidence -- both are regularizers on the same overfit-prone 4-station fit; do not double-count.
- Recommended posture: promote ONE regularized configuration on a recorded B.1 decision (TA5 is the
  graduated lever and slightly stronger; the TA2 baseline is the fold-stability/held-out-station
  enabler). They compose (`fit_glm` accepts both penalties), and the composition can be measured before
  any promotion if the operator wants the combined fit.

## Rails confirmed

No promotion, deploy, ingest, AIS fetch, store write, S3 write, or commit. Default served fit
byte-identical (all enablers OFF). `mlops-gate` green at served confidence 0.0. `data/models/fit_report.json`
untouched.

# INTEGRATE GROUNDING (propose-only) for the served forecast path

Sub-orchestrator: MLOps integrate-grounding waveset. Date: 2026-06-28 (America/New_York).
Repo: `/Users/gilraitses/orcast`, `main` near `9a00e15`. Answers to the O0 central orchestrator.

This doc grounds the graduation verdicts (TA/TB/DE lanes) into a single ranked, PROPOSE-ONLY integrate
plan for the served forecast path. It PROPOSES nothing more than this doc. No model code is changed, no
fit is run, no store/S3 write, no deploy, no commit, no `git add`. Effective confidence stays 0.0.

## 0. Rails and reading rules

- Effective confidence stays 0.0. Nothing here promotes. Served confidence only rises on a passing gate
  on SERVED data plus a recorded human supervisor decision (B.1), neither of which this pass performs.
- Every skill number below is held-out 5-fold `block_cv` mean-deviance-skill. Numbers tagged SERVED are
  the live `acoustic_detections` 4-station store (the W6 ingest landed: 4 stations / 2089 detections /
  66,899 bins). Numbers tagged EXPERIMENT are the mixed-provenance experiment store. Anything else is
  marked NOT-MEASURED. Judge by held-out fold-stable CV-skill, never in-sample fit. Withhold over fake.
- The model: `log lambda = b0 + s_space + k_tide + k_diel + k_lunar + k_season + k_salmon + log E`.
  Current ladder: L0 PASS, L1 PASS, L2 FAIL, L3 WITHHELD. The promotion bar (G2): served CV-skill
  `>= +0.144` AND `>= 4/5` folds positive AND across-fold lower bound `mean - t*SE >= +0.078` AND PIT
  calibrated AND a beaten L1 null, mapping to confidence `>= 0.6`.
- Wire state note: the integrate-promote-launch-handoff thread already LANDED the TA5, TA2, TA3, and the
  TB2/TB5 aperiodic estimator surfaces into the convergence files as default-OFF, byte-identical no-ops,
  and MEASURED several of them on the served store (the verdict docs cited below). For O0's purposes the
  remaining "integrate" for the measured levers is the single-editor default flip plus the recorded
  promotion decision, not new code authorship. This doc does not touch those files.

## 1. Ranked grounding ledger (cheapest high-value first)

| Rank | Candidate | Verdict | MEASURED held-out CV-skill | Served file + seam it touches | Dependency / order |
|---|---|---|---|---|---|
| 1 | TA5 smoothness (roughness) shape prior | GO (strongest, served-measured) | SERVED 4-stn ON `+0.1686` (5/5, across-fold LB `+0.109`, PIT KS p `0.090`, conf 0.63); OFF baseline `+0.0778` (4/5, conf 0.49). Clears all 5 G2 bands on served. Served single-station only `+0.0037` (does not clear). EXPERIMENT store `+0.1767`. | `modeling/estimator.py` `fit_glm` (ridge penalty `lambda*h^(2*order)` on Fourier coefs; `const`/`st__*` unpenalized; `fit_regularized(L1_wt=0)`) + `modeling/fit_kernels.py` `run_fit` (nested `block_cv` lambda, `n_harmonics=1` control, `smoothness_regularized` serving disclosure). Landed OFF/byte-identical. | FIRST. Standalone. |
| 2 | TA2 partial-pool + nested-CV ridge (+ cloglog presence companion) | GO as enabler / fold-stability insurance; NO-GO as additive skill | SERVED 4-stn enablers ON `+0.1547` (5/5, worst fold `+0.046`, PIT KS p `0.614`, conf 0.61); OFF `+0.0778`. cloglog presence companion: log-loss skill `-0.127`, Brier `-0.001` (report-only, no skill). | `modeling/estimator.py` `fit_glm(use_station_effects="partial_pool", pooling_tau, ridge_lambda)` + `modeling/fit_kernels.py` `run_fit` (nested `(tau, ridge)`, `report["presence_reframe"]`). Landed OFF/byte-identical. | With / instead of rank 1. NOT additive with TA5 (both regularize the same fit; pick ONE, do not double-count). Land as the clean baseline before judging covariates. |
| 3 | TA3 AIS effort term in `log E` | GO conditional (de-bias wire); skill NOT-MEASURED | Baseline reproduced `+0.0778`. `log E` is currently FLAT. AIS delta NOT-MEASURED (Marine Cadastre fetch infeasible in-env). Reasoned band `-0.01..+0.03`, most likely near-zero. | `modeling/ais_noise.py` (`D=exp(-kappa*I)`, `kappa=0` exact no-op; exists) + `modeling/design.py` `build_design(noise_by_station=)` + `modeling/effort.py` + `modeling/fit_kernels.py` `_station_intensity_fn` (`log D_ais` on integration grid) + `src/aws_backend/sources/ais.py` (per-station proximity index) + ingest. | Before judging TB2/TB5 (clean, non-flat `log E` baseline). Value is cleaner `k_diel`/`k_season` + fold stability, not `+0.144`. |
| 4 | TB4 ONC / JASCO Boundary Pass (ECHO published) | GO conditional (the real new-observation lever) | MEASURED `6` net-new summer (JJA-2016) SRKW-certain presence-days, disjoint 2015-2019 epoch; `0` JJA-2017, `0` AMAR. SRKW CV-skill NOT-MEASURED (effort denominator needs ONC Oceans 3.0 token). | `src/aws_backend/ingest_multistation.py` (new `ECHO_NODES` + `build_echo_records`, `source="onc_jasco_echo_2025"`, `boundary_pass_uls`/`_amar`) + region expansion (Boundary Pass is outside `SAN_JUAN_BOUNDS`) + `modeling/studies/common.py` `STATION_COORDS` + `log E` effort frame. | After the cheap regularizer integrate. Operator region-expansion + ONC token gate. Small but genuinely new summer signal. |
| 5 | TB1 Port Townsend + Bush Point (OrcaHello) | CONDITIONAL GO (off-season coverage) / NO-GO (summer +0.144 lever) | MEASURED `25` net-new region presence-days (lower bound, range `[25, ~40]`); `0` summer (JJA). Expected summer-gate effect ~0 to slightly negative. | `src/aws_backend/geo_region.py` (`ADMIRALTY_INLET_BOUNDS` two-box) + `src/aws_backend/ingest_multistation.py` (`EXTRA_NODES` PT/BP + `cache_path` + retain `id` for `(station,t,id)` dedupe) + `modeling/studies/common.py` `STATION_COORDS` + node-specific `log E` (BP outages). | Behind a model change that consumes off-season mass (TA2). Operator region-expansion decision D1. Not a summer promotion lever. |
| 6 | TB2 SST-front gradient (MUR/VIIRS), season-orthogonalized | GO conditional, DEFERRED | Marginal NOT-MEASURED (MUR/VIIRS feed unreachable in-env; 5 km blended understates channel fronts; fabrication refused per B.2). Synthetic validation of the landed wire: season-collinear `-0.0001` (refuses to launder `k_season`), season-independent `+0.140`. | `modeling/estimator.py` (`fit_glm(linear_covariates=, season_orthogonalize=)`, landed no-op) + `modeling/design.py` `build_design(linear_by_station=)` + operator MUR/VIIRS feed (B.9 EC2/S3). | After the clean baseline, only if a real feed lands. Demoted: the clean baseline already clears the bar, so a geometry-damped covariate is no longer load-bearing and risks a negative marginal. |
| 7 | TB5 SalishSeaCast subtidal currents / shear | NO-GO at current N / conditional GO behind nodes | Marginal NOT-MEASURED; reasoned near-zero / laundered-tidal at the 4-clustered geometry. SalishSeaCast reachability also NOT-MEASURED. | shares the landed aperiodic wire + a NOT-landed `modeling/subtidal_currents.py` de-tide module + collinearity guard. | Strictly AFTER TB1/TB4 spatially separated nodes are in the served store. Spatial-front signal is unobservable across one ~8x9 km cluster. |
| 8 | TB3 real Albion feed refresh + run-anomaly (D1) | SUPPORTING-ONLY / WITHHELD | Expected `+0.02..+0.08` NOT-MEASURED. Feed already real (G3); L3 stays WITHHELD; lag scan full-span p `0.394`. | `src/aws_backend/sources/salmon.py` (live 2026 Albion fetch, EC2) + `modeling/studies/salmon_lag.py` (frozen pre-registered Jun-Sep re-test). | Not a lever; housekeeping for a future summer OOS test. G3 decision bar (every criterion fails today). |

## 2. Dead-ends (NO-GO; do NOT integrate)

- **TA1 2-state occupancy MMPP** -- the apparent `+0.137` is `baseline_GLM x a single per-fold constant`
  (zero occupancy content), breaks PIT (KS p `4.4e-05`), and does NOT repair the event-level
  time-rescaling GOF (oracle smoothed intensity still leaves pooled KS p `0.0`). Keep at most as an
  optional GOF diagnostic beside Hawkes. Not a skill lever.
- **TA4 in-repo nonlinearities** (F1 lunar x diel `-0.0095`, A1 slack/max-flow `-0.0054`) -- both worse
  than the `+1`-harmonic control `-0.0038`. Pure df cost; no squeezed nonlinearity survives CV.
- **Spatial LGCP / GP intensity at current N** -- DE dead-end (M2/SYN supersede the stale "GO"). Effective
  N ~300 onsets cannot support a latent field.
- **NB to ZI / hurdle COUNT upgrade** -- NO-GO (SYN sec 2; DE3 row #10). Keep the presence-hurdle REFRAME
  (TA2 PATCH-3) lexically and semantically distinct; never feed the cloglog head into the served count
  intensity.
- **Hawkes self-excitation as served skill** -- NO-GO as served intensity. PRESERVE it as the event-level
  GOF diagnostic that justifies the adopted bin-level timing gate; do not delete the diagnostic.
- **CUTI / BEUTI upwelling, HF-radar surface currents, terrain on the temporal gate, full PINN /
  reservoir-ESN / EDM / neural-TPP / SDE-diffusion movement, synthetic augmentation** -- all held NO-GO
  by the DE drift-guard; none lift held-out skill at our N.

## 3. The single highest-value integrate to run first

**TA5 smoothness prior.** It is the cheapest and most load-bearing: a soft roughness penalty on the
existing kernels (a variance reducer; default byte-identical), no new data, no new covariate, no extra
harmonic. It is the one lever MEASURED to clear all five G2 bands on the SERVED 4-station store
(`+0.1686`, 5/5, LB `+0.109`, PIT KS p `0.090`, conf 0.63). The integrate is a single-editor default flip
of `modeling/estimator.py` + `modeling/fit_kernels.py`; promotion is then a recorded B.1 supervisor
decision plus an upload-enabled refit (the explicit promotion step, operator-gated).

Caveat O0 must carry: TA5 and TA2 are NOT additive evidence (both regularize the same overfit-prone
4-station fit). Promote ONE configuration on a recorded decision. TA5 is the graduated lever and slightly
stronger; TA2 is the fold-stability / held-out-station enabler. The single-station served fit clears
neither bar, so the promotion rests on the live 4-station store remaining 4-station.

## 4. Gate each candidate must pass before any promotion

| Candidate | Gate before promotion |
|---|---|
| TA5 | G2 PROMOTE band on SERVED data (MEASURED PASS in `TA5_SERVED_VERDICT.md`) + a recorded B.1 supervisor decision + an upload-enabled refit. |
| TA2 | Same G2 PROMOTE band (MEASURED PASS in `TA2_TA3_BASELINE_VERDICT.md`) + B.1 decision. Promote at most ONE of TA5 / TA2 (no double-count). |
| TA3 | Operator AIS ingest (Marine Cadastre, deploy-gated) THEN fold-stable served `block_cv`; accept only if it does not degrade fold stability. No skill credit until measured. |
| TB4 | ONC Oceans 3.0 effort frame (token, operator gate) + fold-stable summer-conditioned served `block_cv` + a region-expansion decision (Boundary Pass outside `SAN_JUAN_BOUNDS`). |
| TB1 | Operator region-expansion decision D1 + summer-conditioned served `block_cv` (expected ~0 to negative). Off-season coverage only, NOT a summer promotion lever. |
| TB2 | Real MUR/VIIRS feed (not 5 km blended) + fold-stable POSITIVE marginal vs the regularized baseline + absolute SST never enters (B.2 rail, enforced by the landed season-orthogonalization). |
| TB5 | Spatially separated nodes (TB1/TB4) actually in the served store FIRST, then a measured marginal vs the regularized baseline with the collinearity guard. |
| TB3 | G3 decision bar (stock-aligned + frozen pre-registration + FRESH OOS on NEW data + LOYO >= 3-of-n at n >= 8 + multiplicity-clean p + consistent counts). Every criterion fails today; L3 stays WITHHELD. |

## 5. Wave 2 (PATCH-SPEC) status

Wave 2 writes a PATCH-SPEC section per GO / GO-conditional candidate (the precise single-editor change to
the served path, the gate it must pass before promotion, and the expected confidence movement IF the gate
passes). It is GATED on O0's go-ahead per the waveset's between-wave reporting contract, and is NOT
written in this pass. The per-candidate seams and gates above are the inputs Wave 2 expands; the
authoritative source patch-specs already exist in the lane docs (TA5 sec 6, TA2 sec 4, TA3 sec 8,
TB4 PATCH-SPEC, TB1 sec 8) and the served-measured verdict docs in
`.cca/catalogue/O0/20260627_integrate-promote-launch-handoff/`.

## 6. Rails confirmed (this pass)

Nothing promoted, fit, deployed, fetched-to-write, ingested, store/S3-written, or committed. No
`git add`. No edit to `modeling/**` or `src/aws_backend/**`. Only this doc written, under
`.cca/catalogue/O0/20260627_mlops/`. Effective confidence stays 0.0.

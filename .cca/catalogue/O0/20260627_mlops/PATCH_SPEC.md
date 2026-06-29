# Wave 2 PATCH-SPEC (propose-only) for the served forecast path

Sub-orchestrator: MLOps integrate-grounding waveset, Wave 2. Date: 2026-06-28 (America/New_York).
Repo: `/Users/gilraitses/orcast`. Answers to the O0 central orchestrator.

This is a SPEC deliverable only. No model runtime code is modified, no fit is run, no promotion, no
deploy, no commit, no `git add`. Effective confidence stays 0.0. The B.1 supervisor decision (TA5 vs TA2
as the served regularizer) is NOT recorded; nothing here records it.

Grounding doc: `INTEGRATE_GROUNDING.md` (Wave 1 ranked plan). Every metric below traces to a Wave 1
measurement (cited inline); any quantity without a citation is marked NOT-MEASURED.

## 0. Code-state finding that shapes every spec below

The integrate-promote-launch-handoff thread already LANDED the TA5, TA2, TA3, and TB2/TB5 surfaces into
the convergence files as default-OFF, byte-identical opt-ins (verified read-only this pass):

- `modeling/estimator.py`: `fit_glm(..., smoothness_lambda=0.0, smoothness_order=2, ridge_lambda=0.0,
  pooling_tau=0.0, use_station_effects=True, linear_covariates=(), ...)`; `make_fit_predict(...,
  smoothness_lambda_grid=None, baseline_grid=None, linear_covariates=(), season_orthogonalize=False)`;
  helpers `_select_smoothness_lambda`, `_select_baseline_hypers`, `_season_orthogonalize`.
- `modeling/fit_kernels.py`: `run_fit(..., smoothness_prior=None, baseline_enablers=None)` gated by
  `_smoothness_prior_enabled()` (`ORCAST_SMOOTHNESS_PRIOR`) and `_baseline_enablers_enabled()`
  (`ORCAST_BASELINE_ENABLERS`); `SMOOTHNESS_LAMBDA_GRID` / `SMOOTHNESS_ORDER`; the honesty report blocks
  `_smoothness_prior_report` (with the `n_harmonics=1` control) and `_baseline_enablers_report`; the
  `presence_reframe` companion; the `smoothness_regularized` serving disclosure.
- `modeling/ais_noise.py` exists (TA3 detectability factor, `kappa=0` exact no-op).

Consequence: for the MEASURED regularizer levers (TA5, TA2) the remaining "integrate" is NOT new code
authorship. It is (a) a single-editor DEFAULT activation of one opt-in (flag default flip, or the env var
set on the promotion-step refit) and (b) a recorded B.1 supervisor decision plus an upload-enabled refit.
Each spec below states exactly which of these it is. The modeling tree is local-only / untracked (B.6),
so "default flip" means a local edit to the untracked file, never a tracked commit by an agent.

## 1. Mutual exclusivity (read before P1 / P1-ALT)

TA5 (smoothness prior) and TA2 (partial-pool + flat ridge) are TWO FORMS OF THE SAME REGULARIZER on the
same overfit-prone 4-station served fit. They are NOT additive evidence; both reduce variance on the same
fit and `TA2_TA3_BASELINE_VERDICT.md` states explicitly "do not double-count". Exactly ONE may be
activated as the served configuration. P1 (TA5) is the ranked-first lever; P1-ALT (TA2) is the alternative
form, included per the O0 mandate and clearly marked. Choosing between them is the B.1 operator gate in
section 8. The `fit_glm` signature does accept both penalties simultaneously, but composing them is out of
scope here and is NOT proposed (it would need its own served measurement; not done).

---

## P1 -- TA5 smoothness (roughness) shape prior  [RANKED FIRST; GO; served-measured]

**Files / functions.** `modeling/estimator.py` `fit_glm` + `_kernel_penalty_vector` (math, landed);
`modeling/fit_kernels.py` `run_fit` + `_select_smoothness_lambda` + `_smoothness_prior_report` +
`make_fit_predict` (selection + reporting, landed); serving payload `smoothness_regularized` /
`smoothness_lambda` (landed).

**Math / parameterization.** A soft second-derivative roughness penalty on the cyclic-kernel Fourier
coefficients: penalty weight `lambda * h^(2*order)` per `{cov}__cos_h` / `{cov}__sin_h` coefficient
(`order=2` => `h^4`), with `const` and `st__*` columns unpenalized; fit by NB2
`GLM.fit_regularized(alpha=penalty_vec, L1_wt=0.0)` (pure L2 ridge = a smoothing-spline penalty in the
Fourier basis). `lambda` is selected by NESTED `block_cv` inside each training fold over
`SMOOTHNESS_LAMBDA_GRID` (e.g. `{0, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1}`), never hardcoded, re-selected when N
changes. This adds NO degrees of freedom (it is a variance reducer on existing kernels; no LGCP/GP, no new
covariate, no extra harmonic) and stays inside the served log-linear separable-kernel NB2 form.

**Config / flag surface (the single-editor change being proposed).** Default activation of the existing
opt-in: either set `run_fit(smoothness_prior=True)` as the served default, or set
`ORCAST_SMOOTHNESS_PRIOR=1` on the promotion-step refit. No other code change. Default today is OFF
(`_smoothness_prior_enabled()` reads the env; `smoothness_prior=None` falls back to it), which keeps the
served fit byte-identical (B.4). When ON, `kernel_curves()` must publish bands as bootstrap or omit them
(`fit_regularized` returns no covariance), and the serving payload carries `smoothness_regularized: true`.

**Held-out CV metric it moves, and by how much (MEASURED, cited).** Served 4-station 5-fold `block_cv`
mean-deviance-skill (source: Wave 1 `TA5_SERVED_VERDICT.md`, reproduced in `INTEGRATE_GROUNDING.md` rank 1):

| Variant | mean skill | folds>0 | across-fold LB | PIT (KS p) | P0-map confidence |
|---|---|---|---|---|---|
| OFF (baseline) | `+0.0778` | 4/5 | `+0.004` | calibrated (0.364) | 0.49 |
| ON (TA5) | `+0.1686` | 5/5 | `+0.109` | calibrated (0.090) | 0.63 |

`n_harmonics=1` hard control reaches only `+0.0835` (so the gain is graded shrinkage, not fewer
harmonics). Served single-station fit ON is only `+0.0037` (does NOT clear the bar there); the binding
gate is the live 4-station store. EXPERIMENT-store value was `+0.1767` (`TA5_shape_priors.md`).

**Rollback.** Set the flag/env back to OFF. `smoothness_lambda=0` restores the unpenalized `.fit()` path,
so the served fit is byte-identical to today. No data migration, no store change; `data/models/fit_report.json`
is only touched on a deliberate upload-enabled promotion refit, which is itself the B.1 step.

**Acceptance test that gates promotion (G2 PROMOTE band on SERVED data).** All five must hold on the
served 4-station refit, measured under `write_outputs=False` first:
1. mean skill `>= +0.144` (MEASURED `+0.1686`, PASS).
2. `>= 4/5` folds positive (MEASURED 5/5, PASS).
3. across-fold lower bound `mean - t*SE >= +0.078` (MEASURED `+0.109`, PASS).
4. held-out PIT calibrated (MEASURED KS p `0.090 > 0.05`, PASS; re-confirm on the promotion refit, the
   margin is thinner than OFF's 0.364).
5. an L1 null beaten (MEASURED diel, lunar, season, PASS).
Then the deterministic supervisor draft reads `promote` (MEASURED in `TA5_SERVED_VERDICT.md`).

**Expected confidence movement IF the gate passes and the operator records B.1.** The P0 confidence map
would set effective_confidence to `0.63`. This pass does NOT do that; effective confidence stays 0.0 until
the operator records the decision and runs the upload-enabled refit.

---

## P1-ALT -- TA2 partial-pool + flat nested-CV ridge  [ALTERNATIVE FORM of the same regularizer; mutually exclusive with P1]

**Files / functions.** `modeling/estimator.py` `fit_glm(use_station_effects="partial_pool", pooling_tau,
ridge_lambda)` + `_select_baseline_hypers` (landed); `modeling/fit_kernels.py` `run_fit(baseline_enablers=...)`
+ `_baseline_enablers_report` + the `presence_reframe` companion (landed).

**Math / parameterization.** Replace the fixed-effect station dummies with a Gaussian random station
intercept implemented as a ridge `1/(tau^2 * nobs)` on station deviations (global intercept unpenalized),
plus a flat ridge `ridge_lambda` (`1/s_k^2`) on the Fourier kernel coefficients. `(tau, ridge)` selected
by nested `block_cv` per fold (`tau` grid `{0.5,1,2,5}`, ridge grid `{1,0.25,0}`). A cloglog presence
companion head (`report["presence_reframe"]`) is reported alongside the count deviance and is kept
strictly distinct from the NO-GO NB->ZI/hurdle count upgrade; it never feeds the served count intensity.

**Config / flag surface (proposed single-editor change).** Default activation of the existing opt-in:
`run_fit(baseline_enablers=True)` or `ORCAST_BASELINE_ENABLERS=1`. Default today is OFF (byte-identical).

**Held-out CV metric it moves, and by how much (MEASURED, cited).** Served 4-station 5-fold `block_cv`
(source: Wave 1 `TA2_TA3_BASELINE_VERDICT.md`, `INTEGRATE_GROUNDING.md` rank 2):

| Variant | mean skill | folds>0 | worst fold | PIT (KS p) | P0-map confidence |
|---|---|---|---|---|---|
| OFF (FE baseline) | `+0.0778` | 4/5 | `-0.038` | 0.364 | 0.49 |
| ON (TA2 enablers) | `+0.1547` | 5/5 | `+0.046` | 0.614 | 0.61 |

Mechanism: the random intercept shrinks the held-out / structurally-absent station to the population mean
(removes the FE reference-coding worst-fold swing `-0.038 -> +0.046`), and the mild ridge raises the mean
and improves calibration. The cloglog presence companion carries NO measured skill over a per-effort
presence climatology (log-loss skill `-0.127`, Brier `-0.001`); it is a calibrated report-only diagnostic.

**Rollback.** Flag/env OFF restores the fixed-effect unpenalized fit (byte-identical). Same store / report
discipline as P1.

**Acceptance test (G2 PROMOTE band on SERVED).** mean `>= +0.144` (MEASURED `+0.1547`, PASS); `>= 4/5`
folds (MEASURED 5/5, PASS); across-fold lower bound `>= +0.078` (per `TA2_TA3_BASELINE_VERDICT.md` the
enablers clear the G2 robust check; re-confirm the LB numerically on the promotion refit); PIT calibrated
(MEASURED KS p `0.614`, PASS); L1 null beaten (PASS). Then the supervisor draft reads `promote`.

**Expected confidence movement IF the gate passes and the operator records B.1.** P0 map would set
effective_confidence to `0.61`. Not done here.

**Mutual-exclusivity note.** Activate EITHER P1 OR P1-ALT, never both as the served default. TA5 is the
graduated lever and slightly stronger (`+0.1686` vs `+0.1547`); TA2 is the fold-stability / held-out-station
insurance with the strongest calibration (PIT 0.614). The choice is the B.1 gate (section 8).

---

## P2 -- TA3 AIS effort term in `log E`  [GO-CONDITIONAL; de-bias wire; skill NOT-MEASURED]

**Files / functions.** `modeling/ais_noise.py` (`detectability_factor` / `log_detectability`, `kappa=0`
exact no-op; landed); `modeling/design.py` `build_design(noise_by_station=)`; `modeling/effort.py`
detectability passthrough; `modeling/fit_kernels.py` `_station_intensity_fn` (`log D_ais` on the
integration grid); `src/aws_backend/sources/ais.py` (upgrade to a per-station proximity index) and the
`src/aws_backend/ingest_timeseries.py` ingest of a new `env_vessel_noise` per-station stream.

**Math / parameterization.** A multiplicative detectability factor `D_ais(s,b) = exp(-kappa * I_norm(s,b))`
clipped to `[1e-2, 1]` on the existing exposure offset (`log E_eff = log E + log D_ais`), where `I` is a
distance-weighted vessel-proximity load and `kappa` is a fixed (not fitted) masking scalar. Zero added
presence parameters; `kappa=0` / missing index => `D=1` exact no-op. B.2 role: effort / exposure only,
never laundered into a presence kernel. Carries a `coverage="us_side_partial"` flag (US-only Marine
Cadastre under-represents the BC-side Haro Strait lane; the index is a lower bound on masking).

**Config / flag surface.** Operator-gated AIS ingest (Marine Cadastre, a SEPARATE deploy step) THEN set
`noise_by_station` + `ais_kappa>0` and score. No served default flip is proposed until measured.

**Held-out CV metric.** Baseline reproduced `+0.0778` (Wave 1 `TA3_ais_effort.md`). `log E` is currently
FLAT (`effort_assumed_continuous=True`), so AIS would be the first real `log E` structure. The skill delta
is **NOT-MEASURED** (real Marine Cadastre fetch infeasible in-env; fabrication refused per B.3). Reasoned
band (NOT-MEASURED) `-0.01..+0.03`, most likely near-zero; value is cleaner `k_diel`/`k_season` and fold
stability, not `+0.144`. It cannot reach the bar alone.

**Rollback.** `ais_kappa=0` / `noise_by_station=None` => byte-identical. Ingest rollback deletes only the
new `env_vessel_noise` prefix.

**Acceptance test.** After the operator AIS ingest: fold-stable served `block_cv` (`>= 4/5` folds,
across-fold lower bound, PIT) vs the activated regularized baseline; accept ONLY if it does not DEGRADE
fold stability while making the kernel curves cleaner. No skill credit, no confidence movement until
measured. This is a clean-the-baseline step that should precede judging TB2 / TB5, not a promotion lever.

---

## P3 -- TB4 ONC / JASCO Boundary Pass  [GO-CONDITIONAL; the new-observation lever; summer count MEASURED small, CV-skill NOT-MEASURED]

**Files / functions.** `src/aws_backend/ingest_multistation.py` (new `ECHO_NODES` map +
`build_echo_records(annotations_csv, effort_mask)`, `source="onc_jasco_echo_2025"`, station keys
`boundary_pass_uls` / optionally `boundary_pass_amar`, grouped via `_put_grouped_by_station`); region gate
(Boundary Pass is OUTSIDE `SAN_JUAN_BOUNDS`, a region-expansion decision); `modeling/studies/common.py`
`STATION_COORDS` (`49.04,-123.32` ULS; `48.76,-123.07` AMAR); `log E` effort frame.

**Data / parameterization.** Net-new SRKW presence-days from the published ECHO `Annotations.csv`
(filter `Dataset in {StraitofGeorgia, BoundaryPass}`, `Ecotype==SRKW`, bin `UTC` by date), with an effort
denominator reconstructed from deployment window x ONC Oceans 3.0 uptime mask (ULS continuous; AMAR duty
cycle NOT-MEASURED). Disjoint 2015-2019 epoch => zero same-day double-count with the ~2020+ served cache.

**Held-out CV metric.** Summer SRKW presence-day count is **MEASURED**: `6` net-new disjoint-epoch
SRKW-certain days (all JJA-2016, Strait of Georgia ULS), `0` JJA-2017, `0` AMAR (Wave 1
`TB4_PRESENCE_DAY_COUNT.md`). The SRKW CV-mean-deviance-skill is **NOT-MEASURED** (no effort denominator
without an ONC Oceans 3.0 token; presence-only would bias the rate, B.2). Materially better than TB1 (0
summer) but a small payload (6 days, one summer).

**Rollback.** Idempotent `(station,t,id)` write; rollback deletes only the new `boundary_pass*` prefixes;
existing stations untouched (the W6 pattern).

**Acceptance test.** ONC effort frame reconstructed (token, operator gate) AND fold-stable
summer-conditioned served `block_cv` vs the activated baseline AND a region-expansion decision recorded.
Flag the cross-station consistency risk (new BC corridor, older epoch). NO-GO if the parsed summer count is
~0 (it is 6, marginal) or if effort cannot be reconstructed. Not prioritized ahead of the cheap regularizer
integrate; revisit if the operator wants the BC corridor.

---

## P4 -- TB1 Port Townsend + Bush Point  [CONDITIONAL GO as off-season coverage; NO-GO as a summer +0.144 lever]

**Files / functions.** `src/aws_backend/geo_region.py` (`ADMIRALTY_INLET_BOUNDS` two-box gate, keep
`SAN_JUAN_BOUNDS` unchanged); `src/aws_backend/ingest_multistation.py` (`EXTRA_NODES` PT `48.13569,-122.76045`
/ BP `48.03371,-122.6039` + per-node `cache_path` + retain `id` for `(station,t,id)` dedupe + a
station-name normalization map); `modeling/studies/common.py` `STATION_COORDS`; node-specific `log E`
(Bush Point outage-derived monitored hours).

**Held-out CV metric.** `25` net-new region presence-days MEASURED (lower bound, range `[25, ~40]`); `0`
summer (JJA) MEASURED (Wave 1 `TB1_port_townsend_bush_point.md`). Expected summer-conditioned CV-skill
effect (NOT-MEASURED) ~0 to slightly negative (off-season mass can dilute the summer signal and worsen
cross-station consistency). This is off-season COVERAGE, not a promotion lever.

**Rollback.** Two-box gate keeps the served core gate untouched; ingest rollback deletes only
`port_townsend` / `bush_point` prefixes.

**Acceptance test.** Operator region-expansion decision D1 + summer-conditioned served `block_cv`. Ground
behind a model change that consumes off-season mass (P1-ALT / TA2 random intercept). Do NOT credit on the
summer gate; do NOT let any doc reframe these nodes as a summer +0.144 lever (DE3 row #10).

---

## 2. Deferred / not specced (with reason)

- **TB2 SST-front gradient** (`fit_glm(linear_covariates=, season_orthogonalize=)` + `build_design(linear_by_station=)`,
  wire LANDED): GO-conditional but DEFERRED. Marginal NOT-MEASURED (MUR/VIIRS feed unreachable; fabrication
  refused, B.2). The activated regularizer already clears the bar, so a geometry-damped covariate is no
  longer load-bearing and risks a negative marginal. Spec deferred until a real feed lands; acceptance =
  fold-stable POSITIVE marginal vs the regularized baseline AND absolute SST never enters.
- **TB5 SalishSeaCast subtidal currents**: NO-GO at the current 4-clustered geometry; spatial-front signal
  unobservable across one ~8x9 km cluster. Strictly AFTER TB1/TB4 spatially separated nodes. Not specced.
- **TB3 Albion run-anomaly**: SUPPORTING-ONLY / WITHHELD; L3 lever is summer presence-days, not the feed.
  Not a promotion candidate; G3 bar fails today. Not specced.
- **Dead-ends (NO patch-spec):** TA1 MMPP (artifact, breaks PIT, no GOF repair), TA4 in-repo nonlinearities,
  LGCP/GP at N, NB->ZI/hurdle count upgrade, Hawkes-as-served-skill (keep only as the event-level GOF
  diagnostic), CUTI/BEUTI, HF-radar, terrain-on-temporal-gate, full PINN / reservoir / EDM / neural-TPP.

## 3. The B.1 operator gate (explicit, blocking)

Before ANY fit-with-upload or promotion of P1 / P1-ALT:

1. The operator records a B.1 supervisor decision choosing EXACTLY ONE served regularizer: TA5 (P1, ranked
   first, `+0.1686` -> map 0.63) OR TA2 (P1-ALT, `+0.1547` -> map 0.61). They are mutually exclusive (no
   double-count). This decision is NOT recorded; this pass does not record it.
2. Only on that recorded decision does the single-editor integrate flip the chosen default and run the
   upload-enabled refit (the explicit promotion step). Until then effective_confidence stays 0.0 and the
   served fit is byte-identical.
3. P2 (TA3), P3 (TB4), P4 (TB1) are each separately operator-gated (AIS ingest; ONC token + region
   expansion; region expansion D1) and none is a promotion lever; they do not move confidence on their own.

## 4. Adversarial gate (self-check on this spec)

- Every served metric (`+0.1686`, `+0.1547`, `+0.0778`, conf 0.63 / 0.61 / 0.49, the 6 TB4 summer days,
  the 25 TB1 region days) traces to a cited Wave 1 measurement. No metric is invented.
- Every NOT-MEASURED quantity (TA3 AIS delta, TB4 CV-skill, TB1 summer CV effect, TB2/TB5 marginals) is
  labeled NOT-MEASURED, with the reason. No reasoned band is presented as measured.
- No promotion language: P1/P1-ALT are stated as "IF the gate passes and the operator records B.1, the
  P0 map WOULD set confidence to X"; nothing is promoted, and the B.1 decision is flagged as not recorded.
- TA5 and TA2 are stated as mutually exclusive in three places (section 1, P1-ALT, section 3).

## 5. Rails confirmed (this pass)

Nothing promoted, fit, deployed, fetched-to-write, ingested, store/S3-written, or committed. No `git add`.
No edit to `modeling/**` or `src/aws_backend/**` (the existing default-OFF wires were read, not changed).
Only `PATCH_SPEC.md` and the `STEP_LOG.md` entry were written, under
`.cca/catalogue/O0/20260627_mlops/`. Effective confidence stays 0.0.

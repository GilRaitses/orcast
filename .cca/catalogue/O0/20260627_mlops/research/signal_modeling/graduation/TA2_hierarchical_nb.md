# TA2 -- hierarchical/partial-pooling NB + nested-CV regularization + presence-hurdle reframe

Agent: graduation waveset subagent TA2. Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`.
This doc only. No convergence-file edit, no served write, no `data/models/fit_report.json`, nothing
deployed/promoted/committed. Effective confidence stays 0.0.

Authority read first: `GRADUATION_DISPATCH.md` (shared context, RECALIBRATION-FROM-DE drift-guard,
fit-safety, TA2 lane), `GRADUATION_WAVESET_CHARTER.md` (sec 1-2), `20260627_signal-modeling-launch-handoff/
HANDOFF_CHARTER.md` sec B, `SYNTHESIS_signal_modeling.md` + `M1_sparse_data_methods.md` (ranks 1-3),
`docs/methodology/FORECAST_KERNELS.md` + `CALIBRATION_STUDIES.md` + `research/forward/G2_promotion_protocol.md`.

**DRIFT-GUARD obeyed (DE3 row #10).** The GO graduate scored here is the **presence-hurdle REFRAME**
(Bernoulli/cloglog on per-bin *presence*, same kernels + `log E`, scored with Brier/log-loss alongside
the count deviance). An **NB->ZI/hurdle COUNT upgrade** on the hourly NB target is **NO-GO** (SYN sec 2;
DE3 #10) and is NOT prototyped here. The two are kept distinct throughout this doc and the patch-spec.

---

## 1. What was built and measured (this is a REAL fit, numbers MEASURED)

A scratch prototype (`/tmp/ta2_*.py`, outside the repo; no repo file other than this doc written) built the
4-station design exactly as `modeling.studies.level2_multistation` does -- the production `haro_strait`
`acoustic_detections` stream read from S3 + the cached OrcaHello index for `orcasound_lab` /
`andrews_bay` / `north_san_juan_channel`, plus S3 `env_currents` + `station_uptime` -- via
`modeling.design.build_design` (1 h bins). Ran in `.venv-modeling` with
`ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads
AWS_REGION=us-west-2`, `fit_kernels._maybe_write_s3 = lambda: None`, and `write_outputs` semantics never
invoked (no `run_fit` writer path called).

Data realized (mixed-provenance experiment store, identical to the +0.078 experiment):

| station | detections | station-bins | bins with `y>0` |
|---|---:|---:|---:|
| orcasound_lab | 1029 | 50081 | 280 |
| haro_strait | 761 | 5361 | 181 |
| andrews_bay | 265 | 3108 | 21 |
| north_san_juan_channel | 34 | 8349 | 7 |
| **total** | **2089** | **66899** | **489** (presence rate 0.0073) |

Effective independent onsets ~300 pooled (M1 0.2), 4 stations, J=4. Covariates that cleared phase-coverage
in the 4-station design: `diel, tide, lunar, season` (all four; the single-station served fit excludes
tide/season for coverage, but the pooled multi-station window covers them).

### 1.1 Construction

- **Penalized NB2 IRLS (hand-rolled, numpy), log link, offset `log E`.** Reproduces the served estimator's
  Fourier basis (`modeling.estimator._build_features`, 2 harmonics x 4 kernels) and its Cameron-Trivedi NB2
  `alpha` seed. Step-halving on the penalized NB2 negative-log-likelihood for robustness.
- **Random station intercept (partial pooling).** Station effects parametrized as deviations penalized with
  ridge `lambda_s = 1/tau^2` (a Gaussian random intercept's MAP Hessian), with a **weakly-informative
  half-normal(0, ~1) prior on the group SD `tau`** -- J=4 only weakly identifies `tau`, so `tau` is *selected
  by nested CV inside each fold* over a half-normal-consistent grid `tau in {0.5, 1.0, 2.0, 5.0}` (log-rate
  scale) rather than free-estimated. The global intercept is unpenalized, so the penalty (not reference
  coding) breaks the const/station collinearity -- this is what lets a sparse or structurally-absent station
  borrow strength instead of taking an arbitrary reference level.
- **Regularization.** Ridge on the Fourier kernel coefficients, `lambda_k = 1/s_k^2`, `s_k in {1, 2, inf}`,
  also selected by **nested CV inside each fold** (so the held-out skill is not optimistically biased by
  tuning `lambda` on the scored data; M1 1.2). Elastic-net would add coefficient selection; ridge is the
  variance-reducer scored here and sklearn is absent from `.venv-modeling`, so the penalized-IRLS path is the
  one wired.
- **Presence-hurdle reframe.** A **complementary-log-log GLM on per-bin presence `1[y>0]`** with the *same*
  kernels + offset `log E`. cloglog is the exact link for presence from a rate: `P(y>0) = 1 - exp(-lambda*E)`,
  so `cloglog(p) = log(lambda) + log E` -- it shares the count model's linear predictor (no second count
  process; this is the reframe, NOT a ZI/hurdle count upgrade). Scored with Brier + log-loss skill vs a
  per-effort presence climatology, ALONGSIDE the count deviance.

### 1.2 Scoring

Held-out, time-blocked, 5-fold, scored *exactly* like `modeling/validation/crossval.py block_cv`
(equal-width time blocks via `assign_time_blocks`; climatology = rate-per-effort estimated on the train
fold; deviance skill `1 - dev_model/dev_base` from `validation.diagnostics.poisson_deviance`). Lambda
selection is nested (3 inner time-blocks) inside each of the 5 outer folds. Calibration = pooled held-out
randomized NB PIT (`validation.diagnostics.randomized_pit`) KS-vs-uniform. **No in-sample number is used to
judge a graduate** (charter sec 4 / SYN sec 4).

---

## 2. Measured results (per-fold, MEASURED)

### 2.1 Count model -- held-out deviance skill

| model (fitter) | per-fold skill | mean | folds>0 | across-fold 95% lower bound | held-out NB PIT |
|---|---|---:|:---:|---:|---|
| **Served anchor: NB2 + FE station dummies** (statsmodels, the published +0.078) | -0.038, 0.065, 0.140, 0.066, **0.156** | **+0.0778** | 4/5 | **+0.004** | -- |
| NB2 + FE dummies (same model, my robust IRLS) | -0.038, 0.065, 0.140, 0.066, **-0.077** | +0.0312 | 3/5 | -0.052 | calibrated (p=0.25) |
| **Partial-pooling NB (random intercept), nested-CV tau** | -0.126, 0.065, 0.140, 0.066, **0.074** | +0.0438 | 4/5 | -0.051 | not (p=0.014) |
| **Partial-pooling NB + ridge kernels, nested-CV (tau, s_k)** | -0.123, 0.068, 0.143, 0.070, **0.074** | +0.0466 | 4/5 | -0.048 | **calibrated (p=0.235)** |

Nested CV chose `tau=5` (weak pooling) on 4/5 folds and `tau=1` on the last; ridge chose `s_k=1` on every
fold.

**The fold-5 split is the load-bearing observation, and it is honest, not a bug.** In the 5-equal-width
time-blocking, `andrews_bay`'s entire detection window (all 3108 bins, 21 presence bins) lands in the last
block, so `andrews_bay` is **wholly held out** in fold 5 (verified: fold-5 train has 0 `andrews_bay` rows).
A fixed-effect station model has no principled prediction for a station absent from training -- it
extrapolates to whatever the *reference coding* implies:

- statsmodels drops the absent station and andrews inherits the **haro_strait** baseline (high) -> fold-5
  skill +0.156 (the value inside the published +0.078);
- the same model under a different (andrews-as-reference) coding pins andrews to a **low** const -> fold-5
  skill -0.077.

Both are arbitrary artifacts of reference coding. The **random intercept shrinks the held-out station to the
population mean** (a principled, coding-invariant prediction) -> fold-5 skill +0.074, and the across-fitter
fold-5 swing of ~0.23 deviance-skill collapses. This is exactly M1's mechanism (1.1: "shrinks sparse/absent
stations toward the population mean ... models heterogeneity as a variance component instead of over-fitting
it") observed on the real data.

### 2.2 Presence-hurdle reframe -- held-out Brier / log-loss skill (vs per-effort presence climatology)

| model | per-fold log-loss skill | mean log-loss skill | mean Brier skill | folds>0 (log-loss) |
|---|---|---:|---:|:---:|
| cloglog + FE dummies | -0.022, -0.041, 0.040, -0.027, 0.064 | +0.003 | -0.005 | 2/5 |
| cloglog + partial-pooling + ridge, nested-CV | -0.079, -0.039, 0.041, -0.024, 0.075 | -0.006 | -0.004 | 2/5 |

The cloglog reframe is **well-formed and shares the kernels** (it aligns the model with the served object --
encounter *probability*), but it does **not beat the per-effort presence climatology out-of-sample** in mean
(Brier and log-loss skill both ~0, 2/5 folds positive). It buys object-alignment and calibration honesty, not
measured skill -- precisely M1 rank-3's expectation ("small, cheap; better-calibrated served probability,
possible minor skill").

### 2.3 Pooling factor (full-data fit -- an IN-SAMPLE object, reported for transparency, NOT for judging)

Centered station log-rate effects, fixed-effect vs random-intercept:

| station | events (`y>0`) | FE effect (centered) | RE effect, tau=1 | RE effect, tau=0.5 | own-data weight, tau=1 |
|---|---:|---:|---:|---:|---:|
| haro_strait | 181 | +1.246 | +1.217 | +1.142 | 0.995 |
| andrews_bay | 21 | +1.182 | +1.129 | +1.000 | 0.955 |
| orcasound_lab | 280 | -0.446 | -0.448 | -0.451 | 0.996 |
| north_san_juan_channel | 7 | -1.982 | -1.898 | -1.691 | 0.875 |

- **Variance-shrinkage pooling factor** `1 - Var(RE)/Var(FE)`: **0.073 at tau=1**, **0.241 at tau=0.5**.
- Per-station own-data weight `n_s/(n_s + 1/tau^2)` shrinks the sparsest station (`nsjc`, 7 onsets) most
  (0.875 at tau=1 -> 0.636 at tau=0.5) and the dense stations almost none -- shrinkage proportional to
  inverse information, as designed.
- Nested CV's preference for weak pooling (`tau=5`) on the dense folds is the honest read at J=4: the
  between-station SD is large relative to what 4 groups identify, so the data want little global pooling --
  *except* for the structurally-thin/absent station, where pooling is decisive (sec 2.1). The group-SD is
  weakly identified at J=4 (M1 1.1), so the half-normal prior + nested-CV selection, not a free `tau` MLE, is
  what is reported.

---

## 3. GO / NO-GO vs the +0.144 bar

**The bar (G2 / SYN sec 0):** served held-out CV mean-deviance-skill `>= +0.144` AND fold-stable (`>=4/5`
folds positive, across-fold lower bound `mean - t*SE >= +0.078`) AND PIT calibrated AND L1 null beaten ->
confidence 0.60.

**NO-GO as a standalone skill lever vs +0.144.** Every variant scores a measured mean held-out skill in
**[+0.03, +0.08]** -- the best (partial-pooling + ridge) is **+0.047**, ~3x below +0.144, with an
**across-fold 95% lower bound that is negative (~-0.05)**, so it fails the margin test AND the variance-bound
fold-stability test. Even the published served anchor (+0.078) has a lower bound of only ~+0.004 (below the
+0.078 G2 requires). Partial pooling + regularization does not, on this data, move the served number toward
+0.144 -- exactly as M1 (2.2) and SYN (sec 1) predicted: this is a *parameter-saving / variance-reducing*
lever, not a new-information lever.

**GO as the bundled fold-stability + calibration enabler (SYN A2 role).** The measured, real benefits are:
1. **Coding-invariant robustness on the thin/held-out station** -- it removes the ~0.23 fold-skill swing that
   fixed-effect reference coding produces when a sparse station is wholly held out (FE -0.077 vs RE +0.074,
   same fitter), the failure mode M1 1.1 names.
2. **Held-out PIT calibration restored** by the nested-CV kernel ridge (KS p 0.014 pooling-only -> 0.235
   pooling+ridge), the calibration precondition the bin-level timing gate and the +0.15 PIT bonus require
   (G2 sec 1B).
3. **A principled home for cross-station heterogeneity** (variance component, not free dummies), which is the
   foundation Tier B (new nodes B1/B4) needs so a new covariate's CV-skill is read against a fold-stable,
   calibrated baseline rather than a mis-specified one (SYN sec 3).

**Presence-hurdle reframe: GO as a cheap, calibrated object-alignment, NO measured skill gain.** It ties the
served forecast to encounter *probability* with zero added count parameters and stays calibrated, but does
not beat the presence climatology out-of-sample (sec 2.2). Keep NB2 the count primary; add cloglog as a
scored companion head, not a replacement.

**Net TA2 verdict: NO-GO vs +0.144 standalone; GO as the bundled regularizer + presence companion that buys
fold-stability/calibration and de-risks Tier B.** Nothing here promotes; the +0.144 jump still needs Tier B
new independent observation (SYN sec 1).

### Honest caveats (B.1 / B.3)
- **Shrinkage biases the published kernel CURVES toward flat.** Shrunk station intercepts and ridged kernels
  are *predictive objects, not unbiased shape estimates*; the `CALIBRATION_STUDIES` "publishable tuning curve"
  framing needs the M1 1.2 caveat. Judge by fold-stable held-out skill, NEVER in-sample fit or kernel shape.
- **Mixed-provenance experiment store.** These numbers come from the `haro_strait` production stream + cached
  OrcaHello index (the +0.078 experiment's provenance), not a single-provenance served store. The real judge
  is the served refit after the operator-gated 3-node ingest (G2 sec 2); the +0.144 assessment is on that.
- **Station x time confound.** Because each station's cached window differs, equal-width time-blocking
  partially confounds station with fold (andrews entirely in fold 5). This makes the FE fragility vivid and
  is the strongest argument for the random intercept, but it also means the per-fold spread overstates
  instability that a single-provenance, temporally-overlapping served store would not have. A station-stratified
  or grouped-time block scheme is a follow-up for the integrate step (does not change the GO/NO-GO).

---

## 4. PATCH-SPEC (for the later single-editor, operator-gated integrate -- NOT applied here)

Target convergence files: `modeling/estimator.py`, `modeling/fit_kernels.py` (and the CV harness is reused
as-is). This is a spec only; no edit is applied (charter sec 1; B.10).

### PATCH-1 -- partial-pooling NB random station intercept (`modeling/estimator.py`)
- Add `family`/`pooling` option `use_station_effects="partial_pool"` to `fit_glm` that replaces the
  fixed-effect station dummies with a Gaussian random intercept implemented as a ridge penalty
  `lambda_s = 1/tau^2` on station deviations (global intercept unpenalized), fit by penalized IRLS (NB2 at
  the existing Cameron-Trivedi `alpha` seed) with step-halving. Keep the FE path as the default until the
  integrate step records the swap.
- `tau` (group SD): a **weakly-informative half-normal(0, ~1) prior**, with `tau` **selected by nested CV
  inside each `block_cv` fold** over `{0.5, 1.0, 2.0, 5.0}`; J=4 weakly identifies it, so do not free-estimate
  a single `tau` (M1 1.1). Persist the selected `tau` and the variance-shrinkage pooling factor in the report.
- Expose the fit through the existing `make_fit_predict` closure so `block_cv` scores it unchanged (the
  harness is estimator-agnostic; M1 1.1). An alternative implementation is statsmodels
  `PoissonBayesMixedGLM` (random intercept + variational half-normal prior, already in the dep set) scored
  through the same closure; the penalized-IRLS NB2 path scored here is preferred because it keeps NB2 as the
  count family and needs no new dep.

### PATCH-2 -- nested-CV ridge/elastic-net on kernel coefs (`modeling/estimator.py` + fold loop)
- Add a ridge penalty `lambda_k = 1/s_k^2` on the Fourier kernel coefficients (extendable to station x kernel
  interactions and to elastic-net for selection), with `s_k` **selected by nested CV inside each outer fold**
  (`{1, 2, inf}` is sufficient on this data). Nesting is load-bearing: an un-nested CV-tuned `lambda` is
  optimistically biased at ~300 effective onsets (M1 1.2). Report the selected `s_k` per fold.

### PATCH-3 -- presence-hurdle reframe as a scored COMPANION head (`modeling/fit_kernels.py`)
- Add a cloglog GLM on `1[y>0]` with the same kernels + offset `log E` (shared linear predictor; `P(y>0) =
  1 - exp(-lambda*E)`). Score it with held-out **Brier and log-loss skill vs a per-effort presence
  climatology, reported ALONGSIDE the count deviance** in `report["presence_reframe"]`. Add the presence
  reliability/Brier to the report; keep NB2 the count primary.
- **DO NOT** add a second count process (ZI/truncated-NB). The presence reframe is the GO graduate; an
  NB->ZI/hurdle COUNT upgrade is NO-GO (SYN sec 2; DE3 #10). The patch must keep `report["presence_reframe"]`
  (GO) lexically and semantically distinct from any count-zero-process field, and must not feed the cloglog
  head into the served count intensity.

### PATCH-4 -- confidence map untouched; honesty caveats carried
- `_confidence_from_gates`, `_bin_level_timing_gate`, `ADOPT_BIN_LEVEL_TIMING_GATE`, the supervisor rule, and
  the served `data/models/fit_report.json` are **untouched** (no convergence-gate edit; B.1). The integrate
  records the shrinkage-biases-curves caveat (M1 1.2) in `KERNEL_FIT_STATUS.md`/serving disclosure.

### DE drift note (per drift-guard "carry the fix forward")
- This patch-spec implements the **presence-hurdle REFRAME** GO and explicitly forbids the **NB->ZI/hurdle
  COUNT upgrade** NO-GO. Integrator: keep the two distinct per **`DE3_strategy_drift.md` row #10** (and
  `DE2_method_drift.md`'s served-path-clean finding -- the cloglog head must remain a scored companion, never
  wired into `_station_intensity_fn` / the served count intensity).

---

## 5. Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA2_hierarchical_nb.md`.
- **Measured per-fold CV-skill (count):** served-anchor FE +0.0778 (folds -0.038/0.065/0.140/0.066/0.156,
  4/5, lower bound +0.004); partial-pooling NB +0.0438; partial-pooling + nested-CV ridge **+0.0466** (folds
  -0.123/0.068/0.143/0.070/0.074, 4/5, lower bound -0.048, **PIT calibrated p=0.235**). Presence cloglog
  reframe: Brier skill ~-0.004, log-loss skill ~-0.006 to +0.003 (2/5 folds positive) -- calibrated,
  object-aligned, no measured skill over climatology.
- **Pooling factor:** variance-shrinkage 0.073 (tau=1) / 0.241 (tau=0.5); per-station own-data weight shrinks
  the sparsest station (nsjc, 7 onsets) most. Nested CV prefers weak global pooling at J=4 but pooling is
  decisive for the structurally-held-out station (fold 5: FE -0.077 -> RE +0.074, same fitter).
- **GO/NO-GO vs +0.144:** **NO-GO** as a standalone skill lever (best mean +0.047, ~3x below +0.144, negative
  across-fold lower bound, fails fold-stability). **GO** as the bundled fold-stability + calibration enabler
  (cures FE separation/extrapolation fragility, restores held-out PIT calibration, gives a principled
  heterogeneity home) + the cheap calibrated presence companion -- the foundation that lets Tier B pay off
  without overfitting. Matches M1 ranks 1-3 and SYN A2 exactly.
- **PATCH-SPEC:** sec 4 (PATCH-1 random intercept, PATCH-2 nested-CV ridge, PATCH-3 cloglog presence
  companion kept distinct from the NO-GO ZI/hurdle count upgrade, PATCH-4 confidence map untouched) + a DE
  drift note pointing at DE3 #10 / DE2.
- **Confirmation:** nothing deployed, fetched-to-write, promoted, or committed; no convergence-file edit; no
  served write; `data/models/fit_report.json` untouched; `_maybe_write_s3` disabled and `write_outputs` writer
  path never called; mlops-gate untouched. **Effective confidence stays 0.0.**

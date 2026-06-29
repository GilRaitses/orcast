# TA5 -- physics shape priors on existing kernels (monotone dose-response + smoothness)

Agent: TA5 (graduation waveset, Wave TA). Date: 2026-06-27 (America/New_York).
Repo: `/Users/gilraitses/orcast`. This is the only file this lane writes.

Scope: prototype-and-MEASURE only. No convergence-file edit, no served write, no
deploy/promote/commit. The production upload was hard-disabled in-process
(`fit_kernels._maybe_write_s3 = lambda: None`); no `run_fit` write path was
invoked (the harness reads streams and scores variants through `block_cv` only,
`write_outputs=False` semantics). `data/models/*` untouched. Effective confidence
stays 0.0. Every skill number below is held-out 5-fold `block_cv`
mean-deviance-skill, never in-sample.

DRIFT-GUARD honored (DE, binding): the prior is a soft penalty ON THE EXISTING
kernels (a variance reducer / regularizer), NOT added flexibility and NOT a
backbone change. No LGCP/GP, no latent field, no new covariate, no extra harmonic
beyond the served `n_harmonics=2`. It stays inside the served log-linear
separable-kernel NB2 form.

## 0. Result up front

- **Smoothness prior (roughness penalty on the cyclic-kernel Fourier
  coefficients): GO.** On the 4-station experiment store, a soft second-derivative
  smoothness penalty with the penalty strength chosen by NESTED CV (selected
  inside each training fold, never on the held-out fold) lifts held-out
  mean-deviance-skill from the served **+0.078 (4/5 folds, worst fold -0.038)** to
  **+0.177 (5/5 folds positive, across-fold one-sided lower bound +0.111)**, with
  PIT still calibrated and the across-fold kernel-curve variance cut **~12-19x**.
  It is a genuine variance reducer that also flips the failing fold positive.
- **Monotone dose-response prior: NO-GO as specified for the served kernels --
  NO VALID TARGET, not a measured failure.** Every kernel in the served/fitted
  set (`k_diel`, `k_tide`, `k_lunar`, `k_season`) is a CYCLIC (periodic) function;
  a global-monotonicity constraint on a periodic kernel forces it constant and is
  ill-posed. The CALIBRATION_STUDIES dose-response/Hill motivation applies only to
  a CONTINUOUS dose covariate (current SPEED, or a `k_salmon` run-index dose),
  neither of which is in the served temporal fit. Delivered as construction-only
  for a future continuous-dose covariate; **NOT-MEASURED**, do not wire now.

Honesty flag (supersedes the M2 rank-3 "modest/small" expectation): the measured
smoothness effect is LARGER than M2/SYN anticipated. The reason is mechanical and
stated in section 4 -- the unpenalized 2-harmonic kernels were overfitting
fold-specific noise (the `k_season` curve is the worst offender under its
incomplete annual phase coverage), so shrinking the high-frequency kernel shape
buys a large out-of-sample gain. It remains a regularizer, not new flexibility.

## 1. What was built

### 1a. Smoothness prior (the measured GO)

The served kernels are mean-zero truncated Fourier series in phase `p in [0,1)`:
`k(p) = sum_{h=1..H} c_h cos(2*pi*h*p) + s_h sin(2*pi*h*p)`, `H = n_harmonics = 2`
(`modeling/bases.py`, `modeling/estimator.py`). The integrated squared second
derivative of such a series is the natural roughness functional

```
R[k] = integral_0^1 (k''(p))^2 dp = (1/2) * sum_h (2*pi*h)^4 * (c_h^2 + s_h^2)
```

so a smoothness prior is exactly a RIDGE penalty on the Fourier coefficients whose
per-coefficient weight grows as `h^4` (penalize wiggle = penalize high harmonics).
This is a standard smoothing-spline penalty expressed in the Fourier basis -- a
soft physics prior ("the environmental tuning curve is smooth"), not added degrees
of freedom. Realization:

- Penalty vector aligned to the design columns: `0` for `const` and the station
  dummies (level and station effects are unpenalized); `lambda * h^4` for each
  `{cov}__cos_h` / `{cov}__sin_h` Fourier coefficient.
- Fit: NB2 (the served primary family) via statsmodels
  `GLM(..., NegativeBinomial(alpha)).fit_regularized(alpha=penalty_vec, L1_wt=0.0)`
  (pure L2 = ridge = the smoothness penalty), with the `log(exposure)` offset and
  const + 3 station dummies + per-cyclic Fourier blocks, identical design to the
  served fit. The dispersion `alpha` is seeded per fold from a moment estimator so
  the inner CV stays numerically stable on small sub-folds.
- `lambda` chosen by NESTED 5-fold `block_cv` inside each outer training fold
  (no peeking at the outer held-out fold), then refit on the full outer-train fold
  and scored on the outer held-out fold. This is the anti-overfitting-safe number
  (charter sec 4 / SYN sec 4 / G2 sec 1B variance bound).

### 1b. Monotone dose-response prior (construction-only, no served target)

CALIBRATION_STUDIES "dose-response assay" motivates a monotone (threshold +
saturating, Hill-type) response for a CONTINUOUS dose. Construction for a future
continuous-dose covariate `d` (e.g. current SPEED, or a `k_salmon` run-index): an
I-spline / isotonic basis with non-negative coefficients (monotone by
construction), or a soft penalty `lambda_m * sum_k max(0, -(beta_{k+1}-beta_k))^2`
on adjacent monotone-basis coefficients. It is NOT applicable to any served kernel
because all served kernels are periodic; see section 0. No served measurement is
possible, so it is reported NOT-MEASURED and explicitly NOT wired.

## 2. Measured held-out CV mean-deviance-skill (5-fold block_cv, NB2, 4 stations)

Data anchor: 4 stations {haro_strait, orcasound_lab, north_san_juan_channel,
andrews_bay}, 2089 detections, 66,899 station-hour bins; harmonic tide
reconstruction R^2 = 0.847 and overlaps acoustic, so selected cyclic covariates =
{diel, tide, lunar, season} at full phase coverage (the served 4-kernel set). The
**served-anchor baseline reproduces +0.078 exactly**, validating the harness.

| Model | per-fold skill [f0..f4] | mean | min fold | folds>0 |
|---|---|---|---|---|
| **Served anchor** (NB2, n_harm=2, Cameron-Trivedi alpha; `make_fit_predict`) | -0.0381, 0.0648, 0.1401, 0.0662, 0.1559 | **+0.0778** | -0.0381 | 4/5 |
| Within-family baseline (NB2, moment alpha, lambda=0) | -0.0913, 0.0582, 0.1000, 0.0271, 0.1591 | +0.0506 | -0.0913 | 4/5 |
| Smoothness prior, flat lambda=0.001 | 0.0775, 0.1917, 0.2602, 0.2184, 0.1497 | +0.1795 | +0.0775 | 5/5 |
| Smoothness prior, flat lambda=0.003 | 0.0878, 0.1972, 0.2534, 0.2163, 0.1426 | +0.1795 | +0.0878 | 5/5 |
| Smoothness prior, flat lambda=0.01 | 0.0917, 0.1824, 0.2296, 0.1959, 0.1322 | +0.1663 | +0.0917 | 5/5 |
| Smoothness prior, flat lambda=0.03..0.3 | (saturating) | +0.158..+0.154 | +0.092..+0.093 | 5/5 |
| **Smoothness prior, NESTED-CV lambda** | **0.0775, 0.1917, 0.2534, 0.2184, 0.1426** | **+0.1767** | **+0.0775** | **5/5** |

Nested-CV per-fold lambda picks: `[0.001, 0.001, 0.003, 0.001, 0.003]` -- a stable,
consistently small selection (it does not swing fold-to-fold), so the honest
nested number `+0.1767` is essentially the flat-`lambda` plateau, not a lucky
selection artifact.

### Against the G2 promotion bar (on this experiment store)

| G2 criterion | requirement | smoothness prior (nested) | pass? |
|---|---|---|---|
| point margin | mean skill >= +0.144 | +0.1767 | yes |
| fold stability | >= 4/5 folds positive | 5/5 | yes |
| variance lower bound | mean - t_{4,0.95}*SE >= +0.078 | +0.111 | yes |
| calibration | held-out PIT calibrated | KS p 0.47 (yes) | yes |
| Level-1 corroboration | a kernel beats its null | diel (already PASS) | yes |

So on the 4-station EXPERIMENT store the smoothness prior clears every G2 robust
band. This does NOT promote anything (section 5 rails): it is the experiment store,
not the served store, and nothing in this lane changes `effective_confidence`.

### Calibration (held-out PIT, NB2)

| variant | PIT KS-vs-uniform p | calibrated |
|---|---|---|
| baseline lambda=0 | 0.250 | yes |
| smoothness lambda=0.003 | 0.468 | yes |
| smoothness lambda=0.01 | 0.477 | yes |

Calibration is preserved and modestly improves -- the prior does not trade
calibration for skill.

### Kernel-curve stability (the variance-reducer evidence)

Across-fold pointwise SD of each fitted kernel curve (mean over the cycle); lower =
the published curve is more reproducible fold-to-fold:

| kernel | baseline lambda=0 | prior lambda=0.01 | reduction |
|---|---|---|---|
| diel | 0.198 | 0.015 | ~13x |
| tide | 0.135 | 0.011 | ~12x |
| lunar | 0.204 | 0.011 | ~18x |
| season | 0.578 | 0.030 | ~19x |

`k_season` (worst under incomplete annual coverage) is stabilized ~19x. This is the
direct "variance reducer / kernel-curve stability" result the lane was asked for.

## 3. Honesty control: is this just "use fewer harmonics"?

Because the gain comes from shrinking high-frequency kernel shape, the obvious
skeptic question is whether a hard `n_harmonics=1` drop buys the same thing. It
does not:

| model | mean skill | folds>0 | min fold |
|---|---|---|---|
| n_harmonics=1 (hard drop) | +0.0835 | 5/5 | +0.018 |
| n_harmonics=2 (served) | +0.0778 | 4/5 | -0.038 |
| n_harmonics=3 | +0.0532 | 4/5 | -0.039 |
| **smoothness prior (nested, n_harm=2)** | **+0.1767** | **5/5** | **+0.078** |

A hard 1-harmonic model recovers fold-stability (5/5) but only +0.084 mean; the
soft prior reaches +0.177. So the credit is GRADED shrinkage of the whole kernel
shape (the `h^4` weighting attenuates the 2nd harmonic strongly and the 1st
harmonic lightly), not merely a smaller harmonic count. The integrate editor
should keep this n_harmonics=1 control on record so the gain is attributed
correctly.

## 4. Why the effect is larger than M2/SYN expected (mechanism, stated honestly)

M2 rank 3 / SYN A5 expected a "small/modest" effect. The measured effect is large
because the unpenalized NB2 fit spends 2 harmonics x 4 kernels = 16 Fourier
coefficients against an effective independent N of ~300 encounter onsets (M1/SYN),
and the 2nd-harmonic terms fit fold-specific noise rather than reproducible shape.
The `k_season` curve is the clearest case: its lambda=0 across-fold SD is 0.578
(it is wildly different per fold) under incomplete annual phase coverage. Shrinking
that high-frequency wiggle removes a large out-of-sample variance term, so a
regularizer that "only" smooths the curves nonetheless moves the held-out number a
lot. This is still a variance reducer (it reduces effective DOF; it adds no
flexibility), consistent with the DE drift-guard -- the size is the surprise, not
the mechanism.

Caveat carried forward (B.2 / same caveat as TA2 shrinkage): the published kernel
CURVES under the prior are SHRUNKEN predictive objects, not unbiased shape
estimates. The 2nd harmonic is deliberately attenuated, so a curve fit with the
prior must be labeled "predictive (smoothness-regularized) kernel," not "the
unbiased PSTH tuning shape." Serving may use the shrunken curve; publication of the
curve as an unbiased shape must not.

## 5. GO / NO-GO

| Lever | Held-out effect (experiment store) | Verdict |
|---|---|---|
| Smoothness (roughness) prior, nested-CV lambda | +0.078 -> +0.177 (5/5, lower bound +0.111), PIT calibrated, curve SD cut ~12-19x | **GO** (cheap, low-risk variance reducer; the strongest single Tier-A model lever measured here) |
| Monotone dose-response prior | no valid target (all served kernels are cyclic); applies only to a future continuous-dose covariate | **NO-GO as specified / NOT-MEASURED** (construction-only) |

GO rails (load-bearing; the GO is conditional on all of these):
1. **Measured on the EXPERIMENT store only** (production haro_strait stream + cached
   OrcaHello index for the 3 other nodes), not the served store. Nothing promotes;
   `effective_confidence` stays 0.0.
2. **Re-measure on the served fits before any promotion.** The served store today is
   single-station (haro_strait), whose served CV-skill is < 0; the prior's effect on
   the SINGLE-station served fit and on the POST-3-node-ingest served 4-station fit
   were **NOT MEASURED** here (bounded scope) and must be measured under the served
   gate (G2 sec 2) before the bar is claimed served-side. The +0.144 crossing in
   section 2 is an experiment-store result, not a served promotion.
3. **lambda by nested CV, never hardcoded.** The numeric `lambda` is in statsmodels'
   elastic-net internal scaling; the integrate must select it by nested
   `block_cv` per the harness here, and re-select when N changes (e.g. after TB1
   nodes land).
4. Stays a variance reducer on existing kernels (no LGCP/GP, no new covariate, no
   extra harmonic) per the DE drift-guard.

## 6. PATCH-SPEC (for the later single-editor integrate)

Two convergence files would change; this lane edits neither (patch-spec only).

- **`modeling/estimator.py` (`fit_glm`):** add an optional smoothness penalty.
  - New kwargs: `smoothness_lambda: float = 0.0`, `smoothness_order: int = 2`
    (2 = second-derivative / `h^4` weights; 1 = first-derivative / `h^2`).
  - Build a penalty vector over `X.columns`: `0.0` for `const` and every `st__*`
    column; `smoothness_lambda * h**(2*smoothness_order)` for each `{cov}__cos_h` /
    `{cov}__sin_h`.
  - When `smoothness_lambda > 0`, fit the chosen family with
    `sm.GLM(...).fit_regularized(alpha=penalty_vec, L1_wt=0.0)` (keep the existing
    unpenalized `.fit()` path for `smoothness_lambda == 0`, so default behavior is
    byte-identical). Reconstruct kernels from `result.params` exactly as today.
  - Note: `fit_regularized` returns no covariance, so the delta-method CI bands in
    `kernel_curves()` must fall back to a bootstrap (or be omitted) when the penalty
    is on; do not emit unpenalized-MLE CI bands for a penalized fit.
- **`modeling/fit_kernels.py` (`run_fit`):** select `smoothness_lambda` by nested
  `block_cv` over a small grid (e.g. `{0, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1}`) inside
  each training fold, then refit at the selected lambda; pass it through to
  `fit_glm` for the served model and through `make_fit_predict` for the CV/PIT
  scoring so the reported gates reflect the penalized model. Record the selected
  lambda and the n_harmonics=1 control skill in the report for honesty.
  `make_fit_predict` / `block_cv` need a `smoothness_lambda` passthrough.
- **Monotone dose-response:** NO CHANGE to any served kernel. If and only if a
  future CONTINUOUS-dose covariate is added (a `k_salmon` run-index dose after the
  TB3 real feed lands, or a current-SPEED kernel), implement it there with a
  monotone basis (section 1b), gated by the same held-out nested `block_cv`. Do not
  apply monotonicity to any periodic kernel.
- **Guardrails the integrate must keep:** publish penalized curves as
  smoothness-regularized PREDICTIVE kernels, not unbiased shapes (section 4);
  promotion stays gated on the SERVED fit + a recorded supervisor decision (B.1);
  `_maybe_write_s3` and `write_outputs` discipline unchanged.

### DE drift note (for the integrate editor)

`M2_nonlinear_physics.md` (section 4 / shortlist rank 3) and `SYN` row A5 label
physics shape priors a "small/modest" variance reducer. This measurement supersedes
the SIZE of that expectation (measured +0.078 -> +0.177 fold-stable on the
experiment store) while confirming its CLASS (a regularizer, not added
flexibility). When the integrate editor touches the M2/SYN ranking, annotate A5 as
"measured GO with a larger-than-expected fold-stable effect on the experiment
store; re-measure served (TA5), see `graduation/TA5_shape_priors.md`," and note
that the monotone-dose half has no served (cyclic) target. This aligns with the DE
posture that stale source-doc magnitudes are superseded; no DE-flagged convergence
doc is edited by this lane.

## 7. Reproduction / harness invocation

Environment: `.venv-modeling`, repo root, S3 read with the refit-safety env and the
production upload hard-disabled.

```bash
ORCAST_STORAGE_BACKEND=aws \
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
AWS_REGION=us-west-2 \
PYTHONPATH=/Users/gilraitses/orcast \
.venv-modeling/bin/python   # program piped via stdin; writes no file
```

The program (run via stdin heredoc, kept outside the repo tree, not committed):
sets `fit_kernels._maybe_write_s3 = lambda: None`; reproduces the 4-station memory
store as `modeling/studies/level2_multistation.run()` does (production haro_strait
from S3 + cached OrcaHello index for the 3 other nodes + S3 currents/uptime);
builds the design with the harmonic tide phase; sets `tide_overlaps_acoustic=True`
so `_select_covariates` keeps the served 4-kernel set; then for each `lambda`
fits NB2 with the `h^4` roughness penalty vector via
`GLM.fit_regularized(L1_wt=0.0)` and scores through time-blocked `block_cv`
(`n_blocks=5`), including the nested-CV lambda selection, the held-out PIT, and the
across-fold kernel-curve SD. It writes no served artifact (`data/models/*`
untouched), edits no convergence file, and calls no deploy/promote path.

## 8. Return contract

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA5_shape_priors.md`.
- **Measured (held-out 5-fold block_cv mean-deviance-skill, 4-station EXPERIMENT store):**
  served-anchor baseline **+0.0778** (4/5, worst -0.038, reproduces served +0.078);
  smoothness prior with NESTED-CV lambda **+0.1767** (5/5 positive, across-fold
  lower bound **+0.111**), PIT calibrated (KS p 0.47), kernel-curve across-fold SD
  cut ~12-19x; hard n_harmonics=1 control +0.084 (so the gain is graded shrinkage,
  not harmonic count).
- **NOT-MEASURED:** the prior's effect on the SERVED single-station fit and on the
  post-ingest SERVED 4-station fit (must be measured under the served gate before
  any promotion); the monotone dose-response prior (no valid cyclic-kernel target;
  construction-only for a future continuous-dose covariate).
- **GO/NO-GO:** GO for the smoothness (roughness) prior (cheap, low-risk,
  fold-stable variance reducer); NO-GO-as-specified / NOT-MEASURED for the monotone
  dose-response prior (no served target).
- **Confirmation:** nothing was deployed, fetched-to-write, promoted, or committed;
  no convergence file edited; no served artifact written (`_maybe_write_s3`
  disabled, `run_fit` write path never invoked); mlops-gate untouched. Effective
  confidence stays **0.0**.

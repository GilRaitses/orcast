# OS4 findings: open-tool cross-check of the landed TA2 partial-pooling NB against R-INLA / inlabru

Agent: OS4 background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc is the ONLY
file written (plus one STEP_LOG line). READ-ONLY research plus bounded reachability probes; no
convergence-file edit (`modeling/**`, `src/aws_backend/**`), no served/S3 write, no fetch-that-writes,
no ingest, no deploy, no promotion, no commit, no `git add`. Effective confidence stays 0.0; this
RECOMMENDS and SPECs only.

Hydration read in full first: `WAVESET_CHARTER.md` (section 2 OS4 row), `OS_DISPATCH.md` (OS4 source
pointers + rails), `modeling/estimator.py` (`fit_glm`, the `partial_pool` ridge, `_penalty_vector`,
`make_fit_predict`), `modeling/validation/crossval.py` (`block_cv`), the TA2 graduation doc
`graduation/TA2_hierarchical_nb.md`, and the served verdict
`integrate-promote-launch-handoff/TA2_TA3_BASELINE_VERDICT.md` (served TA2 enablers: +0.1547 mean skill,
5/5 folds, PIT 0.61).

## 0. Scope and the one honesty statement

This lane is a BENCHMARK / cross-check, not a served change. It specs how to refit the SAME served
4-station NB design in R-INLA / inlabru as a principled Bayesian partial-pooling model, compare it to the
landed statsmodels TA2, and answer one question: does the full-Bayes random intercept reproduce the
landed +0.155 fold-stable result, and does it add calibrated uncertainty the statsmodels MAP does not.
It changes no served code, adds no observation or parameter to the served model, and earns no confidence.
Every number below is cited or marked NOT-MEASURED. No fit was run in this lane (no R runtime exercised).

## 1. R-INLA + inlabru for this exact model class (characterized; licenses + reachability)

Model class to reproduce (from `modeling/estimator.py`): a per-(station) negative-binomial GLM (NB2,
`Var = mu + alpha*mu^2`), log link, with a mean-zero cyclic Fourier basis (2 harmonics x {diel, tide,
lunar, season}), a fixed observation-effort offset `log E`, and a partial-pooling random station
intercept. This is squarely the inlabru / R-INLA latent-Gaussian-model (LGM) wheelhouse: a GLM with an
`iid` random effect, an offset, and fixed covariate effects, under an NB likelihood.

Sources, licenses, reachability (MEASURED 2026-06-27 from this host):

| component | role | license | reachability |
|---|---|---|---|
| inlabru (CRAN v2.14.1) | high-level LGM/ecology front-end to INLA | GPL (>= 2) (MEASURED via CRAN DB; GitHub SPDX not auto-detected but CRAN DESCRIPTION is GPL>=2) | CRAN metadata reachable; `inlabru.org` / `inlabru-org.github.io/inlabru` docs reachable |
| R-INLA (the `INLA` package) | the integrated-nested-Laplace-approximation engine | GPL (the R-INLA package; confirm exact GPL variant at install) | `https://www.r-inla.org/` reachable (HTTP 200); **NOT on CRAN** (MEASURED: `crandb.r-pkg.org/INLA` returns HTTP 404); installs from its own repo `https://inla.r-inla-download.org/R/stable` |
| inlabru MEE paper | the citable method | journal CC/subscription | DOI `10.1111/2041-210X.13168` (Bachl, Lindgren, Borchers, Illian 2019, Methods Ecol. Evol. 10(6):760-766) |

R-runtime reachability: NOT-MEASURED. No R runtime was exercised in this lane; `.venv-modeling` is a
Python environment and INLA is an R package distributed as a binary from r-inla.org (not pip/CRAN
installable). Standing up R + INLA + inlabru is the operator gate (section 7).

Template vignette: the inlabru SVC (spatially varying coefficients) negative-binomial article on
`inlabru-org.github.io/inlabru` is the documented template for an NB likelihood with structured and
`iid` random effects in inlabru's `bru()` component syntax; for OS4 only its NB + `iid`-random-effect
mechanics are used (the spatial/SVC part is out of scope, section 4). inlabru passes `family="nbinomial"`
straight to INLA, which uses the same NB2 size parameterization (`size = 1/alpha`) the landed estimator
seeds via Cameron-Trivedi.

## 2. The exact correspondence (landed statsmodels MAP vs inlabru full posterior)

The landed `partial_pool` fit (`fit_glm(use_station_effects="partial_pool", pooling_tau=...)`) builds
all-station deviation dummies and penalizes them with a ridge
`station_lambda = 1/(pooling_tau^2 * nobs)` via `fit_regularized(alpha=penalty_vec, L1_wt=0.0)`, with the
global intercept (`const`) unpenalized. statsmodels minimizes `(1/nobs)*(-loglik) + alpha*penalty`, so
that ridge is exactly the MAP penalty `0.5*(1/tau^2)*sum_s beta_s^2` on the FULL negative log-likelihood
(the `nobs` factor restores `tau`'s group-SD meaning under the nobs-normalized objective; the estimator
docstring states this). That is the negative log-density of a Gaussian random intercept
`beta_s ~ Normal(0, tau^2)`.

Therefore:

- The landed statsmodels ridge-on-station-dummies is the MAP POINT ESTIMATE of inlabru's `iid` random
  station intercept `f(station, model="iid")`, whose `iid` precision is `tau_prec = 1/tau^2`. Same prior
  family, same shrinkage geometry (shrink each station toward the population mean with weight
  `n_s/(n_s + 1/tau^2)`), coding-invariant.
- The Fourier kernels map to INLA FIXED linear effects on the same precomputed `{cov}__cos_h` /
  `{cov}__sin_h` columns (identical basis); the landed flat kernel ridge `ridge_lambda = 1/s_k^2`
  corresponds to giving those fixed effects a Gaussian prior with that precision (INLA's default is a
  vague prior, so to match the regularized fit set the fixed-effect prior precision to `ridge_lambda`, or
  compare the unregularized-kernel variant).
- The `log E` offset enters INLA as an `offset()` (identical role).
- The NB2 likelihood is `family="nbinomial"`; the landed code plugs a Cameron-Trivedi `alpha`, while INLA
  puts a prior on the NB size hyperparameter and integrates it out.

What inlabru / INLA adds that the statsmodels MAP does not:

1. The FULL posterior, not a point estimate: calibrated marginal credible intervals on every station
   effect, on the fixed Fourier coefficients, on the NB size, and on predictions. The landed penalized
   fit explicitly SUPPRESSES delta-method CI bands (`FittedModel.penalized` -> no `cov_params`), so the
   served object has no station-effect uncertainty today; INLA supplies it.
2. It integrates over the hyperparameters `(tau, NB size)` with priors (PC-priors or gamma) instead of
   selecting `tau` by nested CV over a grid and plugging a Cameron-Trivedi `alpha`. At J=4 (weakly
   identified `tau`) this is the more principled handling of the group-SD the TA2 doc flagged.
3. Native model-selection / calibration scores: WAIC, DIC, per-observation CPO (conditional predictive
   ordinate, a leave-one-out predictive density) and INLA PIT, computed in one fit. CPO/WAIC give an
   independent read on whether the +0.155 result is corroborated.

## 3. Honest cross-check plan (a benchmark; reuses the existing folds; changes nothing served)

Goal: does the principled Bayesian partial-pooling reproduce the landed served +0.1547 (5/5 folds, PIT
0.61), and does it add calibrated intervals the statsmodels MAP lacks. Run OFFLINE in R (operator-gated,
section 7), read-only against the same served 4-station design; no served write, no convergence edit.

1. Build the identical design. Export the served 4-station design matrix (`modeling/design.py`
   `build_design`, 1 h bins: `y`, `exposure`, the `{cov}__cos/sin` Fourier columns, `station`) to a
   read-only scratch CSV. Do NOT rebuild covariates in R; reuse the exact columns so the only difference
   is the fitter.
2. Fit inlabru. `bru(y ~ Intercept + f(station, model="iid", hyper=<PC-prior on precision>) +
   diel__cos_1 + ... + season__sin_2, family="nbinomial", E=exposure / offset=log(exposure),
   data=design)`. Mirror the served selection: either fix the `iid` precision to the served full-data
   `tau=1.0` for the closest MAP-to-posterior comparison, or use a PC-prior and let INLA integrate `tau`
   (the principled variant); report both.
3. Compare on four axes, all against the landed statsmodels TA2:
   (a) Station-effect shrinkage: posterior-mean station deviations vs the landed `station_effects` and
       the TA2 variance-shrinkage pooling factor (TA2 reported 0.073 at tau=1, and the fold-5 held-out
       station shrinking to the population mean). Expect close agreement of posterior mean with the MAP.
   (b) Held-out CV mean-deviance-skill: reuse the SAME `assign_time_blocks` 5-fold split; for each fold
       fit inlabru on train, take the posterior-mean rate on test (`exp(linear predictor) * exposure`),
       and score with the SAME `poisson_deviance` vs the SAME per-effort climatology baseline as
       `block_cv`, so the number is directly comparable to the served +0.1547 and its 5/5 folds.
   (c) PIT / calibration: compare INLA PIT (and a held-out randomized NB PIT computed the repo way) to
       the served PIT KS p = 0.61.
   (d) CPO / WAIC corroboration: report INLA CPO log-score and WAIC; check they rank the partial-pool +
       Fourier model above the FE baseline consistently with the served +0.078 (FE) -> +0.155 (TA2)
       deviance-skill gap.
4. Verdict rule for the benchmark: inlabru CORROBORATES if (b) reproduces a mean held-out skill close to
   +0.155 with 5/5 (or 4/5) folds positive and (c) calibration holds; it ADDS VALUE if (a) the posterior
   gives calibrated station-effect intervals and (d) CPO/WAIC independently favor the partial-pool model.

Reasoned expectation (NOT-MEASURED, no fit run): because the landed ridge IS the MAP of the inlabru
`iid` prior, the posterior MEAN and the statsmodels MAP point predictions should be very close, so
inlabru is expected to REPRODUCE the +0.155 closely (small differences from integrating `tau` and the NB
size rather than plugging them). The genuine value-add is calibrated uncertainty (station-effect and
predictive credible intervals the penalized statsmodels fit cannot emit) plus WAIC/CPO, NOT a higher
skill. This is a validation/uncertainty-quantification cross-check, not a +0.144 lever; it earns no
confidence and changes nothing served.

## 4. The SYN dead-end stays a dead-end: no LGCP / SPDE at current N

Spatial LGCP / SPDE (inlabru's headline capability, the SVC/spatial mesh path) is NOT in scope and stays
the SYN dead-end at the current N. The served set is four stations in one roughly 8 by 9 km cluster, all
facing the same Haro Strait lane (S1 / TA3); there is no spatial leverage for a continuous spatial field
or a distance-decaying SPDE at four clustered points, and fitting an SPDE/LGCP mesh over them would
invent spatial structure the geometry cannot identify (and would risk laundering a detector artifact into
a spatial effect). The `iid` station random effect (this lane) is the correct latent structure at N=4;
the SPDE/LGCP path is reserved for AFTER TB1 (Admiralty Inlet), TB4 (Boundary Pass), and OS2
(Tekteksen/SIMRES, CarmanahPt) add spatially SEPARATED nodes, at which point a spatial field becomes
identifiable. This lane does not propose LGCP at current N.

## 5. Integration note (no convergence edit; benchmark only)

There is no served PATCH-SPEC here: the cross-check is an offline benchmark, not a served swap. If the
benchmark corroborates (it is expected to), the only optional, separately-gated follow-on is a DISCLOSURE
improvement, surfacing INLA-derived calibrated station-effect credible intervals alongside the served
forecast (this composes with the OS3 EFI parameter-uncertainty field, which the statsmodels penalized fit
currently leaves qualitative). That is an additive disclosure, not a change to `fit_glm`,
`_confidence_from_gates`, the +0.144 bar, or the served intensity. The served estimator stays statsmodels
(no R in the serving path); inlabru is a benchmark/QA tool, run offline.

## 6. DE drift note

None required. This doc specs an offline benchmark and characterizes external tools; it touches no
DE-flagged prose doc (`M2_nonlinear_physics.md`, `wave_shape.yml` objectives, `ORCHESTRATOR_NOTES.md`,
the wildlife register). It is consistent with the TA2 verdict and `SYNTHESIS_signal_modeling.md`: the
partial-pool random intercept is the principled form (this lane cross-checks it), and spatial LGCP at the
current clustered N remains the SYN dead-end (section 4). No stale GO is superseded; the +0.144 bar and
the confidence map are explicitly unchanged.

## 7. Operator gate

The cross-check needs an R runtime with R-INLA installed from `https://inla.r-inla-download.org/R/stable`
(INLA is not on CRAN; MEASURED HTTP 404) plus inlabru from CRAN (GPL >= 2). R-runtime + INLA install
reachability from this environment is NOT-MEASURED (no R exercised here, and `.venv-modeling` is Python).
This is the single operator gate: stand up R + INLA + inlabru offline, then run the section-3 benchmark.

## 8. Return summary

- Doc path: `.cca/catalogue/O0/20260627_open-science-integration/OS4_inlabru_crosscheck.md`.
- Correspondence (MEASURED from the code): the landed `fit_glm(use_station_effects="partial_pool")` ridge
  `1/(tau^2*nobs)` on station-deviation dummies (global intercept unpenalized) is exactly the MAP point
  estimate of inlabru's `f(station, model="iid")` Gaussian random intercept with precision `1/tau^2`;
  inlabru additionally integrates the hyperparameters with priors and returns the full posterior
  (calibrated station-effect and predictive intervals) plus WAIC / CPO / PIT.
- OS4 GO/NO-GO: **GO (spec/benchmark, operator-gated on an R runtime) on running the inlabru `iid`-random-
  intercept NB cross-check against the landed statsmodels TA2 (same design, same `block_cv` folds, same
  deviance-skill metric, plus CPO/WAIC), as a validation + calibrated-uncertainty benchmark; NO-GO on any
  served swap or skill credit (it is expected to reproduce, not beat, the +0.155, and earns no
  confidence). LGCP/SPDE at the current 4-clustered-station N stays a NO-GO dead-end until spatially
  separated nodes (TB1/TB4/OS2) land.**
- Single highest-value next action: stand up R + R-INLA (from r-inla.org) + inlabru offline and run the
  section-3 benchmark axis (b) first (reuse the `block_cv` folds and the `poisson_deviance` metric) to
  confirm inlabru reproduces the served +0.155, then read its CPO/WAIC and calibrated station-effect
  intervals as the value-add.
- Operator gate hit: R runtime + R-INLA install (INLA is not on CRAN; installs from r-inla.org, reachable
  HTTP 200; R-runtime reachability from this Python environment NOT-MEASURED). inlabru is CRAN GPL (>= 2).
- Confirmation: nothing edited in `modeling/**` or `src/aws_backend/**`, nothing fetched-to-write,
  ingested, deployed, promoted, or committed; no fit run (no R exercised); external tools probed
  read-only; only this one findings doc plus a STEP_LOG line written; the served estimator, the +0.144
  bar, and `_confidence_from_gates` untouched; effective confidence 0.0.

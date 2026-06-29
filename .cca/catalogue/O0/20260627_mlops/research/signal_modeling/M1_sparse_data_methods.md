# M1 -- sparse-data modeling methods (W10, signal & modeling research)

Agent: research subagent W10-M1, forecast ML-ops "signal & modeling research" campaign.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. READ-ONLY except this one doc.
Home: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/M1_sparse_data_methods.md`.
Authority: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B; `SIGNAL_MODELING_CHARTER.md` (esp. sec 4
anti-overfitting); `SIGNAL_MODELING_DISPATCH.md` (the M1 brief); `research/forward/G2_promotion_protocol.md`
(the +0.144 bar). Nothing here deploys, promotes, refits-to-write, or commits. Effective confidence stays 0.0.

## 0. Hydration + what I read

- `HANDOFF_CHARTER.md` section B (locked): B.1 honesty/promotion gate, B.2 effort-bias covariate roles,
  B.3 withhold-over-fake, B.6 local-only `modeling/` tree, B.10 no agent commits.
- `SIGNAL_MODELING_CHARTER.md` (sec 4 anti-overfitting is load-bearing) + `SIGNAL_MODELING_DISPATCH.md` (M1).
- `research/forward/G2_promotion_protocol.md`: the verified P0 confidence map and the +0.144 promotion bar.
- `docs/methodology/FORECAST_KERNELS.md` + `CALIBRATION_STUDIES.md`: model form (log-linear separable LNP/GLM
  with Fourier kernels, `log E` offset), the leveled gate plan, time-rescaling GOF framing.
- `research/L2_burstiness_timing.md`: the burstiness finding; Hawkes branching 0.79-0.96 already prototyped.
- Pipeline code that bounds feasibility: `modeling/estimator.py` (statsmodels NB2/Poisson GLM, Fourier basis,
  station fixed effects, cluster-robust SEs), `modeling/validation/crossval.py` (time-blocked 5-fold CV,
  climatology baseline, deviance skill, binomial pass gate).
- Web literature (cited inline per method).

### 0.1 The frontier, stated honestly (the bar every method must clear)

The served 4-station fit is held-out CV mean-deviance-skill **+0.078 (4/5 folds) -> confidence 0.49 HOLD**.
Promotion needs served skill **~+0.144** (the verified 0.6-crossing in G2; ~1.85x the experiment) AND
fold-stable (>=4/5 folds individually positive, across-fold lower bound `mean - t*SE >= +0.078`) AND PIT
calibrated AND a beaten Level-1 null. The W6 ingest added **0 new observations** to the analysis universe, so
the same cached data cannot move the number; "more signal per observation" must come from the model itself.

The judge is `block_cv` in `modeling/validation/crossval.py`: held-out Poisson deviance skill vs a per-effort
climatology, time-blocked (whole stretches held out), gated by a binomial pass-rate test. **No method earns
anything here on in-sample fit or added flexibility.** Charter sec 4: a flexible method that cannot show
out-of-sample, fold-stable gains at our N is a dead-end, said so plainly.

### 0.2 The effective-N reality (the load-bearing number)

N is not 2089. The stream is bursty: 63-91% of detections fall within 6 min of the prior, and the prototyped
Hawkes branching ratios are 0.79-0.96, i.e. 79-96% of events are self-excited repeat-triggers on a single
acoustic encounter, not independent presence events. An illustrative sanity check (stdout only, no writes):

| quantity | value |
|---|---|
| pooled detections (4 stations) | 2089 |
| raw hourly occupancy (events / 66,899 bins) | 0.031 (sparse, ~97% zero bins) |
| effective independent onsets, branching 0.79 / 0.85 / 0.96 | ~439 / ~313 / ~84 |
| per-station effective independent onsets @0.85 (haro/orcasound/andrews/nsjc) | ~114 / ~154 / ~40 / ~5 |

So the data that actually constrains kernel *shape* is on the order of **~300 independent encounter onsets
pooled**, and as few as **~5-150 per station**. This is the number to compare every method's data-volume
requirement against, and it is why the confidence map "saturates quickly": there is very little independent
information to spend, and any method that buys skill by adding effective parameters will overfit it back.

The current served model already uses 2 harmonics x 4 cyclic kernels (16 shape params) + intercept + 3 station
dummies ~= 20 effective parameters against ~300 effective independent onsets. That is already a tight
parameter budget; methods are scored below largely on whether they *spend* or *save* effective parameters.

---

## 1. Method-by-method assessment

For each: what it buys on sparse bursty data; held-out / calibration evidence from the literature; data-volume
requirement; feasibility in the existing `modeling/` pipeline; honest over-fitting risk at our N; verdict.

### 1.1 Hierarchical / partial-pooling Bayesian count models (station random effects + shrinkage)

- **What it buys.** Replaces the current fixed-effect station dummies with a random-intercept (and optionally
  random-slope / partially-pooled kernel) hierarchy. Partial pooling shrinks sparse stations toward the
  population mean by sample size: andrews_bay (eff ~40) and especially north_san_juan_channel (eff ~5) stop
  contributing noisy free parameters and instead borrow strength from haro/orcasound. This is *parameter
  saving*, the opposite of added flexibility, which is exactly what charter sec 4 rewards. It directly targets
  the recorded cross-station heterogeneity (PSTH corr 0.14-0.34; G2: lunar within-station reproducible but
  cross-station divergent) by modeling the heterogeneity as a variance component instead of either ignoring it
  (complete pooling) or over-fitting it (no pooling).
- **Held-out / calibration evidence.** Strong and consistent. The PyMC radon multilevel primer and the Stan
  pool-binary-trials case study show partial pooling gives "objectively more reasonable" estimates precisely
  for *small-sample groups*, with shrinkage proportional to inverse sample size. Bayesian multi-region cell-count
  work (eLife 102391, under-sampled: fewer animals than regions) reports the partially-pooled model
  out-predicting per-group t-tests and giving better-calibrated (narrower, honestly-covered) intervals on
  under-sampled count data. SmallML (arXiv 2511.14049) frames it as raising *effective* sample size by sharing
  across entities while respecting heterogeneity. The gain is largest exactly in our regime (a few groups, some
  very sparse).
- **Data-volume requirement.** Low and well-matched: hierarchical models are the canonical tool *for* small,
  unbalanced grouped data. 4 stations is a small number of groups for estimating a between-station variance
  (the variance component itself is weakly identified at J=4), so use a weakly-informative half-normal prior on
  the group SD and do not over-interpret it -- but the per-station intercept shrinkage still works at J=4.
- **Feasibility in `modeling/`.** Moderate. The estimator is statsmodels GLM with fixed-effect dummies
  (`estimator.py` `use_station_effects`); the docstring already flags "a GLMM random-intercept is a documented
  follow-up." Two feasible paths: (a) `statsmodels` `PoissonBayesMixedGLM` / `BinomialBayesMixedGLM` (variational,
  in the existing dep set, no new heavy dep); (b) a small PyMC/`bambi` NB random-effects fit run offline under a
  scratch env, scored through the *same* `block_cv` harness via a `fit_predict` closure. The CV harness is
  estimator-agnostic (`make_fit_predict` pattern), so a hierarchical fit drops in without touching the gate.
- **Over-fitting risk at our N.** Low -- this is a regularizer, not a flexibility add. The only risk is a
  poorly-chosen group-SD prior at J=4 letting the hierarchy collapse to no-pooling (reintroducing the noisy
  sparse-station params); mitigated by a weakly-informative prior and reporting the pooling factor.
- **Verdict: GO (top candidate).** Most likely of all surveyed methods to add fold-stable held-out skill at our
  N because it *reduces* effective parameters where the data is thinnest (nsjc eff ~5, andrews eff ~40) while
  keeping the dense stations near their own estimates. Prototype as a random-intercept (then random-kernel) NB,
  scored through `block_cv`.

### 1.2 Regularization (ridge / lasso / elastic-net on the GLM coefficients)

- **What it buys.** Penalizes the Fourier kernel coefficients (and station/interaction terms) toward zero,
  trading a little bias for variance reduction -- the standard small-N bias/variance lever. Lets us *propose*
  richer structure (more harmonics, station-by-kernel interactions, M3's derived covariates) without paying the
  full variance cost, because CV-tuned shrinkage prunes what the held-out data will not support. Ridge stabilizes
  correlated covariates (diel/tide/season collinearity, flagged in FORECAST_KERNELS sec on confounding); lasso/
  elastic-net additionally does covariate selection.
- **Held-out / calibration evidence.** The bias-variance payoff of CV-tuned shrinkage on out-of-sample error is
  textbook and directly demonstrated for Poisson GLMs in `glmnet` (`family="poisson"`, `offset` for effort,
  `cv.glmnet` minimizing held-out deviance). For *sparse data with collinearity* specifically, the Thai Stat
  simulation+real-data study found ridge best under multicollinearity and adaptive-lasso best overall for
  high-dimensional sparse Poisson, judged by out-of-sample MSE -- i.e. the gain is real but modest and is a
  variance-reduction gain, not new signal.
- **Data-volume requirement.** Very low; regularization is *most* valuable at small N. The penalty path is cheap
  to CV-tune.
- **Feasibility in `modeling/`.** Moderate. statsmodels `fit_regularized` (elastic-net) exists for GLM but is
  less ergonomic than R `glmnet`; cleaner is a thin scikit-learn `PoissonRegressor` (L2) / Poisson GBM-free
  `ElasticNet`-style path, or a direct penalized-IRLS, wrapped as a `fit_predict` closure into `block_cv`. The
  effort offset must enter as `log E` (supported). Honesty note: shrinkage biases the published kernel *curves*
  toward flat, so the CI bands and the "publishable tuning curve" framing in CALIBRATION_STUDIES need a caveat;
  shrunk kernels are predictive objects, not unbiased shape estimates.
- **Over-fitting risk at our N.** Low for the shrinkage itself; the *real* risk is using regularization as a
  license to add many candidate covariates/interactions and trusting CV at our small effective-N to prune them.
  With ~300 effective independent onsets and 5 folds, the CV-selected lambda is itself high-variance; nest the
  lambda selection inside each CV fold (nested CV) or the held-out skill is optimistically biased.
- **Verdict: GO (as an enabler, not a standalone win).** Best value as the regularizer that lets the
  hierarchical model (1.1) and the M3 derived covariates be proposed safely. As a standalone change to the
  current 20-parameter model it is likely a small (single-digit-percent-of-deviance) variance gain, not a path to
  +0.144 by itself. Graduate it bundled with 1.1, with nested-CV lambda selection.

### 1.3 Hurdle / zero-inflated / negative-binomial (NB already in use)

- **What it buys.** NB2 (already the primary in `estimator.py`) absorbs count overdispersion (fitted alpha=88.1,
  Poisson Pearson dispersion 8.69). Hurdle/ZI models add a separate zero process: a hurdle model splits
  "any presence in the bin" (Bernoulli) from "how many given presence" (truncated NB), which maps cleanly onto
  the bursty structure (onset vs within-bout repeats) and onto the served target (per-bin *presence*).
- **Held-out / calibration evidence.** Mixed-to-negative on the *upgrade* question, which is the honest headline.
  NB is already established here as calibrated (held-out NB PIT p=0.364 vs Poisson p=1.4e-15 in
  `L2_burstiness_timing`). For ZI-vs-NB specifically: the telemedicine trial study (UTHealth) found "a ZINB
  model does not necessarily outperform an NB model ... even when data were simulated from an underlying ZINB,
  the NB model had very similar or smaller relative bias and MSE." The ZI/hurdle comparison literature (PMC8570364)
  finds the two largely indistinguishable on GOF and inconsistent about which wins. The cyanobacteria Bayesian-ZI
  work shows ZI/hurdle help when zeros are *structural and excess beyond NB* -- our zeros are sparse-but-
  overdispersion-explained, which NB already covers.
- **Data-volume requirement.** Hurdle/ZI add a whole second linear predictor (doubling the parameter budget for
  the zero/onset process). That is meaningful at ~300 effective onsets; the truncated-count part is fit on only
  the non-zero bins (a small fraction of 66,899), so its kernels are estimated on little data.
- **Feasibility in `modeling/`.** NB: already done. Hurdle: statsmodels has `HurdleCountModel` and
  `ZeroInflatedNegativeBinomialP`; both are wireable as a `fit_predict` closure, but the deviance-skill metric
  in `block_cv` is Poisson-deviance based, so scoring a hurdle fit fairly needs the predicted mean `mu` (the
  harness already consumes `mu`, so it works) and ideally a presence-Brier/log-loss companion metric.
- **Over-fitting risk at our N.** Moderate-to-high for the *upgrade*: the second linear predictor doubles
  effective parameters for a zero process that NB's variance function already largely explains, so expect
  in-sample improvement that does not survive `block_cv`.
- **Verdict: NO-GO as an NB->ZI/hurdle upgrade** (literature says the upgrade rarely earns out-of-sample at our
  regime; it spends parameters NB already covers). **GO (small, cheap) for one framing variant only:** a
  *presence hurdle as the served target* -- i.e. model per-bin presence probability directly (Bernoulli/
  complementary-log-log with the same kernels + `log E`) and score it with a proper presence score (Brier/
  log-loss) alongside the count deviance. This aligns the model with the served forecast object (encounter
  *probability*) without adding a count process, and is a near-zero-cost reframe of existing kernels. Keep NB2
  as the count primary.

### 1.4 Penalized splines / GAMs (cyclic smooths instead of fixed-harmonic Fourier)

- **What it buys.** Replaces the fixed 2-harmonic Fourier kernels with penalized cyclic regression splines whose
  wiggliness is chosen by the data (REML), so a kernel can be flatter or sharper than 2 harmonics allow without
  the analyst hand-picking harmonic count. The penalty + effective-degrees-of-freedom (EDF) machinery is a
  principled flexibility controller.
- **Held-out / calibration evidence.** Well-established (Wood/mgcv). Key small-N caveats from the literature:
  GCV "undersmooths" and is unstable on small data; **REML is the recommended smoothness selector for small
  samples** (Seascapemodels, Wood). The basis dimension `k` should be set generously and the *penalty* (not `k`)
  controls EDF; on small data the penalty typically drives EDF *down*, often toward the linear/low-harmonic
  solution -- i.e. on our data a penalized GAM will likely shrink toward roughly the 2-harmonic kernel we already
  fit. "Small" in this context is "100s to 1000s of samples"; our effective ~300 onsets is squarely small.
- **Data-volume requirement.** The mgcv rule of thumb is basis dimension >= ~4x the EDF you expect; at our N you
  can only honestly afford low EDF (2-4) per kernel, which is essentially what the current Fourier basis already
  provides.
- **Feasibility in `modeling/`.** Moderate. `pyGAM` (Poisson GAM with penalized splines) is the natural Python
  fit, wireable through `block_cv`; the current Fourier basis is already a (fixed-EDF) special case, so this is an
  apples-to-apples swap. REML smoothness selection is less turnkey in `pyGAM` than in R mgcv.
- **Over-fitting risk at our N.** Low *if* REML/penalty is used (it self-regularizes toward the current fit);
  moderate if GCV or a fixed large `k` is used (undersmoothing / wiggle artifacts on the sparse stations,
  exactly the noise the cross-station consistency study already sees).
- **Verdict: NO-GO as a near-term skill lever** (it will most likely reproduce the current 2-harmonic kernels
  because the penalty has little data to justify more EDF -- no new signal, just a more defensible
  smoothness-selection story). **Optional WEAK-GO** only if bundled as the *flexibility container* for the
  hierarchical/regularized model and reported as a robustness check, not a skill claim.

### 1.5 Hawkes / self-exciting processes (already prototyped)

- **What it buys.** A conditional intensity `lambda*(t)=mu(t)+sum alpha*beta*exp(-beta(t-t_i))` that models the
  self-excitation directly -- the textbook GOF for a clustered stream (Brown et al. 2002).
- **Held-out / calibration evidence (ours, already measured).** `L2_burstiness_timing.md`: single-exp Hawkes cuts
  the pooled event-level time-rescaling KS from 0.773 to 0.134 and the near-zero IEI spike from 81.6% to 0.14%,
  recentering the mean to 1.002 -- but pooled KS p stays 3.3e-33 (residual is heavier-tailed/Omori-like, not
  exponential-memory). Only the sparsest station (nsjc, n=34) "passes" at low power. Branching 0.79-0.96 says the
  excitation is detector repeat-triggering on one encounter, **not animal signal**.
- **Data-volume requirement.** N/A for new graduation -- already explored on the existing data.
- **Feasibility in `modeling/`.** The prototype exists (`/tmp/rd_burstiness_prototype.py`, `fit_hawkes1`); the
  wiring spec (`L2_burstiness_timing` sec 4) deliberately keeps the Hawkes term **out of `_station_intensity_fn`**
  (served intensity stays the smooth bin-rate) and uses it only as an event-level *diagnostic*.
- **Over-fitting risk at our N.** As a *served covariate*, high and dishonest: it would encode a detector
  artifact as if it were presence (B.2 violation). As a diagnostic, none.
- **Verdict: NO-GO as a served-skill method (already adjudicated).** It does not pass event-level Exp(1) and must
  not enter the served intensity. Its only graduated role is the already-specified event-level GOF *diagnostic*
  plus justification for the bin-level timing gate -- an operator-gated gate-definition decision, not a skill
  lever. No new prototype.

### 1.6 Log-Gaussian Cox Processes (LGCP)

- **What it buys.** A latent Gaussian random field on log-intensity captures *residual* spatial/temporal
  autocorrelation the parametric kernels miss -- "smooth structure we did not name." For us the natural use is a
  spatial `s_space` field over the 4 stations (or a continuous spatio-temporal field), feeding Level 3-4.
- **Held-out / calibration evidence.** LGCP/INLA-SPDE is the standard for spatial point patterns and predicts
  well *when there is spatial data to constrain the field*. The decisive small-N caveat (PMC10062232, INLA-SPDE):
  with sparse/under-sampled point patterns the posterior field reverts to the prior away from data, the range
  parameter becomes weakly identified (interval widens ~2x and shifts), and "the LGCP simply cannot predict
  detail in regions far from the observed sections." The SDM evaluation study (s40808-024-02017-z) shows
  Poisson-PP and LGCP can reach AUC>70% on *simulated dense* presence-only data but degrade sharply with coarse
  resolution and imperfect detection -- both of which describe our 4-point, detector-biased setup.
- **Data-volume requirement.** High *in the spatial dimension*: 4 station locations cannot identify a spatial
  correlation range. A purely *temporal* LGCP (GP on log-rate over time) is the only honest variant at our N, and
  that overlaps method 1.7.
- **Feasibility in `modeling/`.** Low. LGCP needs R-INLA/SPDE or a GP stack and a mesh; it is a major dep and
  modeling-form change away from the statsmodels GLM, and the serving schema (`serve.py`) expects parametric
  kernel coefficients, not a latent field.
- **Over-fitting risk at our N.** The spatial field is unidentified at 4 points; it would either revert to prior
  (no gain) or fit station-level noise (overfit). High risk for no expected held-out payoff.
- **Verdict: NO-GO.** Right tool, wrong N in the spatial dimension; revisit only after S1 grounds many more
  in-region nodes (then a spatial LGCP/SPDE becomes worth re-scoring). The temporal-only variant collapses into
  1.7 and is judged there.

### 1.7 GP-modulated intensity (Gaussian-Cox / GP on log-rate, temporal)

- **What it buys.** A nonparametric GP prior on the temporal log-intensity -- maximally flexible kernel shapes
  and automatic, regularity-adaptive smoothing (the length-scale is learned), with full predictive uncertainty.
- **Held-out / calibration evidence.** VBPP (Lloyd et al. 2015) reports more accurate held-out prediction than
  benchmarks on coal-mining and Kenya-malaria point data; Kirichenko-van Zanten (JMLR 2015) prove GP intensity
  learning is minimax-*rate-optimal* and regularity-adaptive -- the theoretical best you can do nonparametrically.
  The universal caveat across this literature: avoiding over/under-fit hinges entirely on hyperparameter
  (length-scale) selection, and sparse approximations / inducing points are used as much for *regularization* as
  for speed.
- **Data-volume requirement.** Moderate-high for the *flexibility to pay off*; at small effective-N the GP
  posterior reverts to its mean/prior between data and the learned length-scale is high-variance. With ~300
  effective onsets the GP will, if honestly regularized, reproduce a smooth low-frequency curve -- i.e. roughly
  the existing low-harmonic kernel -- and add little the Fourier basis does not.
- **Feasibility in `modeling/`.** Low-moderate. Needs GPy/GPflow/PyMC GP, a new dep and a non-GLM fit; scoring
  through `block_cv` is possible via a `fit_predict` closure but the serving schema does not hold a GP.
- **Over-fitting risk at our N.** Moderate-high: the value proposition is flexibility, and charter sec 4 warns
  exactly against flexibility that cannot show fold-stable gains. A GP with a short learned length-scale would
  fit burst noise; forced long, it equals the current kernel.
- **Verdict: NO-GO at our N** (flexibility we cannot afford; expected to converge to the current kernel under
  honest regularization, with much higher engineering cost and no serving path). Reconsider only with far more
  independent observation (S1 nodes / years of accumulation).

### 1.8 Principled data augmentation

- **What it buys.** Synthetic expansion of the training set to reduce variance / overfitting -- attractive given
  small N.
- **Held-out / calibration evidence.** Genuinely double-edged in exactly our regime. Positive: VAE/WGAN-GP
  augmentation cut day-ahead-price MAE ~2-3% (TU/e), and frequency-domain FrAug + synthetic-data forecasting
  studies (arXiv 2605.06032) show low-resource gains -- *but every one of these is continuous time series with
  abundant temporal structure, not a sparse bursty count point-process*. Negative/limits: augmentation can
  *underfit* or *degrade* accuracy if the augmentation distribution `Q` drifts from the data `P` (the
  distribution-shift penalty scales with the synthetic ratio), and the synthetic-data verification literature is
  explicit that synthetic rows must be train-only, leakage-checked, and never span CV splits.
- **Data-volume requirement.** It does not create independent information; at best it encodes a prior as fake
  data. For a point process, any honest augmentation (e.g. simulating from a fitted Hawkes/NB) just re-expresses
  the model we are already fitting -- it cannot manufacture the independent onsets (effective ~300) we lack.
- **Feasibility in `modeling/`.** A generator is buildable, but `block_cv` is time-blocked specifically to
  prevent leakage; injecting synthetic spikes into training folds risks leaking the held-out block's structure
  and *inflating* the very metric the campaign trusts. That is an anti-overfitting hazard, not a help.
- **Over-fitting risk at our N.** High and insidious: the most likely outcome is an optimistic CV number that is
  an artifact of synthetic-to-real correlation, directly threatening the +0.144 bar's integrity (B.1/B.3).
- **Verdict: NO-GO.** The one principled, non-deceptive use is *informative priors* (encode domain knowledge as a
  prior in the hierarchical model 1.1) rather than fabricated rows -- and that is already counted under 1.1/1.2,
  not as augmentation. Treat synthetic-row augmentation as withheld (B.3).

---

## 2. Shortlist -- ranked by expected held-out payoff at our N

Ranked by expected *fold-stable* held-out CV-skill contribution at ~300 effective independent onsets, judged by
`block_cv`, never by in-sample fit.

| rank | method | what it buys at our N | data-volume need | expected held-out payoff | GO / NO-GO |
|---|---|---|---|---|---|
| 1 | **Hierarchical / partial-pooling NB** (random station intercept -> random kernels) | shrinks noisy sparse stations (nsjc eff ~5, andrews ~40) toward population; models the measured cross-station heterogeneity as variance, not free params | low; ideal for few unbalanced groups (caveat: J=4 weakly identifies the group SD -> weak prior) | **highest of the set**; *saves* parameters where data is thinnest -> most plausible fold-stable lift toward +0.144 | **GO** (prototype first) |
| 2 | **Regularization (ridge / elastic-net, nested-CV lambda)** | variance reduction on kernel + station + interaction coefs; safely enables #1 and M3 covariates | very low; most valuable at small N | modest standalone (single-digit % deviance), multiplicative when bundled with #1 | **GO** (bundle with #1) |
| 3 | **Presence-hurdle reframe of the served target** (Bernoulli/cloglog on per-bin presence, same kernels + log E, Brier/log-loss companion) | aligns the model with the served object (encounter *probability*) at ~zero added parameters | low (reuses existing kernels) | small, cheap; better-calibrated served probability, possible minor skill | **GO** (cheap, do alongside #1) |
| 4 | **Penalized-spline / GAM kernels (REML)** | principled smoothness selection; defensible robustness check | low EDF only affordable | ~neutral; expected to reproduce current 2-harmonic kernels | **WEAK-GO** as robustness container only; **NO-GO** as a standalone skill lever |
| 5 | **NB -> ZI / full hurdle count upgrade** | adds a second zero/onset linear predictor | doubles param budget; truncated part on few non-zero bins | literature: rarely beats NB out-of-sample at our regime | **NO-GO** |
| 6 | **GP-modulated intensity (temporal)** | nonparametric flexible kernel + uncertainty | moderate-high to pay off; reverts to prior at our N | converges to current kernel under honest reg; flexibility we cannot afford | **NO-GO** at our N |
| 7 | **Log-Gaussian Cox Process (spatial)** | latent field for residual spatial autocorrelation | high *spatially*; 4 points cannot identify a range | unidentified field -> no gain or station-noise overfit | **NO-GO** (revisit after S1 nodes) |
| 8 | **Hawkes / self-exciting** (already prototyped) | correct event-level GOF; explains the timing failure | already explored | fails Exp(1); detector artifact if served (B.2) | **NO-GO** as skill; keep as the adjudicated GOF diagnostic |
| 9 | **Synthetic data augmentation** | fake training rows to cut variance | creates no independent info; leakage hazard in time-blocked CV | high risk of an optimistic, artifactual CV number | **NO-GO** (withhold, B.3) |

### 2.1 The single highest-value prototype to graduate

**A hierarchical (partial-pooling) negative-binomial fit with CV-tuned shrinkage**, scored through the existing
`block_cv` harness against the +0.144 bar with per-fold skills reported. It is the only surveyed method whose
mechanism (reducing effective parameters where the data is thinnest) is aligned with charter sec 4 rather than
fighting it, and it is the only one with consistent small-N held-out evidence in the literature. Graduate it
*bundled* with regularization (#2) and the presence-reframe (#3); everything else is a dead-end at our N or an
already-adjudicated diagnostic.

### 2.2 Honest expectation (anti-overfitting)

Even the GO methods are *parameter-saving / variance-reducing* levers, not new-information levers. The W6 finding
stands: the analysis universe has 0 net-new observations, and effective independent onsets are ~300 pooled. The
literature's own small-N message (SDM minimum-sample studies; LGCP/GP reversion-to-prior; ZINB-not-beating-NB) is
that at this N the *model* can buy fold-stability and calibration honesty, but the path to a *large* skill jump
(+0.078 -> +0.144) most likely requires **new independent observation (W9/S1 nodes, S2 covariates)**, not more
model flexibility. M1's GO list is the cheapest way to extract the last bit of fold-stable skill from what we
have and to make whatever S1/S2 deliver pay off without overfitting; it is unlikely, on its own, to reach +0.144.

---

## Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/M1_sparse_data_methods.md`.
- **Ranked shortlist + verdicts:**
  1. Hierarchical/partial-pooling NB -- highest expected held-out payoff; low data need (J=4 caveat on group SD) -- **GO**.
  2. Regularization (ridge/elastic-net, nested-CV) -- modest standalone, multiplicative as enabler; very low data need -- **GO** (bundle with 1).
  3. Presence-hurdle reframe of served target -- small/cheap, better calibration; low data need -- **GO**.
  4. Penalized-spline/GAM (REML) -- ~neutral, reproduces current kernels; low EDF affordable -- **WEAK-GO** (robustness only) / NO-GO as a skill lever.
  5. NB->ZI/hurdle count upgrade -- doubles params; literature says rarely beats NB out-of-sample -- **NO-GO**.
  6. GP-modulated intensity (temporal) -- needs more N to pay off; reverts to current kernel -- **NO-GO** at our N.
  7. LGCP (spatial) -- 4 points cannot identify a spatial range; high spatial data need -- **NO-GO** (revisit post-S1).
  8. Hawkes/self-exciting -- already adjudicated; GOF diagnostic only, detector artifact if served -- **NO-GO** as skill.
  9. Synthetic data augmentation -- no new info, leakage hazard in time-blocked CV -- **NO-GO** (withhold, B.3).
- **Per-method held-out payoff + data-volume need:** in section 1 and the section 2 table; the load-bearing
  anchor is effective independent onsets ~300 pooled (5-150 per station), not raw N=2089.
- **Cheapest high-value experiment:** prototype the hierarchical NB (bundled with regularization + presence
  reframe), scored through the existing `block_cv` harness with per-fold skills, against the +0.144 / >=4/5-fold
  bar. Honest expectation: it buys fold-stability and calibration, and is unlikely alone to reach +0.144 -- the
  large skill jump most likely needs new independent observation (W9/S1/S2), which M1's GO methods then exploit
  without overfitting.
- Nothing deployed, refit-to-write, promoted, or committed. Effective confidence stays 0.0. One file written.

# Orchestrator notes for the incoming thread

Context and opinions beyond the standard handoff. This is advisory, not locked. The locked
facts are in `HANDOFF_CHARTER.md` section B. Citations below are recommended from memory;
verify exact authors/years/venues before quoting them in any artifact (the project's honesty
constraint applies to references too).

## 1. The operator's intent, as I read it

The operator wants the forecast to become a real modeled probability surface driven by the
open-source weather and wildlife data already aggregated, and wants to know how to combine the
kernel ML ops with physics-informed machine learning (PIML). The framing is consistent across
the session: build the data foundation first (CAND, done), then model the covariates honestly
(MLM), then operationalize (MLO), and never present skill the data has not earned. The PIML
question is the live design decision: where physical structure should replace or constrain the
empirical kernels.

The operator also values provenance, honesty captions, and a clean lede (research workbench
landing on live orca encounter forecasting), and dislikes filler/smug prose. Keep writing
plain and direct.

## 2. The architecture as it stands (honest summary)

- Model: a log-linear separable-kernel point process (LNP cascade), NB2 GLM, in `modeling/`.
  `log λ = b0 + s_space + k_tide + k_diel + k_lunar + k_season + k_salmon + log E`.
- Estimation is acoustic-first (hydrophone detections as the effort-stable spike train);
  visual sightings are validation + `s_space`. This is the right call and is well motivated by
  the effort-bias problem.
- Today only `k_diel` and `k_lunar` are fitted, on one station, with negative held-out CV
  skill and a failed time-rescaling KS. Effective confidence is 0%. PIT is calibrated, but
  that credit is gated behind time-rescaling.
- The neuroscience analogy (PSTH, reverse correlation, LNP, population decoding) in
  `CALIBRATION_STUDIES.md` is a genuinely good scaffold and gives a clean leveled gate plan.

## 3. How I would combine the ML ops with PIML (concrete)

Keep the interpretable LNP/GLM backbone. Inject physics as (a) physically derived covariates,
(b) physics priors on kernel shape, and (c) a hybrid mechanistic-statistical term where data
is sparse. Do not jump to a full PINN; it would sacrifice the interpretability and the gate
story that make this forecast honest.

Highest-value PIML moves, in order:

1. Tide from harmonic constituents (fixes the L2 tide exclusion). The current code estimates a
   tidal phase from sparse current records, which gave 0.42 phase coverage and got excluded. A
   physical tidal-harmonic model (M2, S2, K1, O1 constituents fit to NOAA CO-OPS, e.g. the
   T_TIDE / UTide approach) predicts current state for ANY timestamp, so coverage becomes 1.0
   and `k_tide` can enter the joint fit. This is the single cleanest PIML win and unblocks a
   real Level 2.
2. Prey as an advected field, not a static index. Build `k_salmon` as run-timing (source)
   transported by the NOAA current field with a fitted lag, rather than a bare climatology
   index. Even a simple convolution of run-timing with a current-derived transport kernel is
   physics-informed and testable with the lag scan already chartered in M-L3.
   (PRIORITY DEMOTED per G3/SYN/M3: the salmon covariate (M3 D1) is BOTH feed-gated AND
   presence-day-gated; it cannot close L3 without first adding summer presence-days from new nodes
   (TB1). D1 stays WITHHELD until then -- sequence prey-transport work AFTER the node grounding.)
3. Frontal / hydrodynamic habitat for `s_space`. Replace effort-confounded sighting density
   with physical proxies for foraging habitat: bathymetric slope, tidal-front index (gradient
   of predicted current speed), channel constriction. This de-biases `s_space` and matches the
   Haro Strait foraging-front hypothesis.
4. Energetic / movement constraint. The whale-tagger dive energetics (DBA, per-dive energy
   cost in `dtag_behavioral_analyzer`) give a physical budget. A biased correlated random walk
   constrained by bathymetry and energy cost can regularize the spatial term once real DTAG
   data lands. This is a Level 4+ idea, partnership-gated.

PIML priors to consider on the existing kernels: monotonic dose-response constraints (from the
dose-response assay in `CALIBRATION_STUDIES.md`), and advection-diffusion smoothness on the
prey field. These are soft constraints that improve estimates under scarcity without faking
structure.

## 4. What I would have done differently (architecture critique)

- The single-station, sparse-hourly-count regime is the core problem, not the covariate list.
  A frequentist NB GLM with a binary gate is brittle here (negative CV skill on one station).
  The fix that GRADUATED (SYN section 2 / M1 Tier A / TA2) is a hierarchical NB with a
  **partial-pooling random station intercept** (a ridge `1/tau^2` on station deviations), which
  cures the held-out-station fragility WITHOUT the flexibility an LGCP adds. A full hierarchical
  Bayesian log-Gaussian Cox process (LGCP) is a **conditional prototype only and a DEAD-END at
  current N** (SYN section 2: GP-modulated/spatial LGCP at 4 stations / ~300 effective onsets):
  it must first beat the GLM on fold-stable held-out CV-skill toward +0.144 (never in-sample
  likelihood) and be coordinated with M1/TA2 to avoid double-counting. The default path is Tier A
  (MMPP, partial-pooling NB), NOT a backbone replacement. Calibrated uncertainty is a fair goal,
  but it does not by itself justify the LGCP at this N.
- Close Level 0 first. The detector ROC needs the confidence-scored detection feed (OrcaHello
  carries a `confidence` field); pairing scores with the moderated labels gives a real ROC/d'.
  Every later kernel is confounded until the detector is characterized.
- Prioritize multi-station coverage and the effort model before adding covariates. A covariate
  added on one station with negative skill cannot earn confidence no matter how good the
  covariate is.
- For the sparse-count regime: the GRADUATE (TA2) is a **presence-hurdle REFRAME** -- a
  Bernoulli/cloglog companion head on per-bin PRESENCE, scored alongside the NB count fit. A
  **zero-inflated / hurdle COUNT upgrade** on the hourly NB target is a **DEAD-END** (SYN section 2
  / M1 section 1.3): do not replace the NB count model with a ZI/hurdle count model. (LGCP likewise
  remains the conditional-prototype dead-end at current N noted above.)
- Decide the acoustic-to-visual bridge explicitly (the standing open decision). The "encounter
  forecast" claim depends on it; deferring it leaves a gap between what is modeled (acoustic
  presence) and what is promised (a viewer's visual encounter).
- Operational: cache external feeds aggressively (the OrcaHello 403s cost real time this
  session). The CAND harness now caches the OrcaHello index; extend that pattern to NOAA and
  salmon pulls in MLO-FEAT.

## 5. Recommended literature (verify before quoting)

Point processes and effort-biased SDMs:
- Fithian, Elith, Hastie, Keith (2015), pooling survey + citizen-science data to correct bias,
  Methods in Ecology and Evolution.
- Warton & Shepherd (2010), Poisson point process models for presence-only data.
- Diggle, Moraga, Rowlingson, Taylor (2013), log-Gaussian Cox processes, Statistical Science.

LNP / GLM encoding (the analogy backbone):
- Pillow et al. (2008), Nature, population GLM point-process encoding.
- Paninski (2004), maximum-likelihood cascade point-process models.

Detector characterization:
- Green & Swets (1966), Signal Detection Theory and Psychophysics.

SRKW ecology and Chinook dependence:
- Ford et al. (2010), Biology Letters, killer whale survival vs prey abundance.
- Hanson et al. (2010), SRKW diet.
- Olson et al. (2018), Endangered Species Research (already in `references.bib`).
- Thornton et al. (2022), DFO CSAS, SRKW summer distribution and habitat use (already cited).

PIML:
- Karniadakis et al. (2021), Physics-informed machine learning, Nature Reviews Physics.
- Raissi, Perdikaris, Karniadakis (2019), physics-informed neural networks, J. Comp. Physics.
- Latent force models / mechanistic-GP hybrids (Alvarez, Luengo, Lawrence) for the
  statistical-mechanistic hybrid, which is closer to the right tool here than a full PINN.

Tidal harmonics and movement:
- Pawlowicz, Beardsley, Lentz (2002), classical tidal harmonic analysis (T_TIDE),
  Computers & Geosciences; UTide is the modern successor.
- Patterson et al. (2008), state-space models of animal movement, Trends in Ecology and
  Evolution; moveHMM for hidden-Markov movement.

## 6. Concrete next experiments (cheap, high information)

1. Build the harmonic tide covariate, re-run M-L2 with `k_tide` included, and see whether
   held-out skill turns positive. This is the fastest path off 0%.
2. Pair OrcaHello detection confidence with moderated labels to close M-L0 (real ROC/d').
3. (CONDITIONAL / sequence after A1 MMPP + A2 hierarchical NB.) If prototyping the LGCP backbone
   on the cached acoustic series, gate it IDENTICALLY to every other candidate: `block_cv`
   fold-stable held-out CV mean-deviance-skill toward +0.144 -- NOT calibrated PIT or in-sample
   log-likelihood alone (a flexible GP always fits better in-sample; SYN section 4 residual-risk
   trap). LGCP is a dead-end at current N (SYN section 2); the promising-now substitute is the TA2
   partial-pooling NB.
4. Re-test M-L3 only AFTER a presence-day lift from new nodes/summers (the binding lever, G3/SYN);
   refresh Albion (TB3) as support. Bonneville/DART is stock-mismatched (PATCH-salmon caveat) and an
   Albion extension alone adds no presence-days, so a lag scan on a refreshed feed cannot move L3 by
   itself.

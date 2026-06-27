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
  I would move the backbone to a hierarchical Bayesian log-Gaussian Cox process (LGCP) with
  partial pooling across stations. It gives calibrated uncertainty natively, which matches the
  project's own principle that "confidence is part of the forecast," and replaces the binary
  gate with a posterior the supervisor can threshold.
- Close Level 0 first. The detector ROC needs the confidence-scored detection feed (OrcaHello
  carries a `confidence` field); pairing scores with the moderated labels gives a real ROC/d'.
  Every later kernel is confounded until the detector is characterized.
- Prioritize multi-station coverage and the effort model before adding covariates. A covariate
  added on one station with negative skill cannot earn confidence no matter how good the
  covariate is.
- For the sparse-count regime, a zero-inflated or hurdle model (or the LGCP) fits better than
  an NB GLM on hourly bins.
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
3. Prototype the LGCP backbone on the cached acoustic series and compare calibrated PIT +
   held-out log-likelihood against the current NB GLM.
4. Run the M-L3 salmon lag scan against a real Albion/Bonneville run-timing series.

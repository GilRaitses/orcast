# Calibration studies: estimating the forecast kernels with neuroscience methods

Companion to [FORECAST_KERNELS.md](FORECAST_KERNELS.md). That doc defines the kernel model. This one sketches the plan level by level, sets a fitness gate at each level, and designs the estimation and calibration studies, using methods borrowed from sensory neuroscience (PSTH, reverse correlation, LNP cascades, signal detection theory, population decoding).

Status: study design. Nothing is fitted yet. Each level states the data it needs and the go/no-go criterion. We do not promote a modeled surface to the default heat until its level passes.

## The unifying analogy: detections as a spike train, environment as the stimulus

The kernel model is, formally, the linear-nonlinear-Poisson (LNP) cascade used to characterize sensory neurons:

```
environment s(t)  ->  linear kernels k  ->  nonlinearity f (=exp)  ->  rate lambda(t)  ->  events (detections)
```

- A hydrophone location is a "detector unit."
- Its detection times are the "spike train."
- Environmental cycles (tide, diel, lunar, season, salmon pulses) are the "stimulus."
- The kernel `k_*` is the unit's temporal "tuning curve" for that covariate.
- The link `f = exp` is the Poisson nonlinearity (same as the GLM in [FORECAST_KERNELS.md](FORECAST_KERNELS.md)).

This is why neuroscience estimation tools apply directly: they were built to recover `k` and `f` from spikes and a stimulus, which is exactly our problem.

Why acoustic detections are the right "spike train": continuous hydrophone monitoring has roughly constant effort, so its event times reflect the animal cycle, not human observation cycles. Visual sightings are effort-confounded and are reserved for validation and the social layer.

## Method 1: Peristimulus Time Histogram (PSTH) for cyclic kernels

For each cyclic covariate, define a repeating "stimulus event" and align detections to it:

| Cycle | Stimulus event (t=0) | PSTH x-axis | Recovers |
|-------|----------------------|-------------|----------|
| Diel | sunrise (or solar midnight) | hours since event (0-24) | `k_diel` |
| Tidal | flood-current onset (slack-to-flood) | hours within tidal cycle (0-12.4) | `k_tide` |
| Lunar | new moon | days within lunation (0-29.5) | `k_lunar` |
| Seasonal | Jan 1 (or run onset) | day of year | `k_season` |
| Salmon | run-timing peak | days relative to peak (lag scan) | `k_salmon` |

Procedure per cycle:
1. Pool detections across many cycles at a station (or pooled stations with a station offset).
2. Bin event times by phase; divide by occupancy/effort per bin to get rate.
3. The resulting rate-vs-phase curve is the empirical kernel (a tuning curve).
4. Smooth with a periodic spline; bootstrap cycles for confidence bands.

PSTH is the cheapest, most legible first estimate, and it produces exactly the publishable curve we want ("acoustic presence peaks ~2 h after flood onset, with a secondary dawn peak").

## Method 2: Reverse correlation / detection-triggered average (for continuous covariates)

For covariates that are continuous rather than evented (current speed, tide height, water temperature), compute the detection-triggered average: the average covariate trajectory in a window around each detection. This is the spike-triggered average (STA) and, under standard assumptions, recovers the linear kernel for that covariate. Whitening the covariate autocorrelation (spike-triggered covariance / regularized STA) corrects for covariate correlations (tide and current are correlated; STC separates them).

## Method 3: Joint LNP / Poisson GLM (the actual estimator)

PSTH and STA are per-covariate and assume separability. The estimator that fits everything jointly is the Poisson GLM/GAM (LNP):

```
log lambda(station, t) = b0 + a_station + Σ_j spline_j(covariate_j(t)) + log effort(station, t)
```

- Penalized cyclic splines per covariate; station random effects; effort offset.
- Fit by penalized likelihood (frequentist GAM) or with GP/spline priors (Bayesian) for uncertainty.
- The fitted splines are the kernels; they should match the PSTH/STA shapes (a consistency check between the simple and joint estimates).

## Leveled plan with fitness gates

Each level is a go/no-go. Do not build the next level until the current one passes on held-out data. Splits are blocked by time (whole cycles held out) to prevent leakage.

### Level 0: instrument characterization (no animal model yet)
- Goal: know the detector and the effort before modeling presence.
- Studies: signal-detection-theory characterization of the OrcaHello detector (hit rate vs false-alarm rate; d', ROC AUC) against the moderated/confirmed labels; station uptime and effort time series.
- Data: existing OrcaHello detections + confirmed labels; station logs.
- Fitness gate: known per-station effort series; detector ROC AUC reported with CI. Without this, every later kernel is confounded by detector behavior.

### Level 1: single-covariate PSTH tuning (start with diel)
- Goal: recover one kernel from acoustic spikes, de-biased by effort.
- Studies: PSTH for `k_diel` per station; then `k_tide`.
- Data: >= ~6-12 months continuous acoustic at >= 1 station.
- Fitness gate: PSTH differs from a phase-shuffled null (permutation test, p and effect size); shape is consistent across stations. If it just mirrors effort, fail.

### Level 2: joint temporal LNP (tide + diel + lunar + season)
- Goal: separate correlated cycles; get stable joint kernels.
- Studies: Poisson GAM with the four cyclic splines + station effects + effort offset; compare fitted splines to Level 1 PSTHs.
- Data: >= 1 lunar year (ideally full annual cycle) of acoustic.
- Fitness gate: held-out Poisson log-likelihood beats (a) climatology and (b) best single-covariate model; kernels stable across CV folds; joint and marginal (PSTH) shapes agree.

### Level 3: prey + space -> lambda(x, t) field
- Goal: full spatiotemporal intensity.
- Studies: add `k_salmon` (run-timing index with lag scan) and `s_space` (point-process intensity with bathymetry/channel covariates + effort-corrected sighting density).
- Data: salmon run-timing series (new adapter); bathymetry; sightings for space.
- Fitness gate: held-out skill beats the recent-detection-density baseline; probabilistic calibration within tolerance (reliability diagram near diagonal; PIT roughly uniform).

### Level 4: population decoding + uncertainty
- Goal: turn the station array into a region forecast with honest confidence.
- Studies: treat stations as a population code; decode region-level presence (population-vector / Bayesian decoder); produce a calibrated probability field with uncertainty.
- Data: multi-station concurrent detections; visual sightings as the independent validation set.
- Fitness gate: localization/region calls validated against held-out visual sightings; forecast beats persistence; calibration holds out of sample.

### Level 5: full-confidence forecast
- The kernel forecast `lambda(x,t)` is the default surface from Phase 0 onward. Each gate raises how sharp and confident it is allowed to be, not whether it is shown. Level 5 is when it has earned full confidence: Levels 3-4 passed, calibration holds out of sample, and the displayed confidence is high. At earlier levels the same forecast is shown with broader uncertainty and the detection/validation overlay one tap away.

## Calibration studies (sensory-transduction-assay framing)

Beyond fitting, these assays probe whether the response behaves like a real transduction system, which is how we earn trust in the curves:

1. Dose-response assay. Bin a covariate (e.g., current speed) into "doses"; plot detection rate per dose. Look for threshold and saturation (Hill-type curve). Tests monotonicity and whether a simple spline is justified.
2. Adaptation / habituation assay. Within a multi-day presence bout, does detection rate decay? Sensory adaptation analog; if present, the static kernel needs a slow gain/adaptation term.
3. Signal-detection (d', ROC) for the detector itself (Level 0), repeated across noise conditions (vessel noise, sea state) to map detector sensitivity vs environment, so animal presence is not confounded with detectability.
4. Null and shuffle controls. Phase-shuffled and circularly-shifted nulls for every PSTH; the kernel must beat them.
5. Cross-validation skill. Held-out deviance, explained-variance ratio vs PSTH-shuffled null, and forecast skill scores (Brier, log-loss) vs baselines.
6. Reliability and PIT. Forecast calibration: reliability diagram and probability-integral-transform histograms for the probabilistic output.
7. Population / emergence read-out. Treat the instrument network as a distributed sensor array; test whether region-scale predictability emerges from many local detectors (population decoding accuracy rising with station count). This is a sensor-fusion / population-coding claim, framed honestly: it guides the read-out architecture (per-station LNP units feeding a population layer), not a claim of cognition.

## How the layers split (restating the role change)

- Acoustic detections: the spike trains that estimate the temporal kernels (Levels 1-2) and feed the field (Levels 3-4).
- Environmental data (NOAA tides/currents, ephemeris for lunar/solar, salmon run index): the stimulus covariates.
- Visual sightings (OBIS / community): the held-out validation set (Levels 3-4) plus the social layer and citizen-science contribution; they corroborate acoustic events (acoustic + nearby visual = high-confidence training event).

## What is honest to do now (no new data required)

- Level 0 partial: characterize current OrcaHello detections (rate, false-positive fraction from the moderation labels) and document station effort.
- Build the covariate library (compute diel/lunar/solar from timestamp+location; pull historical NOAA tide/current; stub a salmon run-timing adapter) so PSTHs can be produced the moment enough acoustic history is assembled.
- Ship the detection/validation overlay UX (collapsible auto-hide instrument panel: temporal-range slider + modality toggles, soft transparent background) over the forecast surface.
- The forecast is the default surface; pre-fit it is prior-driven, broad, and shown with explicit low confidence. Do not present sharp structure the data does not support, but do present the forecast.

## Open questions

- Acoustic presence is not the same as visual encounter for a shore/kayak viewer; decide the link from acoustic `lambda` to visible-encounter probability (a learned bridge, or present them as two honest layers).
- Minimum acoustic history before Level 1/2 are credible (target: full annual + lunar coverage).
- Fitting stack and where coefficients live (offline fit; service loads coefficients), per FORECAST_KERNELS.md.
- Salmon index construction and lag.

# L2 burstiness modeling: the time-rescaling fix (research agent RD)

Owner: research agent RD. Charter: `RESEARCH_CHARTER.md` Q4 / Agent RD. Locked decisions:
`HANDOFF_CHARTER.md` section B. Status: PROTOTYPED, investigation-first, no convergence-file edits,
refit-safety on (`fk._maybe_write_s3 = lambda: None`, `run_fit(..., write_outputs=False)`), no
production store/model write, no confidence promotion, nothing committed.

Report JSON: `modeling/studies/reports/L2_burstiness_timing.json`.
Prototype (scratch, read-only reuse of `time_rescaling_diag._build_memory_store` / `_fit` and the
fitted conditional intensity): `/tmp/rd_burstiness_prototype.py` (not added to the tree).

## Headline (honest)

No ungated fix makes the EVENT-LEVEL pooled time-rescaling KS pass on the dense multi-station data.
A self-exciting (Hawkes) conditional intensity is the theoretically correct GOF and it removes the
near-zero spike almost entirely (pooled KS statistic falls from 0.773 to 0.134, fraction of rescaled
IEIs below 0.05 falls from 81.6% to 0.14%, pooled mean recenters from 0.979 to 1.002), but the pooled
KS p stays at 3.3e-33 because the residual clustering is heavier-tailed than an exponential-memory
process. The ONLY scope that passes event-level Exp(1) is the single sparsest station
(`north_san_juan_channel`, n=34, two-exponential Hawkes p=0.083), which is low power, not a fix.

The bin-count GOF route passes: the held-out hourly NB PIT is calibrated (KS vs Uniform p=0.364,
n=66,899 bins), the Poisson PIT fails at the same bins (p=1.4e-15), and held-out CV deviance skill is
+0.078 (4/5 folds, beats climatology). The honest caveat is that NB PIT uniformity is near-automatic
under a free dispersion parameter (here `nb_dispersion_alpha` = 88.1 absorbing a Poisson Pearson
dispersion of 8.69), which is exactly why the existing `_confidence_from_gates` refuses to credit PIT
unless a timing gate also passes. So the bin-count GOF only constitutes an honest L2 timing criterion
when it is PAIRED with the held-out CV-skill-beats-climatology gate (which is not automatic).

Recommendation: keep event-level time-rescaling WITHHELD with the clustering reason (B.3); the Hawkes
result is the diagnostic that explains WHY event-level Exp(1) is the wrong test for this detector
stream. Graduate, as an operator-gated build-wave decision, a redefinition of the L2 timing gate to a
bin-level criterion (held-out NB PIT calibrated AND held-out CV skill beats climatology). Do not assert
a clean timing-gate pass on the NB PIT alone.

## 1. Option survey (against the W1 diagnosis)

W1 (`time_rescaling_diag.json`) established the cause: the detection stream is bursty/clustered, not a
kernel/effort/grid problem. Median raw inter-event-interval CV 5.45 (1.0 = Poisson), 82% of pooled
rescaled IEIs near zero, a constant-rate homogeneous Poisson fails identically (pooled p=0), effort is
a no-op (uptime disjoint from detections), and the grid sweep 0.05 to 1.0 h does nothing. So a smooth
Poisson/NB conditional intensity provably cannot pass event-level Exp(1) on this stream.

| Option | What it models | Honest prior on this data |
|--------|----------------|---------------------------|
| Self-exciting (Hawkes) | Conditional intensity adds history: `lambda*(t) = mu(t) + sum_i alpha*beta*exp(-beta(t - t_i))`. Time-rescaling with the FULL conditional intensity is the textbook GOF for a clustered process (Brown et al. 2002). | Most promising event-level fix and the correct GOF; prototyped (below). |
| Refractory / dead-time | Suppresses intensity immediately after an event. | Wrong sign. The stream is EXCITATORY clustering (63 to 91% of detections within 6 min of the prior), not inhibition. A refractory term would suppress exactly where the data has the most mass and worsen the fit. Rejected on principle. |
| Hurdle / two-stage (onset vs within-bout) | Models encounter ONSETS separately from within-encounter repeats. | This is exactly the W2 encounter-onset (burst-dedup) re-score already in `_time_rescaling_report`. It recenters the mean to ~1.01 but the onset process is itself clustered and pooled KS stays p~7.5e-22 (W2 STEP_LOG). Does not pass; prototype confirms the onset process needs the Hawkes treatment too. |
| Bin-count GOF | Stop scoring event-level Exp(1); score per-bin COUNT calibration (held-out NB PIT) plus held-out predictive skill. | The charter's hypothesis: the held-out NB PIT already covers count overdispersion, so event-level Exp(1) is the wrong test for a forecast whose served target is per-bin presence. Prototyped (below); passes with a teeth caveat. |

## 2. Prototype: measured before/after

Same 4-station memory store and NB2 joint GLM as `level2_multistation` / `time_rescaling_diag`
(haro_strait from S3 + cached OrcaHello index for orcasound_lab / north_san_juan_channel /
andrews_bay; tide harmonic; covariates diel/tide/lunar/season). 2,085 pooled rescaled IEIs.

### 2a. Event-level pooled time-rescaling vs Exp(1)

| Model | Pooled KS stat | Pooled KS p | Pooled mean | Frac IEI < 0.05 | Pass (p>0.05) |
|-------|---------------:|------------:|------------:|----------------:|:-------------:|
| BASELINE smooth NB intensity (current gate) | 0.773 | 0.0 | 0.979 | 81.6% | NO |
| Hawkes, single exponential | 0.134 | 3.30e-33 | 1.002 | 0.14% | NO |
| Hawkes, two exponentials | 0.180 | 1.26e-59 | 0.853 | 0.19% | NO |

KS critical value at n=2,085, alpha=0.05 is ~0.030. The single-exponential Hawkes cuts the deviation
by ~5.7x and eliminates the near-zero spike, but 0.134 is still far above 0.030. Two exponentials do
not help (one station overfits a near-zero second rate and gets worse).

Per-station event-level KS p:

| Station | n | Baseline p | Hawkes-1 p | Hawkes-2 p | Hawkes-1 branching ratio | Hawkes-1 beta (1/h) |
|---------|---:|-----------:|-----------:|-----------:|-------------------------:|--------------------:|
| haro_strait | 761 | 0.0 | 9.6e-14 | 4.0e-15 | 0.79 | 11.7 |
| orcasound_lab | 1029 | 0.0 | 8.7e-16 | 1.2e-64 | 0.80 | 7.6 |
| andrews_bay | 265 | 2.4e-279 | 2.9e-15 | 1.2e-15 | 0.96 | 12.4 |
| north_san_juan_channel | 34 | 3.4e-33 | 0.020 | **0.083** | 0.91 | 4.7 |

The fitted branching ratios (0.79 to 0.96) say 79 to 96% of detections are self-excited (within-burst
or within-bout), i.e. the stream is dominated by repeat-triggering on a single acoustic encounter,
not by independent animal events. That is why even a correctly specified self-exciting intensity
leaves residual structure (the within-burst spacing is near-deterministic detector chatter at the
sub-minute scale, which no continuous intensity reproduces; the residual is sub-exponential / Omori
like rather than exponential-memory). Only the sparsest station passes, and only at low power.

### 2b. Bin-count GOF (Option D), held-out

| Metric | Value | Pass |
|--------|------:|:----:|
| Held-out hourly NB PIT, KS vs Uniform p | 0.364 (n=66,899) | YES (calibrated) |
| Held-out hourly Poisson PIT, KS vs Uniform p | 1.37e-15 | NO |
| NB dispersion alpha | 88.1 | (free parameter absorbing overdispersion) |
| Poisson Pearson dispersion | 8.69 | (heavily overdispersed counts) |
| Held-out CV mean deviance skill | +0.078 (4/5 folds) | YES (beats climatology) |

The held-out NB PIT passes and the Poisson PIT fails at the same bins, which only demonstrates that NB
absorbs the count overdispersion (alpha=88.1). On its own that is near-automatic and weak. The held-out
CV deviance skill (+0.078, beats climatology) is the bin-level test with teeth: it shows the
time-varying kernel intensity predicts per-bin counts better than a flat climatology out of sample.
Together (NB PIT calibrated AND CV skill beats climatology) they form an honest bin-level timing
criterion.

## 3. Does the timing gate pass honestly?

- Event-level Exp(1) (the current `pooled_pass_exp` gate): NO. The best ungated model (single-exp
  Hawkes) gets dramatically closer but fails (p=3.3e-33). This is the correct GOF for the process, so
  the failure is informative: the within-encounter timing is detector repeat-triggering, not the animal
  signal, and is not reproducible by any conditional intensity. Reporting event-level time-rescaling as
  WITHHELD with the clustering reason (B.3) remains the honest verdict.
- Bin-count level: YES, under the paired criterion (held-out NB PIT calibrated p=0.364 AND held-out CV
  skill +0.078 beats climatology). This is NOT threshold tuning; it is choosing the GOF that matches the
  served forecast target (per-bin presence / counts) instead of event-level Exp(1) on detector chatter.
  The honest caveat (NB PIT is near-automatic alone) is handled by requiring the non-automatic CV-skill
  gate alongside it.

Chosen fix: do not chase an event-level pass. Adopt the bin-count GOF as the L2 timing criterion
(NB PIT + CV skill), and carry the Hawkes self-excitation layer as the event-level diagnostic that
justifies the switch. This is a gate-definition change and therefore an operator/promotion decision for
a future build wave, not something to apply now.

## 4. Wiring spec (for a future build wave; NOT applied)

All targets in `modeling/fit_kernels.py` (local-only/untracked per B.6). Do not edit the convergence
files in this research wave.

1. `_station_intensity_fn` (around line 484). Leave the SERVED intensity unchanged (the served forecast
   is the smooth bin-rate; self-excitation is a GOF-diagnostic layer, not a served covariate). Do not
   add the Hawkes term to the served intensity.

2. `_time_rescaling_report` (around line 1194). Add two blocks alongside the existing event-level and
   encounter-level scopes:
   - `self_exciting`: per station, fit a single-exponential Hawkes
     `lambda*(t) = mu + alpha*beta*sum_i exp(-beta(t - t_i))` by MLE (multistart over beta; branching
     ratio alpha in (0,1)); compute compensator increments
     `tau_k = mu*dt_k + alpha*(1+A_k)*(1 - exp(-beta*dt_k))` with the Ogata recursion
     `A_k = exp(-beta*dt_{k-1})*(1 + A_{k-1})`; pool and KS vs Exp(1). Record the branching ratios and
     the pooled KS as the diagnostic that event-level timing is dominated by self-excitation. The
     prototype's `fit_hawkes1` / `_hawkes1_rescaled` are drop-in.
   - `bin_count_gof`: surface the held-out NB PIT (`report["pit"]`) and the held-out CV deviance skill
     (`report["cv"]["mean_deviance_skill"]`) together as the bin-level timing readout, with the Poisson
     PIT as the overdispersion contrast.
   Keep the honest `verdict` logic: event-level stays `withheld` with the clustering reason; add a
   `bin_level_verdict` = pass only when NB PIT calibrated AND CV skill > 0 (beats climatology).

3. `_confidence_from_gates` (around line 1301). This is the operator-gated change. Today the function
   requires the event-level `time_rescaling.pooled_pass_exp` for the timing quarter and gates the PIT
   quarter on that same `tr_pass`. Replace `tr_pass` with a `timing_gate` satisfied by EITHER the
   event-level Exp(1) pass OR the bin-level criterion (`pit.calibrated AND cv.mean_deviance_skill > 0`).
   Then condition the PIT quarter on `timing_gate` rather than on event-level pass. This is the only
   change that would let L2 earn timing credit on the current data, and it must be a recorded supervisor
   decision (B.1), not a refit side effect.

4. `level2_multistation.py` (convergence file, do NOT edit here): its `tr_pass = bool(tr.get("pooled_pass_exp"))`
   gate would follow the same `timing_gate` redefinition once (3) lands.

## 5. Risks

- The bin-count GOF leans on NB's free dispersion (alpha=88.1). Pairing it with the CV-skill gate is
  what keeps it honest; if a future build drops the CV-skill pairing, the timing gate becomes
  near-automatic and over-credits the model. The pairing is load-bearing.
- The Hawkes "pass" on `north_san_juan_channel` is n=34 (low power), not evidence of a genuine fix; do
  not generalize it.
- Fitting a Hawkes to the raw detection stream models detector repeat-triggering, not animal behavior.
  Used as a served covariate it would be a detector artifact; it is only honest as a GOF diagnostic, so
  the spec deliberately keeps it out of `_station_intensity_fn`.
- The whole prototype is the mixed-provenance multi-station spike train (production haro_strait + cached
  OrcaHello index); it is an EXPERIMENT, unpromoted. The cross-station consistency blocker (per-station
  sample size, gated on the 3-node production ingest, agent RE) is unaffected by this timing work.
- Adopting the bin-level gate redefinition is a methodology change with publication implications
  (time-rescaling is named the gold-standard point-process GOF in CALIBRATION_STUDIES.md); it should be
  documented as "event-level Exp(1) is inappropriate for a detector-chatter stream; GOF is scored at the
  served bin-count level" rather than presented as having passed time-rescaling.

## Return summary

- Findings doc: `.cca/catalogue/O0/20260627_mlops/research/L2_burstiness_timing.md`; report JSON:
  `modeling/studies/reports/L2_burstiness_timing.json`.
- Before/after (event-level pooled KS): baseline stat 0.773 / p 0.0 / 81.6% near-zero, recenter mean
  0.979 -> Hawkes single-exp stat 0.134 / p 3.3e-33 / 0.14% near-zero / mean 1.002. Still fails.
- Bin-count GOF: held-out NB PIT p=0.364 (calibrated), Poisson PIT p=1.4e-15 (fails), CV skill +0.078
  (beats climatology). Passes under the paired criterion.
- Chosen fix: event-level time-rescaling stays WITHHELD (clustering, B.3); recommend graduating a
  bin-level timing gate (NB PIT + CV skill) plus a Hawkes diagnostic, as an operator-gated build-wave
  decision. Wiring spec in section 4.
- No promotion, no convergence-file edits, nothing committed.

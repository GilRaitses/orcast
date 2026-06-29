# TA1 graduation: 2-state occupancy MMPP (latent present/absent chain modulating the Poisson rate)

Agent: TA1 (Tier A, graduation waveset). Date: 2026-06-27 (America/New_York). Repo:
`/Users/gilraitses/orcast`. This doc only; no convergence-file edit, no served write, no
production fetch-that-writes, no promotion, no commit. Effective confidence stays 0.0.

Authority: `GRADUATION_DISPATCH.md` (TA1 lane + the binding RECALIBRATION FROM DE + the Fit-safety
block), `GRADUATION_WAVESET_CHARTER.md` sec 1-2, `HANDOFF_CHARTER.md` sec B (B.1/B.2/B.3/B.5/B.6/B.7/
B.10), `research/signal_modeling/SYNTHESIS_signal_modeling.md`, `M2_nonlinear_physics.md` (rank 1
MMPP only), `research/L2_burstiness_timing.md`, `docs/methodology/FORECAST_KERNELS.md`,
`CALIBRATION_STUDIES.md`, `research/forward/G2_promotion_protocol.md` (the +0.144 bar + fold
stability).

DRIFT-GUARD honored: LGCP / GP-modulated intensity was NOT proposed or prototyped (NO-GO at our N per
SYN sec 2 and M1 1.6-1.7); this lane is MMPP only.

## 0. Verdict (read first)

**NO-GO vs the +0.144 fold-stable bar.** The 2-state occupancy MMPP, scored the only leakage-free way
a covariate-only served forecast can be scored, does NOT add honest held-out skill and, most
importantly, does NOT repair the event-level time-rescaling GOF (the load-bearing L2 blocker). The one
number that looks like a gain (marginal CV mean-deviance-skill +0.136) is reproduced exactly by
multiplying the existing GLM rate by a single per-fold constant (proven by a control), so it carries
zero occupancy/shape information; it is a scoring-family re-leveling artifact, and it breaks PIT
calibration (held-out KS p = 4.4e-05). The latent chain contributes nothing to the held-out predictive
shape. The structural reason: the failing GOF is sub-hour detector chatter (63-91% of detections within
6 min of the prior), and an hourly occupancy state adds no sub-hour memory.

## 1. Construction (what was prototyped)

A 2-state Markov-modulated Poisson process whose emission rate carries the EXISTING kernels. Per
station-hour bin `t`:

```
latent state          z_t in {0 (quiet/absent), 1 (foraging/present)}, shared 2x2 transition A,
                       covariate-FREE transitions (one matrix, no covariate in A)
emission mean          mu_{t,s} = base_t * r_s
base_t                 = exp(b0 + a_station + k_diel + k_tide + k_lunar + k_season) * E_t
                         (the served NB2 GLM rate per bin; carries the existing kernels + log E)
state multipliers      r_0 < r_1, fit by EM (weighted Poisson MLE), r_0 floored at 1e-3
emission family        Poisson in the EM (block_cv scores the predictive MEAN by Poisson deviance, so
                         the latent-mean structure is what matters)
```

Caps / regularization (per M2 rank-1 honesty notes and the lane brief): states capped at 2;
transitions covariate-free; Dirichlet pseudo-counts (+1) on the transition rows; `r_0` floored.
`base_t` is held to the existing kernel fit (the chain does not re-learn the kernels), so the MMPP adds
about 5 free parameters (A 2x2 with 2 free, `r_0`, `r_1`, plus the initial dist), the lowest-complexity
way to attack the timing GOF.

Two held-out predictives were scored through the SAME `block_cv` harness:

- **marginal (served-representative, leakage-free):** for a held-out contiguous time block the chain
  has no observed history to filter on (the block is held out), so the predictive collapses to the
  stationary-occupancy mixture `mu_t = base_t * (pi @ r)`. This is the honest analogue of the served
  forecast, which is covariate-and-effort-only and forward (`_station_intensity_fn` has no
  autoregressive term on observed counts).
- **one-step-ahead (contrast only):** filter forward within the test block using the observed past
  counts. This is NOT servable (the served forecast never observes "did we detect last hour"); it is
  reported only to show what the chain's memory captures.

## 2. Harness invocation (isolated scratch, write_outputs=False)

Scratch prototype (not added to the tree): `/tmp/ta1_mmpp_prototype.py` + control
`/tmp/ta1_control.py`. Mixed-provenance memory store identical to
`modeling/studies/level2_multistation.py` (production `haro_strait` stream from S3 + cached OrcaHello
index for orcasound_lab / north_san_juan_channel / andrews_bay + S3 currents + uptime). Run:

```
ORCAST_STORAGE_BACKEND=aws \
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
AWS_REGION=us-west-2 PYTHONPATH=. \
.venv-modeling/bin/python /tmp/ta1_mmpp_prototype.py
```

Refit safety (B.5/B.6): `fk._maybe_write_s3 = lambda: None` set at import; the canonical baseline came
from `fk.run_fit(mem, write_outputs=False, make_figures=False)`. No `data/models/fit_report.json` or any
served artifact was written; no production / model-bucket object was touched. `tools/waves/run-gate.sh
mlops-gate` was not modified.

Data realized: 4 acoustic stations, 2089 detections, 66,899 station-bins; covariates fit =
{diel, tide, lunar, season}. Effective independent N is about 300 onsets (most detections are
self-excited repeats; SYN sec 1 / M1).

## 3. Measured per-fold numbers (5-fold block_cv, held-out mean-deviance-skill)

### 3a. Baseline NB2 GLM (reproduces the served experiment)

| fold | 0 | 1 | 2 | 3 | 4 | mean | folds>0 | across-fold lower bound (mean - t*SE) |
|------|---|---|---|---|---|------|---------|---------------------------------------|
| skill | -0.0381 | 0.0648 | 0.1401 | 0.0662 | 0.1559 | **+0.0778** | 4/5 | **+0.0044** |

Matches the recorded experiment (+0.0778, 4/5). Event-level time-rescaling: pooled KS p = 0.0, pooled
mean 0.979, frac rescaled-IEI < 0.05 = 0.816, verdict WITHHELD (clustering, B.3).

### 3b. MMPP marginal (stationary-mixture predictive, served-representative)

| fold | 0 | 1 | 2 | 3 | 4 | mean | folds>0 | lower bound |
|------|---|---|---|---|---|------|---------|-------------|
| skill | -0.0829 | 0.1710 | 0.2762 | 0.1542 | 0.1639 | **+0.1365** | 4/5 | **+0.0104** |

Held-out NB-vs-uniform PIT for this predictive: KS p = **4.44e-05 -> NOT calibrated**.

### 3c. The +0.136 is a uniform re-leveling artifact, not occupancy skill (CONTROL)

The MMPP marginal predictive is `base_t * (pi @ r)`, i.e. the baseline GLM rate times a single per-fold
scalar (`pi @ r` approximately 0.70: the stationary mixture under-predicts the GLM level). Two controls
that multiply the SAME baseline GLM by a constant:

| predictor | per-fold skill | mean |
|-----------|----------------|------|
| baseline GLM | [-0.0381, 0.0648, 0.1401, 0.0662, 0.1559] | +0.0778 |
| baseline x (train moment match, c = sum y / sum base ~ 1.0) | [-0.0305, 0.0734, 0.1372, 0.0697, 0.1559] | +0.0812 |
| baseline x (MMPP mixture scalar, c ~ 0.70) | [-0.0829, 0.1710, 0.2762, 0.1542, 0.1639] | **+0.1365** |
| MMPP marginal (full chain) | [-0.0829, 0.1710, 0.2762, 0.1542, 0.1639] | **+0.1365** |

The "baseline x MMPP mixture scalar" row reproduces the MMPP marginal per-fold skills EXACTLY. So the
entire +0.0587 apparent gain over baseline is a global rate rescale: the NB2 MLE level (tuned to NB
likelihood) is above the Poisson-deviance-optimal level, and the Poisson-EM occupancy fit happens to
land near the lower level the Poisson-deviance CV metric rewards. It is a fitting-family vs
scoring-family mismatch, achievable by a one-line intercept shift, and it BREAKS the NB PIT (3b). No
part of it comes from the latent occupancy chain. The chain adds nothing to held-out predictive shape
(by construction the stationary mixture is shape-identical to the GLM).

### 3d. One-step-ahead (contrast only; NOT servable)

| fold | 0 | 1 | 2 | 3 | 4 | mean | folds>0 |
|------|---|---|---|---|---|------|---------|
| skill | 0.0872 | 0.3910 | 0.4627 | 0.2934 | 0.4025 | +0.3274 | 5/5 |

This large gain is the chain crediting observed-past persistence, which is the SAME detector-chatter
autocorrelation the Hawkes branching (0.79-0.96) flagged as a detector artifact, not biological
presence (L2_burstiness; M2 7b). It is unavailable to the served covariate-only forward forecast and is
therefore not gate-relevant. Reported for honesty, not as skill.

## 4. Does the occupancy chain repair the event-level time-rescaling GOF? (the load-bearing question)

**No.** Built the most favorable case: fit the MMPP on all data and form the event-level conditional
intensity `lambda*(t) = base_intensity(t) * E[r_{z(t)} | all data]` using the SMOOTHED posterior (an
oracle that peeks at the events themselves), then ran the per-station and pooled time-rescaling KS vs
Exp(1):

| scope | pooled n | pooled mean | frac IEI < 0.05 | pooled KS p | pass |
|-------|---------:|------------:|----------------:|------------:|:----:|
| baseline smooth NB | 2085 | 0.979 | 0.816 | 0.0 | NO |
| oracle MMPP (smoothed posterior) | 2085 | 1.002 | 0.316 | 0.0 | NO |

Per-station (oracle MMPP): haro_strait p = 2.7e-113, orcasound_lab p = 3.7e-249, andrews_bay
p = 4.0e-82, north_san_juan_channel p = 2.3e-18. Fitted chain: r = [0.11, 78.9], A diagonal
[0.995, 0.400], stationary pi = [0.992, 0.008].

The occupancy chain recenters the pooled mean to ~1.0 and roughly halves the near-zero IEI spike
(0.816 -> 0.316), exactly the partial improvement the Hawkes diagnostic showed (L2_burstiness:
0.816 -> 0.0014, mean -> 1.002), but the KS still fails at p = 0.0 even with the oracle posterior and
even less than the Hawkes layer kills the spike. The reason is structural and was anticipated by
L2_burstiness: the failing IEIs are within-encounter detector chatter at the sub-minute scale, inside a
single hourly bin; an hourly occupancy state is piecewise-constant within the hour, so it adds no
sub-hour memory and cannot reproduce the within-burst spacing. A constant-rate Poisson fails event-level
Exp(1) identically (Wave 1 diagnostic). The MMPP does not change that.

## 5. GO/NO-GO vs the +0.144 bar (G2)

**NO-GO.** Against the G2 promotion definition (band B: cv mean-deviance-skill >= +0.144 AND >= 4/5
folds positive AND across-fold lower bound >= +0.078 AND PIT calibrated AND a beaten Level-1 null):

- Primary purpose FAILS: the chain does not repair the event-level time-rescaling GOF (sec 4), so it
  does not unlock the timing credit it was proposed to unlock.
- The only positive-looking CV number (+0.136 marginal) is below +0.144, has an across-fold lower
  bound of +0.010 (far below the required +0.078), is a uniform re-leveling artifact with zero
  occupancy content (sec 3c), and breaks PIT calibration (KS p = 4.4e-05). With PIT failing, the
  bin-level timing gate (PIT calibrated AND skill > 0) cannot pass and the +0.15 PIT bonus is withheld,
  so even the artifact does not earn confidence under `_confidence_from_gates`.
- The honest occupancy contribution to held-out predictive shape is ~0.
- The servable, leakage-free, shape-bearing skill is therefore baseline (+0.078, conf 0.49 HOLD); the
  MMPP does not move it.

This matches SYN sec 4's residual-risk warning: the MMPP can buy in-sample / metric-gamed fit that does
not survive an honest `block_cv` read, and it did.

## 6. PATCH-SPEC (for the later single-editor integrate; NOT applied here)

Recommendation to the integrate step: **do NOT wire a served 2-state MMPP into the intensity.** The
chain neither repairs the timing GOF nor adds honest held-out shape skill, and a served stationary
mixture is just a re-leveled GLM that breaks PIT. Keep the served intensity as the smooth NB2 GLM.

If the integrate step still wants to record the negative result so the question is not re-opened
blindly, the minimal, honest, gated change in `modeling/fit_kernels.py` (local-only/untracked, B.6) is a
DIAGNOSTIC-only block, never a served-intensity change:

1. `_station_intensity_fn` (around line 485): **no change.** The served conditional intensity stays the
   smooth GLM rate. Do NOT add a latent-state multiplier to the served intensity (it does not pass
   event-level Exp(1); sec 4).
2. `_time_rescaling_report` (around line 1354): OPTIONALLY add an `occupancy_mmpp` sub-block next to the
   existing `self_exciting` (Hawkes) diagnostic, recording, per station and pooled, the oracle MMPP
   event-level KS (pooled p = 0.0, frac < 0.05 = 0.316, mean ~1.0) with the verbatim interpretation:
   "a 2-state hourly occupancy chain recenters the mean and halves the near-zero spike but does NOT pass
   event-level Exp(1); the failing IEIs are sub-hour within-encounter chatter, so the verdict stays
   WITHHELD (B.3)." Reuse the prototype's `fit_mmpp` / `_forward_backward`. This is a sibling to the
   Hawkes diagnostic (DE2 keeps Hawkes contained as a diagnostic; the MMPP diagnostic is the same
   posture), not a served covariate and not a gate.
3. `_confidence_from_gates` (around line 1623): **no change.** No new gate, no new credit. The MMPP does
   not pass any timing criterion honestly.
4. Do NOT alter `ADOPT_BIN_LEVEL_TIMING_GATE` or the bin-level gate on the back of this result: the MMPP
   marginal fails PIT, so it cannot satisfy the bin-level criterion (PIT calibrated AND skill > 0).

Net: the integrate step should reclassify the MMPP from "the cheapest gate fix" to "measured NO-GO for
served skill; valid only as an optional event-level GOF diagnostic alongside Hawkes," and spend the
fold-stable-skill budget on the Tier-B new-observation levers (B1 nodes) that SYN identifies as the
actual +0.144 route.

### DE drift note (for the integrate step)

`M2_nonlinear_physics.md` rank 1 still reads the 2-state HMM/MMPP as "PROMISING AT OUR N / GO
(prototype)" and "the single highest-value M2 candidate ... attacks the load-bearing L2 blocker." This
TA1 measurement SUPERSEDES that optimism for SERVED skill: the MMPP does not repair the time-rescaling
GOF and adds no honest held-out shape skill (NO-GO vs +0.144). When the integrate touches
`M2_nonlinear_physics.md`, append the supersession caveat alongside the existing LGCP caveat, cross-
referencing `DE1_text_drift.md` rows #1-3 (M2 reading an adjudicated/now-refuted method as a live GO)
and this doc (`TA1_occupancy_mmpp.md` sec 4-5).

## 7. Honesty / rails confirmation

- Nothing was deployed, fetched-to-write, promoted, or committed. No `data/models/fit_report.json` or
  any served artifact was written (`write_outputs=False`; `_maybe_write_s3` disabled). No convergence
  file was edited. `tools/waves/run-gate.sh mlops-gate` was not modified. Effective confidence stays
  0.0.
- The fit used the B.4 bucket (`198456344617-us-west-2-orcast-aws-backend-raw-payloads`, us-west-2) in
  `.venv-modeling`, mixed-provenance experiment store, exactly as the existing experiment (B.5/B.7).
- Numbers are MEASURED (not NOT-MEASURED): baseline +0.0778 (4/5), MMPP marginal +0.1365 (4/5, an
  artifact per sec 3c), one-step +0.3274 (not servable), oracle MMPP time-rescaling pooled KS p = 0.0
  (GOF not repaired).
- LGCP was not proposed or prototyped (drift-guard).

## 8. Return summary

- **Doc:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA1_occupancy_mmpp.md`.
- **Per-fold (block_cv, 5 folds):** baseline +0.0778 (4/5, lower bound +0.0044); MMPP marginal +0.1365
  (4/5, lower bound +0.0104) but reproduced exactly by baseline x constant (control), PIT KS
  p = 4.4e-05 (fails); one-step-ahead +0.3274 (5/5, not servable, credits detector-chatter persistence).
- **Time-rescaling repair:** NO. Oracle smoothed-posterior MMPP event-level pooled KS p = 0.0
  (frac < 0.05 down 0.816 -> 0.316, mean -> 1.0, still fails); the GOF failure is sub-hour chatter an
  hourly chain cannot fix.
- **GO/NO-GO vs +0.144:** NO-GO (below the bar, lower bound far below +0.078, PIT fails, gain is a
  re-leveling artifact, and the load-bearing timing GOF is not repaired).
- **Patch-spec:** keep the served intensity unchanged; at most add an optional event-level MMPP GOF
  DIAGNOSTIC sibling to Hawkes; no new gate, no new credit; plus a DE drift note superseding M2 rank-1's
  GO (cross-ref DE1 rows #1-3).
- Nothing deployed / fetched-to-write / promoted / committed. Effective confidence stays 0.0.

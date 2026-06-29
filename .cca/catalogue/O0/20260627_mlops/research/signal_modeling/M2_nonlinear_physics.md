# M2 nonlinear-dynamics & physics-based modeling literature (W10)

> **SUPERSEDED IN PART by SYNTHESIS_signal_modeling.md section 2 (2026-06-27).** The rank-2
> "Hierarchical LGCP backbone" below predates the synthesis and is a **DEAD-END at current N**
> (GP-modulated / spatial LGCP needs flexibility we cannot afford at 4 stations / ~300 effective
> onsets; revisit only after substantial node expansion). It is NOT a "PROMISING AT OUR N" / "GO"
> path. The authoritative graduate/dead-end split is SYNTHESIS_signal_modeling.md sections 1-2:
> graduates are MMPP (rank 1) and physics shape priors (rank 3, TA5); the Tier-A small-N win is
> the hierarchical NB partial-pooling reframe (TA2), not an LGCP backbone swap. Hawkes is retained
> only as an event-level GOF diagnostic, never as served intensity or skill.

Agent: M2 nonlinear-dynamics / physics-ML research subagent, W10 of the signal & modeling research
campaign. Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`.
Home: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/M2_nonlinear_physics.md` (this doc; no
other file edited). Read-only investigation. No deploy, no production write, no fit that writes, no
promotion, no commit (HANDOFF_CHARTER B.1/B.6/B.10).

## 0. Hydration (files read)

- `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (B.1 honesty/promotion gate, B.2 effort-bias /
  covariate-role honesty, B.3 withhold-over-fake, B.6 local-only modeling tree).
- `20260627_mlops/SIGNAL_MODELING_CHARTER.md` (this campaign; sec 4 anti-overfitting discipline).
- `20260627_mlops/SIGNAL_MODELING_DISPATCH.md` (the M2 brief).
- `20260627_mlops/research/forward/G2_promotion_protocol.md` (the +0.144 bar; the two-band promotion
  definition; fold-stability and variance-bound rules).
- `docs/methodology/FORECAST_KERNELS.md` + `CALIBRATION_STUDIES.md` (the joint-fit form, the LNP/GLM
  backbone, effort-bias design, the leveled gates).
- `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` (operator PIML strategy; the explicit "do not jump to a
  full PINN" note; the LGCP-backbone recommendation; recommended literature).
- Current-literature web survey (citations in section 9; verify authors/years before any external quote,
  per ORCHESTRATOR_NOTES sec 0 and B.1).

## 1. The data reality every method is judged against (read first)

This is the load-bearing constraint. The frontier data is NOT animal-movement telemetry. It is a
fixed-position acoustic presence stream:

- ~2089 reviewed detections across 4 fixed hydrophone stations (haro_strait, orcasound_lab, andrews_bay,
  north_san_juan_channel), binned to hourly counts (`bin_hours=1.0`).
- The hydrophone is a fixed point, not a whale GPS fix: acoustic presence is NOT a position track and NOT
  a visual encounter (B.2). There are no movement trajectories, step lengths, or turning angles.
- The stream is bursty: 63 to 91 percent of detections fall within 6 minutes of the prior detection, so
  the effective independent event count is far below 2089, and the per-station bout count (independent
  presence episodes) is in the dozens-to-low-hundreds, not thousands.
- Annual phase coverage is incomplete at some stations (0.42 to 1.00), so long-baseline cyclic structure
  is under-sampled.
- A prototyped Hawkes self-exciting fit already measured branching ratio 0.79 to 0.96 (near-critical).
  That high self-excitation is detector chatter (repeated detections of the same passing group), and it
  is exactly why event-level time-rescaling GOF fails (pooled KS p=0.0).

The promotion bar (G2): served held-out CV mean-deviance-skill must reach about +0.144, fold-stable
(at least 4 of 5 folds individually positive, across-fold lower bound at least +0.078), with PIT
calibrated and a Level-1 null beaten. The current served multi-station experiment sits at +0.078
(confidence 0.49, HOLD). Every method below is judged ONLY by whether it can plausibly show fold-stable
out-of-sample gains toward +0.144 at THIS N and THIS data modality, never by in-sample fit, flexibility,
or parameter count (charter sec 4).

The current backbone (the thing to beat or extend): a log-linear separable-kernel Poisson / NB2 point
process, `log lambda = b0 + s_space + k_tide + k_diel + k_lunar + k_season + k_salmon + log E`, fit by
penalized likelihood, scored by held-out Poisson deviance + PIT + time-rescaling.

## 2. State-space / hidden-Markov / switching models

**What granularity it could add.** The current GLM treats hourly bins as conditionally independent given
the covariates. It has no latent occupancy memory, so it cannot represent "a group is in the area for
several hours, then absent for days." A hidden-Markov / Markov-modulated Poisson process (MMPP) adds a
small latent state chain (e.g. present / absent, or quiet / foraging-present) that modulates the Poisson
rate. The covariate kernels then modulate the emission rate inside the "present" state, while the hidden
chain carries the dwell-time and gap structure. This is the single most relevant added granularity for
our data because it directly models the autocorrelation / clustering that the iid GLM mis-specifies, and
that mis-specification is the documented cause of the time-rescaling failure (the load-bearing L2
blocker). Note this is a switching model on a fixed-station COUNT series, not the moveHMM step/turn model
(we have no tracks).

**Data scale it realistically needs.** HMMs / MMPPs are among the most data-frugal latent-dynamics
models. The moveHMM literature gives no formal minimum but warns that asymptotic confidence intervals are
unreliable at small N and that formal model selection (AIC) tends to over-add states to absorb outliers.
What matters here is the number of independent state transitions (bouts), not raw bin count: with
dozens-to-low-hundreds of presence bouts, a 2-state model is identifiable; a 3-state model is marginal; a
state chain with rich covariate-dependent transition matrices is not.

**Honest over-fitting risk at our N.** MODERATE for a 2-state, covariate-light MMPP; HIGH for >=3 states
or covariate-dependent transitions. The known failure mode (moveHMM: extra states added to absorb
artifacts) is real at our N. Mitigation: cap states at 2, keep transitions covariate-free or with a
single covariate, regularize, and judge by held-out deviance + fold stability, never by AIC or in-sample
likelihood.

**Feasibility against the joint-fit form.** HIGH. An MMPP is a natural wrapper around the existing GLM:
the same kernels live in the emission rate; only a 2-state chain (about 2 extra free parameters) is added.
It is the lowest-marginal-complexity way to attack the time-rescaling GOF, and a correct timing model is
the gate that, if it flips, unlocks `gate_factor=1.0` and the +0.15 PIT bonus. It does not break the
interpretable-kernel / gate story.

## 3. Stochastic differential equations + diffusion models of movement

**What granularity it could add.** Continuous-time movement (Langevin diffusion, varying-coefficient
SDEs) would model habitat selection and behavioral response as a drift-plus-diffusion process with an
explicit stationary (utilization) distribution, natively handling irregular sampling.

**Data scale it realistically needs.** Individual telemetry tracks (GPS / satellite / DTAG) with
many fixes per animal. The beaked-whale varying-coefficient SDE work and the Langevin habitat-selection
model are both fit to per-individual position tracks. We have none of this: the data is fixed-station
presence, not movement. The DTAG dive-energetics path is explicitly Level 4+ and partnership-gated in
ORCHESTRATOR_NOTES.

**Honest over-fitting risk at our N.** Not assessable as a presence model, because the required data type
(tracks) does not exist in the frontier. Any SDE "movement" fit on fixed-station presence would be
fitting a model to data it was not designed for. Separately, generative score-based diffusion models
(the other meaning of "diffusion model") need thousands to tens of thousands of training samples and are
hopelessly over-parameterized at ~2k bursty events.

**Feasibility against the joint-fit form.** LOW. Movement SDEs do not plug into a fixed-station intensity
GLM. The ONE physics-from-SDE idea that is admissible here is not a movement model at all: an
advection-diffusion transport of a prey/run-timing field to build a physics-informed `k_salmon` covariate
(orchestrator move #2). That is a derived covariate and belongs to M3, not a nonlinear presence model.

## 4. Physics-informed ML (PINNs) and physics-guided features

**What granularity it could add.** Three distinct things, which must not be conflated:
(a) a full PINN that learns the intensity field while penalizing a PDE residual (e.g. advection-diffusion
of prey, tidal dynamics); (b) physics-guided features (harmonic tide, frontal index, transport-lagged
prey) fed to the existing GLM; (c) soft physics priors on kernel shape (monotonic dose-response,
smoothness) inside the existing GLM.

**Data scale it realistically needs.** Current literature (2025-2026) is blunt: PINN failure modes ARE
overfitting (the residual is minimized at collocation points but not elsewhere), and the fixes are heavy
regularization, double-backprop, adaptive loss weighting, and non-dimensionalization. PINNs are "data
sparse" only relative to a high-dimensional PDE field where the physics carries most of the solution;
they still carry a full neural network of parameters and offer no held-out-skill guarantee on a noisy
~2k-event stochastic point process. Process-informed NN ecology work shows wins in data-sparse, high-
transfer tasks, but those are continuous flux fields with strong mechanistic constraints, not sparse
presence counts.

**Honest over-fitting risk at our N.** Full PINN (a): HIGH, and it sacrifices the interpretability and
the leveled-gate story that make this forecast honest (ORCHESTRATOR_NOTES explicitly says do not jump to a
full PINN). Physics-guided features (b): LOW risk, but they are covariates, so the modeling credit lives
in M3 / S2, not here. Physics shape priors (c): LOW risk; they reduce variance under scarcity and are a
regularizer, not added flexibility.

**Feasibility against the joint-fit form.** Full PINN: LOW. Physics shape priors on the existing kernels
(monotonicity from the dose-response assay in CALIBRATION_STUDIES, smoothness on the prey field): HIGH and
recommended as a cheap variance reducer. The honest framing: the high-value PIML at our N is "physics into
the kernels and covariates," not "kernels replaced by a physics neural net."

## 5. Reservoir computing / echo-state networks

**What granularity it could add.** A reservoir (fixed random recurrent net) plus a linear readout can
capture nonlinear temporal memory and reconstruct low-dimensional deterministic chaotic dynamics.

**Data scale it realistically needs.** The headline "trains on ~100 to 1000 steps" results are all on
clean, noise-free, densely-sampled, low-dimensional DETERMINISTIC chaotic systems (Lorenz, Rossler), and
even there require multi-seed ensembling, careful regularization, and deterministic minimal-ESN
constructions to avoid overfitting at short length. Our data is the opposite regime: a noisy, stochastic,
bursty, mostly-zero point process with no smooth low-dimensional attractor to learn.

**Honest over-fitting risk at our N.** VERY HIGH. A reservoir of even 300 nodes hands the linear readout
300 weights to fit a series whose independent-event content is in the hundreds; on a stochastic sparse
count series with no deterministic attractor, the readout fits noise and will not generalize across CV
folds. The success regime (deterministic chaos) does not match the data-generating process (stochastic
ecological point process).

**Feasibility against the joint-fit form.** LOW. Black box, no interpretable kernels, no physical
covariate link, breaks the gate / honesty story, and no plausible path to fold-stable out-of-sample gains
at our N.

## 6. Recurrence + attractor reconstruction (delay embedding / EDM)

**What granularity it could add.** Takens delay-coordinate embedding and empirical dynamic modeling (EDM:
simplex, S-map, convergent cross mapping) can detect nonlinear determinism, state-dependent dynamics, and
(via CCM) causal coupling between an environmental driver and presence, without assuming an equation form.

**Data scale it realistically needs.** EDM needs at least ~35 to 40 points to attempt a reconstruction,
and the maximum recoverable embedding dimension is roughly sqrt(series length); short ecological series
are routinely pooled across dynamically-similar replicates. Raw bin count is not the binding constraint;
the binding constraint is that Takens assumes a deterministic attractor observed with LOW noise, which a
sparse, near-binary, stochastic Poisson presence series violates. Heavy zeros and burstiness mean there
is no smooth attractor to unfold.

**Honest over-fitting risk at our N.** HIGH as a forecast model: the S-map nonlinearity parameter (theta)
is trivially over-tuned in-sample, and on noisy sparse counts the reconstruction mostly captures noise.
CCM in particular is prone to false-positive "causality" when two series share seasonality (presence and
any seasonal covariate would), which is exactly our situation.

**Feasibility against the joint-fit form.** LOW as a model. The ONE defensible, cheap use is CCM as a
DIAGNOSTIC (does an environmental driver causally precede presence, beyond shared seasonality?), run as a
sanity check with surrogate-null controls, not as a skill-improving model. Even that is unreliable at our
N and is low priority.

## 7. Spatiotemporal point processes

This family is the closest to the current backbone and splits into three sub-methods with very different
verdicts.

**7a. Hierarchical / log-Gaussian Cox process (LGCP) with partial pooling.**
- Granularity: a latent smooth Gaussian random field added to the log-intensity captures residual
  spatiotemporal autocorrelation and overdispersion the separable kernels miss, and (the real prize)
  gives calibrated posterior uncertainty natively, which matches the project principle that "confidence is
  part of the forecast." Partial pooling across the 4 stations stabilizes per-station kernels.
- Data scale: LGCPs are standard in species-distribution modeling on sparse, clustered presence patterns,
  fit tractably via INLA/SPDE or HMC; partial pooling is specifically the small-N remedy. This is the
  orchestrator's explicit recommended backbone upgrade.
- Over-fitting risk at our N: MODERATE. The GP hyperparameters (range, variance) can over-flex and an
  unconstrained latent field can absorb signal that should be in the kernels; controlled by informative
  priors, INLA, and held-out scoring. The honest caveat: the latent GP must show fold-stable HELD-OUT
  gains, not merely a better in-sample fit (a flexible GP residual will always fit better in-sample).
- Feasibility vs joint-fit: MODERATE-to-HIGH. It is a principled generalization of the current log-linear
  Poisson GLM (same covariate kernels + a latent GP + partial pooling), not a replacement of the
  interpretable structure. Overlaps M1 (sparse-data methods); coordinate so it is not double-counted.

**7b. Spatiotemporal / self-exciting Hawkes process.**
- Already prototyped: branching ratio 0.79 to 0.96 (near-critical). That self-excitation is the detector
  chatter that breaks event-level time-rescaling; it models repeated detections of the same passing group,
  not independent biological presence.
- As a forecast it adds little honest skill (it predicts "another detection follows a detection," which is
  an artifact). Its real value was diagnostic: it is the evidence that an OCCUPANCY framing (section 2),
  not a self-exciting framing, is the right way to absorb the clustering.

**7c. Neural temporal point processes (RMTPP, neural / transformer Hawkes).**
- Data-hungry: these need many event sequences / tens of thousands of events to train, and are black-box.
  At ~2k bursty events they over-parameterize badly and break the gate story.

**Honest over-fitting risk at our N.** 7a MODERATE (controllable); 7b already characterized (skill-poor,
diagnostic only); 7c VERY HIGH.

**Feasibility against the joint-fit form.** 7a is the most natural extension of the existing model; 7b is
done; 7c is a dead-end at our N.

## 8. Shortlist, ranked by expected fold-stable held-out payoff at our N

| Rank | Method | Promising at our N vs needs far more data | GO / NO-GO | Why |
|---|---|---|---|---|
| 1 | 2-state HMM / MMPP occupancy modulation of the Poisson rate | PROMISING AT OUR N | GO (prototype) | Lowest added complexity (about 2 params); directly targets the time-rescaling GOF blocker, the load-bearing L2 gate; keeps the interpretable kernels |
| 2 | Hierarchical LGCP backbone (latent GP residual + partial pooling + calibrated uncertainty) | DEAD-END AT OUR N (superseded by SYN section 2) | NO-GO at current N; revisit post node-expansion | Per SYNTHESIS_signal_modeling.md section 2, GP-modulated/spatial LGCP is a dead-end at 4 stations / ~300 effective onsets (flexibility we cannot afford). The Tier-A small-N substitute is the hierarchical NB PARTIAL-POOLING reframe (TA2: ridge random intercept), NOT an LGCP backbone swap. Was "GO conditional" pre-SYN |
| 3 | Physics shape priors on existing kernels (monotonic dose-response, smoothness) | PROMISING AT OUR N | GO (cheap add-on) | Variance reducer under scarcity, not added flexibility; modest payoff; low risk |
| 4 | CCM / delay-embedding causality DIAGNOSTIC (with surrogate nulls) | PROMISING AT OUR N only as a diagnostic, NOT a model | WEAK GO (optional, low priority) | Cheap sanity check on driver-to-presence causality; unreliable at our N; not skill-improving |
| 5 | Spatiotemporal / self-exciting Hawkes | Already characterized | NO-GO for skill | Models detector chatter, not presence; its value was the diagnostic that motivates rank 1 |
| 6 | Full PINN (PDE-residual neural intensity field) | NEEDS FAR MORE DATA | NO-GO at our N | Failure modes are overfitting; kills interpretability + gate story; no held-out-skill guarantee at 2k events |
| 7 | Reservoir computing / echo-state network | NEEDS FAR MORE DATA (and a deterministic regime we do not have) | NO-GO at our N | Success regime is clean low-dim deterministic chaos; overfits a stochastic sparse count series |
| 8 | Delay-embedding / EDM as a forecast model | NEEDS FAR MORE DATA (low-noise determinism) | NO-GO at our N | Takens determinism assumption violated by sparse noisy point process; S-map theta over-tunes |
| 9 | Neural temporal point processes (RMTPP / neural Hawkes) | NEEDS FAR MORE DATA | NO-GO at our N | Tens of thousands of events needed; black box; over-parameterized at 2k |
| 10 | SDE / diffusion MOVEMENT models | NEEDS A DIFFERENT DATA TYPE (telemetry tracks) | NO-GO at our N | No movement tracks exist; fixed-station presence is the wrong modality; DTAG path is Level 4+ / partnership-gated |

Note: the SDE advection-diffusion PREY-TRANSPORT idea and the physics-guided FEATURES (harmonic tide,
frontal index) are admissible but are derived covariates (M3 / S2), not nonlinear presence models, so they
are excluded from this M2 model shortlist and flagged for those waves.

## 9. Promising-now vs needs-more-data split (explicit)

PROMISING AT OUR N (a fold-stable out-of-sample gain is plausible without new data):
- 2-state HMM / MMPP occupancy modulation (rank 1): the strongest single candidate, because the clustering
  it absorbs is the documented cause of the failing timing gate.
- Physics shape priors on the kernels (rank 3): cheap, low-risk variance reduction (graduated as TA5).
- Hierarchical NB PARTIAL POOLING (M1 Tier A / TA2, the small-N substitute for the LGCP backbone):
  a ridge random station intercept that cures the held-out-station fragility -- this, not LGCP, is the
  promising-now generalization of the GLM.
- CCM diagnostic (rank 4): not a model; a cheap causality sanity check only.

NEEDS FAR MORE DATA (or a different data modality), DEAD-END at our N, stated honestly:
- Hierarchical LGCP / GP-modulated intensity (was rank 2): superseded by SYN section 2 -- a dead-end at
  4 clustered stations / ~300 effective onsets; the flexible GP fits better in-sample but offers no
  plausible fold-stable held-out gain at this N. Revisit only after substantial node expansion. Use the
  TA2 partial-pooling NB as the small-N substitute.
- Full PINN, reservoir computing / ESN, delay-embedding / EDM forecasting, neural TPPs: all over-fit a
  ~2k-event bursty stochastic stream and offer no plausible fold-stable out-of-sample gain at this N.
- SDE / diffusion movement models: blocked on data TYPE (require telemetry tracks we do not have), not
  merely data volume; the hydrophone is a fixed point, not a whale GPS fix (B.2).
- Self-exciting Hawkes for skill: already characterized; models detector chatter, not presence. (Retained
  ONLY as an event-level GOF diagnostic in `_time_rescaling_report`, never as served intensity.)

## 10. Honesty notes (B.1 / B.2 / B.3 / charter sec 4)

- Nothing here promotes confidence; this doc is a decision aid (B.1). A graduated method earns confidence
  only later via a passing gate on SERVED data + a recorded supervisor decision.
- Acoustic presence stays the temporal driver with a `log E` offset; nothing proposed launders it into
  whale position (B.2). The SDE-movement NO-GO is partly a B.2 statement: we do not have, and must not
  fabricate, a whale track.
- Every PROMISING verdict is explicitly conditioned on fold-stable HELD-OUT gain toward +0.144, not
  in-sample fit, flexibility, or parameter count (charter sec 4). The LGCP caveat (a flexible GP always
  fits better in-sample) is called out so its credit cannot be claimed from in-sample likelihood.
- Methods that cannot show fold-stable out-of-sample gains at our N are named dead-ends, not deferred with
  optimistic framing (B.3 withhold-over-fake).

## Return summary

- Doc path: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/M2_nonlinear_physics.md`.
- Ranked shortlist (best fold-stable held-out payoff at our N first), RECONCILED WITH SYN section 2:
  (1) 2-state HMM/MMPP occupancy modulation; (2) physics shape priors on existing kernels (graduated as
  TA5); (3) hierarchical NB partial pooling (M1 Tier A / TA2 -- the small-N substitute for the LGCP
  backbone); (4) CCM/delay-embedding causality DIAGNOSTIC only; then dead-ends at current N: (5)
  hierarchical LGCP / GP-modulated intensity (was rank 2, superseded by SYN), (6) self-exciting Hawkes
  for skill (diagnostic-only), (7) full PINN, (8) reservoir computing/ESN, (9) EDM forecasting, (10)
  neural TPPs, (11) SDE/diffusion movement models.
- Promising-now vs needs-more-data: PROMISING AT OUR N = MMPP + shape priors + partial-pooling NB (and
  the CCM diagnostic); NEEDS FAR MORE DATA / dead-end at our N = LGCP/GP, Hawkes-as-skill, PINN,
  reservoir/ESN, EDM, neural TPPs, SDE-movement (SDE-movement blocked on data TYPE, not volume).
- Go/no-go: GO = HMM/MMPP (prototype), physics shape priors (TA5), hierarchical NB partial pooling
  (TA2); WEAK GO = CCM diagnostic (optional); NO-GO at our N = hierarchical LGCP/GP (superseded by SYN
  section 2; revisit post node-expansion), self-exciting Hawkes for skill, full PINN, reservoir/ESN,
  EDM forecasting, neural TPPs, SDE/diffusion movement models.
- The single highest-value M2 candidate is the 2-state occupancy MMPP, because it attacks the load-bearing
  L2 blocker (the failing time-rescaling GOF) with the least added complexity while preserving the
  interpretable-kernel and gate story.
- No code change, no refit, no production/model write, no promotion, nothing committed. Effective
  confidence stays 0.0.

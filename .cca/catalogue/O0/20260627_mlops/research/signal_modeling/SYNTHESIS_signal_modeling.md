# SYNTHESIS -- signal & modeling research campaign (the ranked path toward fold-stable +0.144)

Agent: O0 orchestrator (SYN run directly by the launching orchestrator, per the operator's choice).
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This doc only; no deploy, no
production write, no fit, no promotion, no commit (B.1/B.6/B.10). Effective confidence stays 0.0.

Authority: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B; `SIGNAL_MODELING_CHARTER.md`;
`SIGNAL_MODELING_DISPATCH.md` (SYN). Inputs read in full: the five findings docs
`S1_node_sources.md`, `S2_covariate_sources.md`, `M1_sparse_data_methods.md`,
`M2_nonlinear_physics.md`, `M3_derived_covariates.md`, plus `research/forward/G2_promotion_protocol.md`
(the +0.144 bar) and `G3_l3_grounding.md` (the L3 presence-day constraint).

## 0. The bar, restated (what every graduate is judged against)

Served 4-station fit = held-out CV mean-deviance-skill **+0.078 -> confidence 0.49 (HOLD)**. Crossing
0.6 needs served skill **~+0.144 AND fold-stable** (>=4/5 folds individually positive, across-fold
lower bound >= +0.078, PIT calibrated, L1 null beaten). W6 added **0 net-new analysis observations**,
so no re-run moves the number. Nothing in this campaign promotes; every graduate earns confidence
later only via a passing gate on SERVED data + a recorded supervisor decision.

## 1. The single convergent finding (all five docs independently land here)

**The +0.078 -> +0.144 gap is an OBSERVATION problem first and a MODEL problem second.**

- M1: effective independent N is **~300 encounter onsets pooled** (5-150/station), not 2089, because
  Hawkes branching 0.79-0.96 means most detections are self-excited repeats. Against ~300 onsets the
  served model already spends ~20 effective parameters. So the model-side GO list is
  *parameter-saving / variance-reducing* (hierarchical pooling, regularization, presence reframe) --
  it buys fold-stability and calibration, and is "unlikely on its own to reach +0.144."
- M3: most derived covariates are deterministic functions of covariates already in the additive model,
  so the 5-fold CV will not credit them; the only independent signal lives in a **real salmon run
  anomaly (D1, feed-gated)**, an **SST-front gradient (C1, S2-gated)**, and one cheap in-repo
  **lunar x diel (F1)**. The spatial covariate families are "blocked not by a missing recipe but by
  the 4-clustered-station data geometry" -- i.e. an S1 node-density problem.
- G3 (prior): the binding L3 constraint is **summer acoustic presence-days**, not more predictors.
- S1: unlike W6 (0 net-new), **none of the new nodes are in the cache**, so a fresh fetch adds
  genuinely new analysis observations -- the lever W6 did not have.
- M2: the one model change that could move the gate without new data is the **2-state occupancy MMPP**,
  because it fixes the documented load-bearing L2 blocker (the failing time-rescaling GOF). Every
  flexible/black-box method (PINN, reservoir, EDM, neural TPP, SDE-movement, GP/LGCP-spatial) is a
  dead-end at our N.

So the plan has two honest tiers: **(A) extract the last fold-stable skill from what we have** (cheap,
no sourcing, also makes new data pay off without overfitting), and **(B) add genuinely new independent
observation** (the actual route to +0.144). Tier A cannot reach +0.144 alone; Tier B is where the
skill jump comes from, and Tier A is what keeps Tier B honest.

## 2. Ranked graduates (data vs model, B.2 role, why)

"Type" = data (new observation) vs model (more signal per observation). "Role" = B.2 class.

### Tier A -- extract from existing data (cheap, no sourcing, do first)

| # | Graduate | Source doc | Type | B.2 role | Why it graduates | Expected held-out effect |
|---|---|---|---|---|---|---|
| A1 | **2-state occupancy MMPP** (latent present/absent chain modulating the Poisson rate; existing kernels in the emission) | M2 rank 1 | model | effect (timing) | Directly attacks the failing time-rescaling GOF -- the load-bearing L2 blocker -- at ~2 added params; if the timing gate flips it unlocks `gate_factor=1.0` + the PIT bonus | gate-relevant; the cheapest single change that can move the served number |
| A2 | **Hierarchical / partial-pooling NB** (random station intercept -> kernels) bundled with **regularization (nested-CV)** and the **presence-hurdle reframe** of the served target | M1 ranks 1-3 | model | effect | *Saves* parameters where data is thinnest (nsjc eff ~5, andrews ~40); the only model family with consistent small-N held-out evidence; buys fold-stability + calibration and lets Tier B pay off without overfitting | fold-stability/calibration; modest skill |
| A3 | **AIS-derived effort/noise term in `log E`** | S2 rank 1 | data (effort) | **effort/exposure** | De-biases the exposure offset every temporal kernel already depends on; raises skill without adding a presence parameter; open Marine Cadastre feed | small, low-risk; cleans existing kernels |
| A4 | **F1 lunar x diel** + **A1-tide slack/max-flow** (with the +1-harmonic control), under A2's regularizer | M3 ranks 3-4 | model | effect | The only in-repo derived covariates with independent content; cheap bounded tests of whether any squeezed nonlinearity survives CV | small; run because nearly free |
| A5 | **Physics shape priors** (monotonic dose-response, smoothness) on existing kernels | M2 rank 3 | model | effect | Variance reducer under scarcity, not added flexibility; low risk | small |

### Tier B -- add new independent observation (the actual +0.144 lever, operator-gated)

| # | Graduate | Source doc | Type | B.2 role | Why it graduates | Expected held-out effect |
|---|---|---|---|---|---|---|
| B1 | **Ground Port Townsend + Bush Point (OrcaHello)** via the W6 reviewed-outcome path with a widened region gate | S1 ranks 1-2 | **data** | effect (acoustic, `log E`) | Same adapter/feed/schema as the current 4; absent from the cache, so genuinely new SRKW presence-days (Admiralty Inlet corridor). Caveat: out-of-box region expansion; Bush Point effort gaps must be in `log E` | the cheapest new-observation lever; the thing M1/M3 say is actually needed |
| B2 | **Wire the SST-front gradient covariate (C1)** from MUR/VIIRS | S2 rank 2 + M3 C1 | data + model | effect | The strongest field-sourced independent covariate; unlocks M3-C1; use the gradient, orthogonalized vs `k_season` | small-to-moderate, genuinely independent |
| B3 | **Refresh the real Albion feed + wire the run ANOMALY (D1)** | M3 D1 + G3 | data + model | effect | The strongest non-tidal biological driver; use the anomaly vs day-of-year climatology to break season collinearity. NOTE per G3: L3's binding constraint is presence-days (-> B1), not the feed; D1 is gated on a real feed and stays WITHHELD on climatology | potentially highest single covariate, but feed-gated + presence-day-gated |
| B4 | **Ground ONC / JASCO Boundary Pass (ECHO published dataset)** | S1 rank 3 | **data** | effect (acoustic, `log E`) | Best independence (independent operator + detector + expert annotations, real SRKW corridor); higher effort (historical, own extraction, duty-cycle effort model) | strong independent corroboration node |
| B5 | **Wire SalishSeaCast subtidal currents + shear** to enable the front covariate (M3-B1) | S2 rank 3 + M3 B1 | data + model | effect | Gridded in-region current field (HF radar is shadowed); only the de-tided residual/shear is admissible. Payoff still damped until presence is spatially resolved (depends on B1/B4 nodes) | conditional; pairs with more nodes |

### Dead-ends (named honestly, B.3 -- do not spend effort here)

- **Modeling:** full PINN, reservoir computing / ESN, delay-embedding / EDM forecasting, neural TPPs
  (all overfit ~2k bursty events); **SDE/diffusion movement models** (blocked on data TYPE -- we have
  no whale tracks, B.2); **self-exciting Hawkes for skill** (detector chatter, already adjudicated --
  keep only as the GOF diagnostic that motivates A1); **GP-modulated intensity / spatial LGCP at
  current N** (flexibility we cannot afford; revisit only after many more nodes); **synthetic data
  augmentation** (no new info, CV-leakage hazard); **NB -> ZI/hurdle count upgrade** (rarely beats NB
  out-of-sample at our regime).
- **Covariates:** **CUTI/BEUTI upwelling** (out of product coverage, 31-47 N; our region ~48.5 N);
  **HF-radar currents** (in-region radar shadow); **bathymetry/terrain on the gate** (it is `s_space` /
  validation-only, not a temporal-skill lever -- GO only inside a separate `s_space` quality wave);
  **most A/B/F derived transforms** (A2, F2, F3 collinear; B1/D3 blocked by station geometry).
- **F4 station x tide** is not a dead-end but a mis-filed item: its honest form is A2's hierarchical
  station random effect, so it folds into Tier A, not M3.

## 3. The cheapest high-value experiment

Two distinct "cheapest" answers, because the gap is two problems:

- **Cheapest gate-relevant model experiment (zero sourcing): the 2-state occupancy MMPP (A1).** It
  needs no fetch, no new feed, ~2 added parameters, and it attacks the *documented* load-bearing L2
  blocker (the time-rescaling GOF failure that the prototyped Hawkes branching 0.79-0.96 explains). If
  the timing model flips the gate, it unlocks `gate_factor=1.0` + the PIT bonus on the data we already
  have. This is the first thing to run.

- **Highest-value new-observation experiment (the actual +0.144 lever): the S1 Port Townsend + Bush
  Point dry-run (B1).** Re-fetch OrcaHello reviewed-outcomes for those two nodes with the region gate
  widened to Admiralty Inlet, build the new caches, and dry-run whether they add net-new SRKW
  presence-days the current 4-station universe lacks. It is the exact W6 mechanic but -- unlike W6 --
  against stations **not already in the cache**, so it is the first move that adds *new analysis
  observation* rather than re-shelving it. M1 and M3 both conclude this is what the +0.144 jump
  actually requires.

**Recommended sequencing:** run A1 (MMPP) and B1 (PT+Bush dry-run) first and in parallel -- A1 is the
cheapest gate fix from existing data, B1 is the cheapest new observation. Bundle A2/A3 next so the
model is fold-stable and the effort offset is clean before any new covariate (B2/B3) is judged;
otherwise a new covariate's CV-skill is read against a mis-specified baseline. B3/B4/B5 follow as
their feeds/extractions land. Everything in Tier B is a separate operator-gated build/deploy/promote
wave; nothing here promotes.

## 4. One residual risk carried forward

**Small-N overfitting masquerading as a graduate.** Tier A is deliberately parameter-saving, but A1
(MMPP), A4 (interactions), and any Tier-B covariate can still buy in-sample fit that does not survive
`block_cv`. Every graduate MUST be scored by fold-stable held-out CV mean-deviance-skill (>=4/5 folds,
across-fold lower bound >= +0.078, nested-CV for any tuned penalty), never in-sample likelihood or
added parameters. The LGCP/GP caveat is the canonical trap (a flexible residual always fits better
in-sample); the MMPP and every interaction inherit it. State per-fold skills on every graduation.

## 5. Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/SYNTHESIS_signal_modeling.md`.
- **Convergent finding:** the +0.078 -> +0.144 gap is an OBSERVATION problem first; model levers buy
  fold-stability/calibration, new independent observation buys the skill jump.
- **Tier A (cheap, from existing data, model + effort):** A1 2-state occupancy MMPP (gate-relevant);
  A2 hierarchical NB + regularization + presence reframe; A3 AIS effort term in `log E`; A4 in-repo
  F1/A1 derived covariates (bounded); A5 physics shape priors.
- **Tier B (new independent observation, the +0.144 lever, operator-gated):** B1 ground Port Townsend +
  Bush Point (cheapest new obs); B2 SST-front gradient covariate; B3 real Albion feed + run anomaly
  (presence-day-gated per G3); B4 ONC/Boundary Pass node; B5 SalishSeaCast subtidal-current shear.
- **Dead-ends (B.3):** PINN, reservoir/ESN, EDM, neural TPP, SDE-movement, spatial GP/LGCP at our N,
  synthetic augmentation, NB->ZI upgrade, CUTI/BEUTI (coverage), HF radar (shadow), terrain-on-the-gate,
  most derived transforms.
- **Cheapest high-value experiment:** A1 (2-state MMPP) as the zero-sourcing gate fix, run in parallel
  with B1 (PT+Bush Point dry-run) as the cheapest new-observation lever; bundle A2/A3 before judging
  any new covariate.
- **Residual risk:** small-N overfitting; score every graduate by fold-stable held-out CV-skill, never
  in-sample fit.
- Nothing deployed, promoted, or committed. Effective confidence stays 0.0. Each Tier-B item is a
  separate operator-gated wave.

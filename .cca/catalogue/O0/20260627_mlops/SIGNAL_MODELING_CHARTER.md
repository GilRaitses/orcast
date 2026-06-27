# Signal & modeling research campaign charter (the +0.144 lever)

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (MLM + MLO)
Home: `.cca/catalogue/O0/20260627_mlops/`
Authority above this doc: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
Inputs: the W7 measured-HOLD result and the forward-path grounding (`research/forward/G1-G3`,
`CAMPAIGN_CHARTER.md`).

## 0. Why this campaign exists

W7 measured the served 4-station fit at held-out CV skill **+0.078 -> confidence 0.49 (HOLD)**, below
the 0.6 supervisor threshold. The W6 ingest reproduced the experiment but added **0 new observations**,
so the same cached data cannot move the number further. Crossing 0.6 honestly needs genuinely new,
independent signal pushing served skill toward **~+0.144** AND a fold-stable result. There are two ways
to get there, and this campaign researches both, investigation-first:

1. **More independent observation** -- discover and ground additional in-region nodes and sourceable
   covariate signals (more stations, more real presence-days, independent physical drivers).
2. **More signal per observation** -- creative + physics-based modeling for sparse, bursty, nonlinear
   data, and subtler covariates computed from existing or sourceable signals (extract more granularity
   from what we have).

Honesty is unchanged (B.1/B.2/B.3): nothing here promotes confidence; findings are decision aids. The
effort-bias rule stands -- acoustic detections drive temporal kernels with a `log E` offset; visual /
external presence is validation + `s_space` only; a covariate must be classed honestly as an
effect-modifier vs an effort/exposure term, never laundered into whale GPS.

## 1. Objectives

- **S1 -- In-region node source discovery + grounding.** Enumerate every additional in-region acoustic /
  hydrophone node and reviewed-detection source beyond the current four (haro_strait, orcasound_lab,
  andrews_bay, north_san_juan_channel), with data access, provenance, license, cadence, and a W6-style
  ingest/grounding plan per node. The deliverable is a node catalog + per-node grounding readiness.
- **S2 -- Covariate signal source discovery.** Catalogue sourceable physical/oceanographic/biological
  signals (SST/fronts, salinity, currents/shear, river discharge, upwelling, tide harmonics, bathymetry-
  derived terrain, ambient-noise/AIS, prey proxies) with access + provenance, each classed honestly by
  its admissible role (effort/exposure term vs effect-modifier vs validation-only, B.2).
- **M1 -- Sparse-data modeling literature.** Methods that extract more held-out skill from sparse, bursty
  count/point-process data (log-Gaussian Cox processes, GP intensity, hierarchical/partial-pooling Bayes,
  Hawkes/self-exciting, hurdle/NB, regularization, data augmentation), with applicability + expected
  payoff at our N.
- **M2 -- Nonlinear-dynamics & physics-based modeling literature.** State-space / SDE / physics-informed
  (PINN) / reservoir-computing / dynamical-systems approaches for capturing granularity in presence
  dynamics, with feasibility at our data scale and an honest over-fitting risk assessment.
- **M3 -- Subtler derived covariates.** Physics-based / engineered covariates computable from existing or
  S2-sourceable signals (tidal-phase nonlinearities, current shear/strain, thermal-front proximity,
  prey-lag interactions, spatiotemporal terms), each with a computation recipe and an expected-signal
  rationale.
- **SYN -- Synthesis.** Rank what graduates to a build/deploy wave, what is a dead-end, and the cheapest
  high-value experiment that could move served skill toward +0.144 honestly.

## 2. Shape: two parallel research waves + a synthesis

```
W9  source discovery (parallel, investigation-first; web + repo reads, no deploy)
  S1 in-region node discovery + grounding   -> research/signal_modeling/S1_node_sources.md
  S2 covariate signal source discovery       -> research/signal_modeling/S2_covariate_sources.md

W10 modeling literature (parallel, investigation-first; literature + small numeric sanity only)
  M1 sparse-data methods                     -> research/signal_modeling/M1_sparse_data_methods.md
  M2 nonlinear-dynamics / physics-based       -> research/signal_modeling/M2_nonlinear_physics.md
  M3 subtler derived covariates              -> research/signal_modeling/M3_derived_covariates.md

SYN synthesis (depends on W9 + W10)          -> research/signal_modeling/SYNTHESIS_signal_modeling.md
```

W9 can run first (its node/covariate catalog feeds M3's "computable from sourceable signals"), or W9 and
W10 can run together with M3 assuming S2's candidate list; the synthesis depends on all five. Each agent
writes ONE doc, edits no convergence file, deploys nothing, promotes nothing, commits nothing.

## 3. Honesty rails (HANDOFF_CHARTER section B)

- B.1 No promotion; findings are decision aids. A graduated method only earns confidence later via a
  passing gate on SERVED data + a recorded supervisor decision.
- B.2 Covariate honesty: every proposed signal/covariate must be classed as effort/exposure vs
  effect-modifier vs validation-only; acoustic stays the temporal driver, visual stays validation/s_space.
- B.3 Withhold over fake: a method/source that cannot be honestly validated at our N is reported as such.
- B.6 Local-only pipeline; B.8 mlops-gate stays green; B.10 no agent commits.
- External literature/sources via web search/fetch; in-region feed fetches (if any test) via the aimez
  EC2 `i-04a649f91274e9fce`. No production store write; no fit that writes.

## 4. Anti-overfitting discipline (load-bearing)

The frontier is small-N and the confidence map jumps quickly. Every modeling/covariate proposal MUST be
judged by held-out CV mean-deviance-skill + fold stability (the W7 bar: ~+0.144 and a fold pass-rate that
beats chance), NOT by in-sample fit or added parameters. Flexible nonlinear methods that cannot show
out-of-sample, fold-stable gains on this N are dead-ends, stated honestly.

## 5. Gates

- W9 exit: S1 + S2 each land a catalog with access/provenance + a per-item honest role/grounding plan.
- W10 exit: M1/M2/M3 each land a method/covariate shortlist with applicability + expected held-out payoff
  + an over-fitting risk note.
- SYN exit: a ranked plan -- what graduates to a build/deploy wave (e.g. ground a specific new node, or
  prototype a specific sparse-data model / derived covariate), what is a dead-end, and the cheapest
  high-value next experiment.
- Any build/deploy/promotion that follows is a separate operator-gated wave; nothing here promotes.

## 6. Return contract

Each agent returns its doc path, the catalog/shortlist, the honest role/over-fitting assessment, and a
go/no-go for graduating each item. The synthesis returns the ranked plan + the cheapest experiment. No
agent deploys, promotes, or commits.

## 7. Status

CHARTERED. Dispatch in `SIGNAL_MODELING_DISPATCH.md`. W9/W10 launch is the next operator gate.

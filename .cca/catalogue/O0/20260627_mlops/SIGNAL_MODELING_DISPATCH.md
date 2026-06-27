# Signal & modeling research dispatch (W9 source discovery + W10 modeling literature)

Canonical prose: `SIGNAL_MODELING_CHARTER.md`. Self-contained prompts for the two parallel research
waves + the synthesis. Each agent owns ONE doc under
`.cca/catalogue/O0/20260627_mlops/research/signal_modeling/`, edits no other file, deploys nothing,
writes to no production store, runs no fit that writes, promotes nothing, commits nothing (B.1/B.6/B.10).

Shared context every agent must read first:
- `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (locked; esp. B.1 honesty,
  B.2 covariate-role honesty, B.3 withhold-over-fake)
- `.cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_CHARTER.md` (this campaign)
- `.cca/catalogue/O0/20260627_mlops/research/forward/G1_ingest_deploy.md` (W6 node ingest pattern),
  `G2_promotion_protocol.md` (the W7 bar: served skill ~+0.144, fold-stable), `research/SYNTHESIS_L2_L3.md`
- `docs/methodology/FORECAST_KERNELS.md` + `CALIBRATION_STUDIES.md` (model form, effort-bias, the gates)

Current state to anchor on: served 4-station fit = held-out CV skill +0.078 -> confidence 0.49 HOLD;
the W6 ingest added 0 new observations; crossing 0.6 needs genuinely new signal to ~+0.144, fold-stable.
Judge every proposal by held-out, fold-stable CV-skill, never in-sample fit (anti-overfitting, charter
sec 4). External literature/sources via web search/fetch; in-region feed probes (if any) via aimez EC2
`i-04a649f91274e9fce`. Repo: `/Users/gilraitses/orcast`; reads only.

---

## S1 -- in-region acoustic node source discovery + grounding (W9)

Produce `research/signal_modeling/S1_node_sources.md`. Goal: find EVERY additional in-region
acoustic/hydrophone node and reviewed-detection source beyond the current four (haro_strait,
orcasound_lab, andrews_bay, north_san_juan_channel) that could add independent presence observations.

Read the W6 ingest pattern (`src/aws_backend/ingest_multistation.py`, `EXTRA_NODES`, the OrcaHello
reviewed-outcome cache) and `modeling/studies/common.py` STATION_COORDS. Then discover (web + known
networks): all Orcasound/OrcaHello hydrophone locations in the Salish Sea / Haro Strait / San Juans;
Ocean Networks Canada (ONC) hydrophones; SMRU/JASCO/WHale-listening or Salish Sea Hydrophone Network
nodes; any DFO/NOAA passive-acoustic deployments in-region; and reviewed-detection feeds for each.

Deliver a NODE CATALOG: per node -> name, coordinates, operator, data access (API/endpoint/cache/license),
temporal span + cadence, reviewed-vs-raw detections, in-region relevance, and a W6-style grounding plan
(how to turn it into `acoustic_detections` records keyed by station, dedupe, provenance). Flag which add
genuinely INDEPENDENT observation (new whale-presence days) vs duplicate the existing cache. End with a
ranked go/no-go: which nodes are worth grounding next to push served skill toward +0.144. No fetch that
writes; no deploy; no commit.

---

## S2 -- covariate signal source discovery (W9)

Produce `research/signal_modeling/S2_covariate_sources.md`. Goal: catalogue sourceable
physical/oceanographic/biological signals that could become honest covariates.

Read `docs/methodology/FORECAST_KERNELS.md` (current covariates: tide harmonic, diel, lunar, season,
k_salmon, s_space; effort-bias B.2) and `modeling/tide_harmonic.py`. Then discover sourceable feeds (web):
SST + thermal fronts (e.g. NOAA/NASA MUR SST), salinity, surface currents/shear (HF radar, ROMS/SalishSeaCast),
river discharge (Fraser at Hope), upwelling indices, tidal/current harmonics, bathymetry-derived terrain
(already have CUDEM), ambient noise / AIS vessel traffic, and prey proxies beyond Albion/DART.

Deliver a COVARIATE SOURCE CATALOG: per signal -> source, access/provenance/license, spatial+temporal
resolution, and -- critically -- its ADMISSIBLE ROLE under B.2 (effort/exposure term vs effect-modifier
covariate vs validation-only), with the honest reason. Flag collinearity risks with existing covariates
(e.g. SST vs season). End with a ranked go/no-go on which signals are worth wiring as covariates. No
fetch that writes; no deploy; no commit.

---

## M1 -- sparse-data modeling literature (W10)

Produce `research/signal_modeling/M1_sparse_data_methods.md`. Goal: methods that extract more held-out
skill from sparse, bursty count/point-process detection data at our N (~2k detections, 4 stations).

Survey (web + your knowledge): log-Gaussian Cox processes, GP-modulated intensity, hierarchical /
partial-pooling Bayesian count models, Hawkes / self-exciting processes (already prototyped -- branching
0.79-0.96), hurdle / zero-inflated / negative-binomial models, penalized splines/GAMs, regularization,
and principled data augmentation. For each: what it buys on sparse bursty data, the held-out-skill /
calibration evidence from the literature, its data-volume requirement, and feasibility in the existing
`modeling/` pipeline. Judge by out-of-sample, fold-stable skill (charter sec 4), not flexibility. End with
a shortlist ranked by expected held-out payoff at our N + a go/no-go for graduating each to a prototype.
No code change; no commit. (A tiny illustrative numeric sanity check is allowed but must not write.)

---

## M2 -- nonlinear-dynamics & physics-based modeling literature (W10)

Produce `research/signal_modeling/M2_nonlinear_physics.md`. Goal: nonlinear/dynamical-systems and
physics-informed approaches for capturing more granularity in presence dynamics.

Survey (web + knowledge): state-space / hidden-Markov / switching models, stochastic differential
equations + diffusion models of movement, physics-informed ML (PINNs) and physics-guided features,
reservoir computing / echo-state networks, recurrence + attractor reconstruction (delay embedding), and
spatiotemporal point processes. For each: what granularity it could add, the data scale it realistically
needs, an HONEST over-fitting risk at our N (small-N flexible models that cannot show fold-stable
out-of-sample gains are dead-ends), and feasibility against the current joint-fit form. End with a
shortlist + a go/no-go per method, explicitly separating "promising at our N" from "needs far more data".
No code change; no commit.

---

## M3 -- subtler derived covariates (W10)

Produce `research/signal_modeling/M3_derived_covariates.md`. Goal: physics-based / engineered covariates
computable from EXISTING covariates or S2-sourceable signals, that could add subtle independent signal.

Read the current covariates (`docs/methodology/FORECAST_KERNELS.md`, `modeling/tide_harmonic.py`). Propose
derived features: tidal-phase nonlinearities + slack/max-flow timing, current shear/strain + convergence
(fronts), thermal-front proximity, prey-lag interaction terms, bathymetry-derived terrain features
(slope/aspect/channel proximity from the CUDEM grid), and spatiotemporal interaction terms. For each: the
computation recipe (from which existing/sourceable signal), the physical rationale for why it should track
SRKW presence, its admissible role under B.2, collinearity with existing covariates, and the expected
held-out-skill contribution. (If S2 is available, cite its sources; else assume a reasonable candidate
list and flag the dependency.) End with a ranked go/no-go for prototyping each. No code change; no commit.

---

## SYN -- synthesis (depends on W9 + W10)

Produce `research/signal_modeling/SYNTHESIS_signal_modeling.md`. Read S1, S2, M1, M2, M3. Deliver a ranked
action plan toward an honest served skill ~+0.144 (fold-stable): which NODE(s) to ground next (S1), which
COVARIATE source(s) to wire (S2), which MODEL(s)/derived covariate(s) to prototype (M1/M2/M3); what is a
dead-end; and the single cheapest high-value experiment most likely to move served, fold-stable CV-skill.
State, for each graduate, whether it is data (new observation) or model (more signal per observation), and
its honest role (B.2). Nothing promotes. Return the ranked plan + the cheapest experiment.

# Graduation waveset dispatch (Tier A / Tier B / Dead-End drift audit)

Canonical prose: `GRADUATION_WAVESET_CHARTER.md`. Self-contained prompts for three parallel waves of
deep subagents. Each subagent writes ONE findings/report doc (TA/TB also emit a patch-spec section in
that same doc), edits no convergence file, runs no fit that writes the served store, deploys nothing,
promotes nothing, commits nothing (B.1/B.5/B.6/B.10).

Shared context every subagent reads first:
- `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (locked; esp. B.1 honesty,
  B.2 covariate-role honesty, B.3 withhold-over-fake, B.5 AWS bucket footgun, B.6 refit-upload-disable,
  B.7 local-only pipeline, B.10 no commits)
- `.cca/catalogue/O0/20260627_mlops/GRADUATION_WAVESET_CHARTER.md` (this waveset + the execution model)
- `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/SYNTHESIS_signal_modeling.md` (the ranked
  plan; your lane's row) + the relevant S1/S2/M1/M2/M3 findings doc
- `docs/methodology/FORECAST_KERNELS.md` + `CALIBRATION_STUDIES.md` (model form, effort-bias, gates)
- `research/forward/G2_promotion_protocol.md` (the +0.144 bar + fold-stability definition)

Current state to anchor on: served 4-station fit = held-out CV mean-deviance-skill +0.078 -> conf 0.49
HOLD; effective confidence 0.0; crossing 0.6 needs served skill ~+0.144, fold-stable. Judge every
proposal by held-out, fold-stable CV-skill via `modeling/validation/crossval.py` `block_cv`, never
in-sample fit. Effective independent N is ~300 encounter onsets pooled (not 2089). Repo:
`/Users/gilraitses/orcast`.

Findings dir (create if needed): `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/`.

## RECALIBRATION FROM DE (2026-06-27) -- read before your lane

The DE wave ran first (read-only). Outcome: the SERVED CODE is clean -- DE2 found **0 HIGH** drift,
no adjudicated dead-end model family is implemented or reachable from the served path, and Hawkes is
correctly contained as an event-level GOF diagnostic. The drift that exists is entirely in PROSE, and
some of it lives in the very source docs your lane reads. So this drift-guard is binding:

- **SYN section 2 dead-end set + `signal_modeling_graduation.dead_end_set` OVERRIDE any stale GO you
  encounter in a source doc.** If a doc you read recommends a dead-end, treat it as superseded, cite
  the DE register row, and do not revive it. The full adjudicated dead-end set is restated in the
  WAVE DE section below.
- **DE1 rows #1-3 -- `M2_nonlinear_physics.md` still reads LGCP rank-2 as "GO / PROMISING AT OUR N"
  (pre-SYN).** TA1, read M2 for the MMPP (rank 1) ONLY; the LGCP backbone is **NO-GO at current N**
  (SYN section 2; M1 1.6-1.7). Do not propose, prototype, or offer LGCP/GP-modulated intensity as an
  alternative.
- **DE3 row #10 -- the presence/count distinction.** TA2: the **presence-hurdle reframe** (Bernoulli/
  cloglog on per-bin presence) is the GO graduate; an **NB->ZI/hurdle COUNT upgrade** on the hourly NB
  target is **NO-GO**. Keep them distinct in your report and patch-spec.
- **DE1 row #5 / DE3 rows #3-9 -- the L3 framing is stale.** TB3: the Albion Chinook feed is already
  real and stock-aligned (G3); the binding L3 constraint is summer **PRESENCE-DAYS** (TB1), not the
  feed. TB3 stays SUPPORTING, D1 stays WITHHELD on the placeholder, and L3 stays WITHHELD. Do not
  frame "more prey series" or "validate the feed" as the L3 lever. CUTI/BEUTI upwelling is **NO-GO
  (out of 31-47 N coverage)** -- do not reintroduce it.
- **DE1 rows #6-10 -- role honesty.** TB2/TB5/TA4: terrain/bathymetry is **`s_space`/validation-only**,
  never credited on the temporal gate; HF-radar currents are **NO-GO in-region (shadow)** -- SalishSeaCast
  residual only; raw current speed is collinear with `k_tide` (subtidal/shear residual only).
- **Carry the fix forward.** If your lane's patch-spec touches a doc DE flagged (`M2_nonlinear_physics.md`,
  `wave_shape.yml` `signal_modeling_research.objectives`, `ORCHESTRATOR_NOTES.md`, the wildlife
  register), append a one-line "DE drift note" to your patch-spec pointing at the relevant DE register
  row, so the later single-editor integrate lands the supersession caveat alongside your change.

Full DE registers: `research/signal_modeling/graduation/DE1_text_drift.md`, `DE2_method_drift.md`,
`DE3_strategy_drift.md`.

Fit safety for ANY fit (TA/TB): run in `.venv-modeling`, in an isolated scratch output dir, with
`ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`
and the production upload disabled (`fit_kernels._maybe_write_s3 = lambda: None` and/or
`write_outputs=False`). NEVER write `data/models/fit_report.json` or any served artifact. Do not edit
any convergence file; deliver a PATCH-SPEC instead. Keep `tools/waves/run-gate.sh mlops-gate` green.

---

# WAVE TA -- extract from existing data (model + effort)

## TA1 -- 2-state occupancy MMPP

Produce `research/signal_modeling/graduation/TA1_occupancy_mmpp.md`. Read M2 (rank 1) and
`research/L2_burstiness_timing.md` (the time-rescaling failure + Hawkes branching 0.79-0.96). Prototype
a 2-state (present/absent or quiet/foraging) Markov-modulated Poisson process whose emission rate
carries the EXISTING kernels (`k_diel/k_tide/k_lunar/k_season` + `log E`); cap at 2 states; keep
transitions covariate-free or single-covariate; regularize. In an isolated scratch fit (write_outputs
=False), score it through `block_cv`: report per-fold held-out CV mean-deviance-skill, the across-fold
lower bound, PIT, and crucially whether the occupancy chain repairs the event-level time-rescaling GOF
(the load-bearing L2 blocker). Judge by fold-stable held-out skill, NEVER in-sample likelihood or AIC.
Deliver: measured per-fold numbers + a GO/NO-GO vs the +0.144 bar + a PATCH-SPEC for the later
single-editor integrate into `fit_kernels.py`. No convergence edit, no served write, no commit.

## TA2 -- hierarchical NB + regularization + presence reframe

Produce `.../graduation/TA2_hierarchical_nb.md`. Read M1 (ranks 1-3). Prototype a partial-pooling NB
(random station intercept, then optionally partially-pooled kernels) with a weakly-informative
half-normal prior on the group SD (J=4 weakly identifies it), bundled with nested-CV regularization
(ridge/elastic-net on the kernel + interaction coefs) and a presence-hurdle reframe of the served
target (Bernoulli/cloglog on per-bin presence, same kernels + `log E`, scored with Brier/log-loss
ALONGSIDE the count deviance). Score through `block_cv` (write_outputs=False), nested-CV lambda inside
each fold. Report per-fold CV-skill + calibration + the pooling factor. GO/NO-GO + PATCH-SPEC. Honest
note: shrinkage biases published kernel CURVES toward flat (predictive objects, not unbiased shapes).
No convergence edit, no served write, no commit.

## TA3 -- AIS-derived effort/noise term in log E

Produce `.../graduation/TA3_ais_effort.md`. Read S2 (rank 1, the effort/exposure classing). Source
NOAA Marine Cadastre AIS (AccessAIS clip-and-ship / bulk GeoParquet, US side; describe BC-side gap),
build a per-station, per-time-bin vessel-traffic / proximity-noise index, and enter it as an
**effort/exposure** term in `log E` (B.2 -- NOT a presence kernel; vessel noise lowers detectability,
it is not laundered into presence). Re-score the existing kernels with the cleaner `log E` through
`block_cv` (write_outputs=False) and report the skill delta + whether `k_diel`/`k_season` get cleaner.
GO/NO-GO + PATCH-SPEC + provenance/license. No convergence edit, no served write, no commit.

## TA4 -- in-repo derived covariates (F1 + A1, with the A3 control)

Produce `.../graduation/TA4_inrepo_covariates.md`. Read M3 (F1 lunar x diel; A1 distance-to-slack/
max-flow; A3 +1-harmonic control). Build F1 and A1 from in-repo signals only (lunar + diel in
`design.py`; the harmonic tide in `tide_harmonic.py`). Fit jointly with the existing kernels and report
the MARGINAL fold-stable CV-skill of each vs the A3 "+1 tide harmonic" control (so a gain is not just
what one more harmonic buys). write_outputs=False. GO/NO-GO + PATCH-SPEC. Expect small effects; the
value is a clean honest read on whether any squeezed nonlinearity survives the 5-fold CV. No
convergence edit, no served write, no commit.

## TA5 -- physics shape priors on existing kernels

Produce `.../graduation/TA5_shape_priors.md`. Read M2 (rank 3). Add soft physics priors (monotonic
dose-response where CALIBRATION_STUDIES motivates it, smoothness penalties) to the EXISTING kernels as
a variance reducer (not added flexibility). Score through `block_cv` (write_outputs=False): report the
effect on per-fold CV-skill + calibration + kernel-curve stability. GO/NO-GO + PATCH-SPEC. No
convergence edit, no served write, no commit.

---

# WAVE TB -- ground new independent observation (the +0.144 lever)

## TB1 -- Port Townsend + Bush Point (OrcaHello), widened region gate

Produce `research/signal_modeling/graduation/TB1_port_townsend_bush_point.md`. Read S1 (ranks 1-2) +
`research/forward/G1_ingest_deploy.md` (the W6 reviewed-outcome ingest pattern) +
`src/aws_backend/ingest_multistation.py` + `src/aws_backend/geo_region.py` (`SAN_JUAN_BOUNDS`). Design
a DRY-RUN re-fetch of OrcaHello reviewed-outcomes for Port Townsend + Bush Point with the region gate
widened to Admiralty Inlet, build per-node cache indexes, and ESTIMATE net-new SRKW presence-days the
current 4-station universe lacks (these are absent from the cache, so unlike W6 they are new analysis
observations). Deliver: the dry-run net-new estimate + a `log E` effort plan that encodes Bush Point's
documented outages + a runbook + a REGION-EXPANSION DECISION MEMO (out-of-box nodes; Bigg's-confound
caveat; cross-station consistency risk) for the operator. NO production fetch-that-writes, NO ingest,
NO commit. The actual fetch/ingest/region expansion is a separate operator-gated step.

## TB2 -- SST-front gradient covariate

Produce `.../graduation/TB2_sst_front.md`. Read S2 (rank 2) + M3 (C1). Specify sourcing MUR SST
(`jplMURSST41`, ERDDAP/PO.DAAC; VIIRS L2P for sharper fronts), computing `|grad SST|` + distance-to-
front near the station cluster per day, orthogonalizing against `k_season` (absolute SST is seasonal;
the gradient is the independent signal). If feasible without a production write, dry-run the incremental
fold-stable CV-skill of the front covariate (write_outputs=False); else deliver the construction recipe
+ an expected-skill band + the patch-spec. GO/NO-GO + provenance/license. No convergence edit, no
served write, no commit.

## TB3 -- real Albion feed refresh + run-anomaly covariate

Produce `.../graduation/TB3_albion_anomaly.md`. Read M3 (D1) + `research/forward/G3_l3_grounding.md`
(the live 2026 Albion fetch design via aimez EC2; the L3 decision bar) + `src/aws_backend/sources/
salmon.py`. Specify the live-feed refresh runbook (EC2 `i-04a649f91274e9fce`; overwrite-in-place
`fos2026.csv`; keep `PREREG_*` frozen) and the run-ANOMALY construction (run minus day-of-year
climatology, to break season collinearity) with the pre-registered out-of-sample lag. Re-state, per
G3, that L3's binding constraint is summer PRESENCE-DAYS (TB1), not the feed, so D1 stays WITHHELD on
the climatology placeholder and the L3 result stays WITHHELD. Deliver runbook + anomaly recipe +
expected-skill band + go/no-go. No production fetch-that-writes here, no convergence edit, no commit.

## TB4 -- ONC / JASCO Boundary Pass (ECHO published dataset)

Produce `.../graduation/TB4_onc_boundary_pass.md`. Read S1 (rank 3, group C). Specify extracting
per-day SRKW-present events from the published annotated ONC/JASCO ECHO dataset (Sci. Data 2025, DOI
10.1038/s41597-025-05281-5) and/or the ONC Oceans 3.0 API, mapping to `acoustic_detections`
(`station: "boundary_pass"`), attaching the deployment duty cycle as `log E` effort (bottom-mounted,
duty-cycled). Assess independence (independent operator + detector + corridor) and the extraction
effort. Deliver: presence-day extraction plan + effort model + runbook + independence/go-no-go. No
production write, no commit.

## TB5 -- SalishSeaCast subtidal currents + shear

Produce `.../graduation/TB5_salishseacast_currents.md`. Read S2 (rank 3) + M3 (B1). Specify pulling
SalishSeaCast NEMO v21-11 surface velocity (ERDDAP griddap `ubcSSg3DPhysicsFields1hV21-11` /
`ubcSSfDepthAvgdCurrents1h`), REMOVING the tidal band (raw currents are `k_tide`; only the subtidal
residual + shear/convergence/Okubo-Weiss is admissible), and sampling at the station footprints.
Deliver the de-tided recipe + provenance + an HONEST conditional-payoff assessment (the spatial front
leverage is damped until presence is spatially resolved -> depends on TB1/TB4 nodes). GO/NO-GO +
patch-spec. No production write, no commit.

---

# WAVE DE -- dead-end drift audit (READ-ONLY)

Each DE lane is read-only: it cites concrete files/lines/symbols, classifies drift, and RECOMMENDS
remediation -- it applies no edit and commits nothing. Preserve the one allowed nuance: self-exciting
Hawkes is a NO-GO as a served-skill method but a GO as the event-level GOF DIAGNOSTIC (and it justifies
the bin-level timing gate); do not recommend deleting the diagnostic. The adjudicated dead-end set
(from SYN section 2): full PINN; reservoir/ESN; delay-embedding/EDM forecasting; neural TPPs;
SDE/diffusion movement models; Hawkes-as-skill; GP-modulated intensity / spatial LGCP at current N;
synthetic data augmentation; NB->ZI/hurdle count upgrade; CUTI/BEUTI upwelling (coverage); HF-radar
currents (shadow); bathymetry/terrain credited on the temporal gate.

## DE1 -- text drift (methodology + charter prose)

Produce `research/signal_modeling/graduation/DE1_text_drift.md`. Audit `docs/methodology/**`, the
`.cca/catalogue/**` charter/handoff prose, and READMEs for any place where an adjudicated dead-end is
presented as a live/recommended/aspirational path WITHOUT the now-established caveat. Deliver a register:
file -> exact quote -> why it is now a drift source (cite the SYN/M-doc verdict) -> recommended edit
(add caveat / reclassify / remove). Prioritize the highest drift-risk items. Read-only; no edit, no
commit.

## DE2 -- method drift (code + methods)

Produce `.../graduation/DE2_method_drift.md`. Audit `modeling/**` and `src/aws_backend/**` for any
dead-end method that is implemented, wired, or at risk of LEAKING into the served path. Specifically
check: is the Hawkes term kept OUT of `_station_intensity_fn` / the served intensity (it must be a
diagnostic only)? Any ZI/hurdle-count, GP/LGCP, synthetic-augmentation, CUTI/BEUTI, or HF-radar code
present and reachable from serving? Any terrain feature entering a TEMPORAL kernel rather than
`s_space`? Deliver a register: symbol/path -> current behavior -> drift/leak risk -> recommended
remediation (guard, isolate, annotate, or remove). Read-only; no edit, no commit.

## DE3 -- strategy drift (operator-facing)

Produce `.../graduation/DE3_strategy_drift.md`. Audit `.../20260627_orcast-handoff/ORCHESTRATOR_NOTES.md`,
the handoff charters, and any PIML/strategy prose for places that still steer toward a dead-end (e.g. a
full-PINN aspiration, an unconditioned LGCP-backbone recommendation, "more prey series" framing that G3
refutes) without the adjudicated caveat. Deliver a register: where -> what it recommends -> why it is
now a drift source -> recommended caveat/edit. Read-only; no edit, no commit.

---

Return contract (every subagent): the doc path; the measured numbers or register; the GO/NO-GO or
remediation recommendation; explicit confirmation that nothing was deployed, fetched-to-write,
promoted, or committed and effective confidence stays 0.0. TA/TB additionally return a PATCH-SPEC for
the later single-editor integrate. DE returns a prioritized remediation list.

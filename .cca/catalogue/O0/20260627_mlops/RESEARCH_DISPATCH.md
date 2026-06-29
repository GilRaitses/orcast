# Research dispatch, L2/L3 push research waveset

Status: READY. NOT launched. Launch is the next operator gate. Model: inherit (all six).
Six parallel research agents, investigation-first, disjoint findings docs, no convergence-file
edits, any fit under refit-safety (`fk._maybe_write_s3 = lambda: None`, `write_outputs=False`), no
production store/model write, no confidence promotion, no agent commits. An honest "no gain" is a
valid result (B.3).

Shared context (every agent prompt embeds this):
- Charter: `.cca/catalogue/O0/20260627_mlops/RESEARCH_CHARTER.md`. Locked decisions:
  `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B. Methodology:
  `docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/CALIBRATION_STUDIES.md`.
- Read the W1/W2/W3 results in `.cca/catalogue/O0/20260627_mlops/STEP_LOG.md` and reuse, read-only,
  the existing studies: `modeling/studies/salmon_lag.py`, `time_rescaling_diag.py`,
  `cross_station_consistency.py`, and `modeling/studies/common.py` (`load_orcahello_index`,
  `STATION_COORDS`). Do not edit any of them.
- Blocker map (grounded): L2 time-rescaling WITHHELD = detection burstiness (NOT effort/grid/kernels,
  NOT data volume) -> ungated modeling fix; L2 cross-station NOT met = per-station sample size ->
  gated 3-node production ingest; L3 WITHHELD = real stock-aligned Albion feed wired all years
  2020-2026 but the binary-presence lag scan does not beat the null (best lag +20 d, r 0.076,
  p 0.394).
- Repo: `/Users/gilraitses/orcast`. Modeling pipeline + data/models local-only/untracked (B.6); heavy
  fits/experiments under `.venv-modeling`, stdlib studies/gate under system python3, backend `.venv`.
- AWS store (B.4): bucket `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, `us-west-2`.
  External feeds DNS-blocked locally are reachable from the aimez EC2 (`i-04a649f91274e9fce`,
  `ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177`; see `WIRING-salmon-albion.md`).
- Convergence files (DO NOT EDIT): `modeling/fit_kernels.py`, `modeling/studies/level2_multistation.py`,
  `modeling/studies/salmon_lag.py`, `src/aws_backend/sources/salmon.py`,
  `src/aws_backend/ingest_timeseries.py`.
- Own ONLY your `research/<topic>.md` (+ an optional `modeling/studies/reports/<topic>.json` if you
  run a study). Return the findings doc path, key MEASURED numbers, a ranked recommendation, risks.
  No commit.

---

## Agent RA -- L3 response variable: counts vs binary presence

You are research agent RA. [Embed shared context.]

YOUR TASK: own `.cca/catalogue/O0/20260627_mlops/research/L3_response_variable.md`. The L3 lag scan
(`salmon_lag.py`) correlates BINARY daily presence (1 if any detection that day) with the lagged
daily Albion run index, which discards count magnitude and saturates on busy days. Investigate
whether the response variable is the problem:
- daily detection COUNTS, and counts per effort (rate), vs the lagged run index (reuse the lag-scan
  + circular-shift null machinery read-only from `salmon_lag.py`);
- a count GLM: NB/Poisson regression of daily counts on the lagged run index (and a season term),
  reporting coefficient, deviance skill, and a permutation/null comparison;
- whether any of these beat the null where binary presence did not (p<0.05), honestly.

DELIVERABLE: the findings doc with measured numbers (best lag, effect, p for each formulation) and a
recommendation on whether a counts-based L3 test is worth wiring. Optional small report JSON.

VALIDATION: run under `.venv-modeling` (refit-safety on). Report real numbers. No convergence-file
edits, no promotion, no commit.

---

## Agent RB -- L3 conditioning: season / per-station / SRKW window

You are research agent RB. [Embed shared context.]

YOUR TASK: own `.cca/catalogue/O0/20260627_mlops/research/L3_conditioning.md`. Test whether
conditioning sharpens the salmon alignment:
- restrict the scan to the Albion run / summer season (drop the off-season zeros that dilute the
  pooled correlation), and report the in-season lag/correlation/p;
- score per-station (haro_strait, orcasound_lab, andrews_bay, north_san_juan_channel) rather than
  pooled, and report which stations show any alignment;
- condition on the SRKW summer presence window and report the change.
Reuse `salmon_lag.py` functions read-only.

DELIVERABLE: findings doc with measured numbers and a recommendation. Optional report JSON.

VALIDATION: `.venv-modeling`, refit-safety on, real numbers, no promotion, no commit.

---

## Agent RC -- time-of-day + temperature/SST feasibility

You are research agent RC. [Embed shared context.]

YOUR TASK: own `.cca/catalogue/O0/20260627_mlops/research/L3_diel_temperature.md`. Two parts:
1. Time-of-day: test whether conditioning presence on the diel-active window (the fitted `k_diel`
   active hours) changes the salmon-lag signal, or whether time-of-day is irrelevant at the
   daily/seasonal salmon timescale (report honestly; likely an L1/L2 concern).
2. Temperature / SST: survey water-temperature sources for the region/period (NOAA SST / CO-OPS water
   temperature, NDBC buoy water temp; check the existing `src/aws_backend/sources/noaa.py` and the S3
   env streams) for coverage over the acoustic window. CLASSIFY temperature's honest role per B.2:
   prey/habitat effect modifier for `s_space`/`k_salmon` vs a detectability/effort term at Level 0.
   Do a small data-availability spike only (use the aimez EC2 if a source is DNS-blocked locally). Do
   NOT claim temperature as an animal kernel without justification.

DELIVERABLE: findings doc with coverage findings, the honest role classification, and a go/no-go on a
temperature feasibility spike. Optional report JSON.

VALIDATION: real coverage numbers; no promotion; no commit.

---

## Agent RD -- L2 burstiness modeling (the time-rescaling fix)

You are research agent RD. [Embed shared context.]

YOUR TASK: own `.cca/catalogue/O0/20260627_mlops/research/L2_burstiness_timing.md`. The L2
time-rescaling blocker is detection burstiness (W1 `time_rescaling_diag.json`: pooled KS p=0, a
constant-rate Poisson fails identically, 63-91% of detections within 6 min of the prior). Investigate
the ungated modeling fixes:
- self-exciting (Hawkes) / refractory terms, and bin-level GOF (the held-out NB PIT already
  covers count overdispersion) as alternatives to event-level Exp(1) rescaling. NOTE (2026-06-27,
  per M1/SYN): "hurdle" here means the onset-dedup / bin-level timing DIAGNOSTIC only -- NOT a
  NB->ZI/hurdle COUNT upgrade (a dead-end); and Hawkes is retained as an event-level GOF diagnostic
  only, never served intensity. The adjudicated fix is the bin-level timing gate;
- prototype the most promising one against the cached multi-station data (read-only reuse of
  `time_rescaling_diag.py` and the fit), and report whether it makes the timing gate pass HONESTLY;
- give a concrete wiring spec (where it would attach in the conditional intensity / GOF) for a future
  build wave -- do NOT apply it to the convergence files.

DELIVERABLE: findings doc with the measured before/after KS (or bin-level GOF) numbers, the chosen
fix, and the wiring spec. Optional report JSON.

VALIDATION: `.venv-modeling`, refit-safety on (no S3/model write); if nothing passes honestly, say so
(withheld with the reason). No promotion, no commit.

---

## Agent RE -- L2 data-volume dependency (the gated cross-station blocker)

You are research agent RE. [Embed shared context.]

YOUR TASK: own `.cca/catalogue/O0/20260627_mlops/research/L2_data_volume.md`. The cross-station
consistency blocker is per-station sample size (W1/W2 `cross_station_consistency.json`: within-station
split-half reliability below 0.5 for diel/tide/lunar). Quantify the dependency:
- a power analysis: detections-per-station needed for split-half reliability >= 0.5 per kernel
  (subsample the dense stations to estimate the curve);
- what the operator/deploy-gated 3-node production ingest would add (use the dry-run counts from
  `ingest_multistation.py` / `WIRING-ingest.md`: orcasound_lab ~1029, andrews_bay ~265,
  north_san_juan_channel ~34);
- whether deeper OrcaHello history per node is reachable (reviewed-outcome endpoints + cache, B.9)
  and would materially help.
Confirm or refute that the 3-node ingest is the binding cross-station dependency.

DELIVERABLE: findings doc with the power curve, the projected post-ingest reliability, and a clear
statement of what is gated vs reachable now. Optional report JSON.

VALIDATION: `.venv-modeling`, refit-safety on, real numbers, no promotion, no commit.

---

## Agent RF -- synthesis + ranked action plan

You are research agent RF. [Embed shared context.]

YOUR TASK: own `.cca/catalogue/O0/20260627_mlops/research/SYNTHESIS_L2_L3.md`. After RA-RE land (read
their findings docs), consolidate into a ranked, honest action plan for L2 and L3:
- separate UNGATED moves (do now) from operator/deploy-gated moves (need the 3-node ingest or a
  deploy);
- for each, give expected payoff and the cheapest next experiment;
- name which findings (if any) are strong enough to graduate to a real W4 build/integrate wave, and
  which honestly dead-end (report as withheld).
Do not promote confidence; this is a decision aid for the operator.

DELIVERABLE: the synthesis doc with the ranked plan. RF runs last (depends on RA-RE).

VALIDATION: cite RA-RE measured numbers faithfully; no promotion; no commit.

---

## Wave exit (orchestrator, operator-gated)

On completion the orchestrator collects the six findings docs, confirms RF's ranked plan, refreshes
the `wave_shape.yml` `research_dispatch` status + `STEP_LOG.md`, and (only on an explicit operator
ask) does one surgical commit. No confidence promotion. The operator decides which findings graduate
to a build/integrate wave (a future W4).

# L2/L3 push research waveset charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (MLM + MLO)
Home: `.cca/catalogue/O0/20260627_mlops/`
Authority above this doc: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B
(locked decisions). Sibling docs: `WAVESET_CHARTER.md` (the frontier execution model),
`wave_shape.yml` (frontier_dispatch W1-W3, now W1/W2 done, W3 in-progress).

This charters a RESEARCH waveset that investigates concrete ways to push L3 and L2 off their honest
blockers. It is investigation-first: each agent produces a findings doc with measured numbers and a
ranked recommendation, plus at most a small local experiment under the refit-safety rules. It does
NOT change served confidence and does NOT promote (B.1). Some avenues may honestly conclude "no
gain"; that is a valid result (B.3).

## A. Why this wave (the blocker map, grounded in W1/W2)

Effective confidence is 0%. The honest blockers, with their true dependencies:

- L2 time-rescaling: WITHHELD because the detection stream is bursty (pooled KS p=0; a constant-rate
  Poisson fails identically; 63-91% of detections within 6 min of the prior one). Effort is a no-op
  (uptime stream disjoint from detections). This is a MODELING problem (self-excitation / refractory
  / bin-level GOF), NOT data volume, so it is attackable NOW, ungated.
- L2 cross-station consistency: NOT met because per-station PSTHs are below their own split-half
  reliability (sparse-count artifact, not heterogeneity). This IS data-volume bound: the binding
  dependency is the operator/deploy-gated 3-node production `acoustic_detections` ingest (and
  possibly deeper OrcaHello history).
- L3 k_salmon: WITHHELD. The real, complete, stock-aligned Albion (Fraser-summer Chinook) feed is
  now wired for all detection years 2020-2026, and the lag scan still does not beat the permutation
  null (best lag +20 d, r 0.076, p 0.394). The current test is binary daily presence vs a daily run
  index, pooled across years; it discards count magnitude and mixes in-season and off-season days.

So "the L2 dependency remains the gated 3-node ingest" is true for cross-station consistency only;
time-rescaling and the entire L3 reformulation can advance without it.

## B. Locked constraints carried in (do not reopen; HANDOFF_CHARTER section B)

1. No confidence promotion in any wave; promotion is a gate pass + a recorded supervisor decision.
2. Effort-bias design: temporal kernels from acoustic detections + `log E`; visual is validation +
   `s_space`. Weather (wind/waves/temperature) and AIS enter as detector-QC / effort terms at Level
   0, NOT as animal kernels (FORECAST_KERNELS.md). Any temperature avenue must respect this: SST is
   investigated as a prey/habitat effect modifier and a detectability/effort term, not smuggled in
   as an animal kernel without justification.
3. Coverage honesty: insufficient coverage reports withheld; an agent may conclude "no gain".
4. AWS store (B.4): bucket `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, `us-west-2`.
5. Refit safety (B.5): any fit sets `fk._maybe_write_s3 = lambda: None` and `write_outputs=False`.
   No production store or model-bucket write.
6. Repo layout (B.6): the `modeling/` fit pipeline + `data/models/` are local-only/untracked; only
   `modeling/studies/**` + reports and `modeling/tide_harmonic.py` are tracked. Research findings
   docs live under `.cca/catalogue/O0/20260627_mlops/research/` (tracked when committed).
7. Environments (B.7): heavy fits/experiments `.venv-modeling`; stdlib studies/gate system python3;
   backend `.venv`. External feeds via the aimez EC2 when DNS-blocked locally (see
   `WIRING-salmon-albion.md`).
8. Write policy (B.10): no commit/push without an explicit operator ask; surgical staging.

## C. Research questions (operator-posed + derived)

L3 (push the salmon test):
- Q1 Response variable. Does using daily detection COUNTS (or rate per effort, or a count GLM:
  NB/Poisson of daily counts on lagged run index) recover signal that the binary presence lag scan
  discards? Binary presence throws away magnitude and saturates on busy days.
- Q2 Conditioning. Does restricting to the run/summer season (and removing off-season zeros), and/or
  scoring per-station rather than pooled, sharpen the salmon alignment? Does the lag/correlation
  change when conditioned on the SRKW summer presence window?
- Q3 Time-of-day conditioning. Does conditioning presence on diel-active hours (the fitted `k_diel`
  active window) change the salmon-lag signal, or is time-of-day irrelevant at the salmon
  daily/seasonal timescale (likely an L1/L2 concern, but tested honestly)?

L2 (more ammo):
- Q4 Burstiness modeling (the time-rescaling fix). Does a self-exciting (Hawkes) / refractory /
  hurdle term, or a bin-level GOF decision, make the timing gate pass honestly on the multi-station
  data? This is the ungated path to the time-rescaling blocker.
- Q5 Temperature / SST. Is water temperature a defensible covariate, and in which role (prey/habitat
  effect modifier for `s_space`/`k_salmon`, or a detectability/effort term at L0 per B.2)? What
  sources (NOAA SST, NDBC water temp, buoy series) cover the region/period, and is a feasibility
  spike worth it?
- Q6 Data-volume dependency. Quantify how much the cross-station blocker needs: detections-per-
  station for split-half reliability >= 0.5, what the 3-node production ingest would add, and whether
  deeper OrcaHello history (more years per node) is reachable and would help. Confirm or refute that
  the 3-node ingest is the binding cross-station dependency.

Synthesis:
- Q7 Consolidate Q1-Q6 into a ranked, honest action list for L2 and L3: what is ungated vs
  operator/deploy-gated, expected payoff, and the cheapest next experiment for each.

## D. Execution model (research variant; same collision discipline)

1. One findings doc per agent under `.cca/catalogue/O0/20260627_mlops/research/<topic>.md` (+ an
   optional small report JSON under `modeling/studies/reports/` only if the agent runs a study).
   No two agents write the same file.
2. No agent edits a convergence file (`modeling/fit_kernels.py`,
   `modeling/studies/level2_multistation.py`, `src/aws_backend/sources/salmon.py`,
   `src/aws_backend/ingest_timeseries.py`, `modeling/studies/salmon_lag.py`). Experiments are
   standalone scratch scripts or read-only reuse of existing study functions; proposed code changes
   are written as specs, not applied.
3. Any fit/experiment runs with the S3 upload disabled and `write_outputs=False`; no production store
   write; no concurrent heavy fit (serialize S3 reads or reuse a shared fit report).
4. No confidence promotion as a side effect. An honest "no gain / withheld" is a valid finding.
5. No agent commits or pushes; each returns its findings doc + measured numbers + a recommendation.
   The orchestrator does one integration step at wave end, commit only on an explicit operator ask.

## E. Research agents (6 parallel; investigation-first)

- RA, L3 response variable (counts vs binary). Owns `research/L3_response_variable.md`. Re-run the
  lag relationship using daily COUNTS and rate-per-effort, and a count GLM (NB/Poisson of daily
  counts on lagged Albion run index) with the same circular-shift null. Reuse `salmon_lag.py`
  functions read-only; do not edit it. Report whether counts beat the null where binary did not.
- RB, L3 conditioning (season / per-station / SRKW window). Owns `research/L3_conditioning.md`.
  Restrict to the run/summer season (drop off-season zeros), score per-station, and condition on the
  SRKW summer presence window; report how lag/correlation/p change.
- RC, time-of-day + temperature/SST feasibility. Owns `research/L3_diel_temperature.md`. Test diel-
  window conditioning of the salmon signal; survey SST/water-temp sources (NOAA SST, NDBC water
  temp) for region/period coverage and classify temperature's honest role per B.2 (effect modifier
  vs effort term), with a small data-availability spike (use the aimez EC2 if a source is DNS-blocked
  locally). No animal-kernel claim without justification.
- RD, L2 burstiness modeling (time-rescaling fix). Owns `research/L2_burstiness_timing.md`. Survey
  and prototype the self-excitation/refractory/hurdle or bin-level GOF options against the cached
  multi-station data (read-only reuse of `time_rescaling_diag.py` / the fit); report whether any make
  the timing gate pass honestly, with a concrete wiring spec for the chosen one. Refit-safety on.
- RE, L2 data-volume dependency. Owns `research/L2_data_volume.md`. Power analysis: detections-per-
  station needed for cross-station split-half reliability >= 0.5; what the 3-node production ingest
  adds; whether deeper OrcaHello history per node is reachable (reviewed-outcome endpoints + cache,
  B.9) and would help. Confirm/refute the 3-node ingest as the binding cross-station dependency.
- RF, synthesis + ranked action plan. Owns `research/SYNTHESIS_L2_L3.md`. Consolidate RA-RE into a
  ranked, honest plan separating ungated vs operator/deploy-gated moves, expected payoff, and the
  cheapest next experiment for each. Names what (if anything) is worth promoting to a real W4
  build/integrate wave.

Wave gate: each findings doc lands with measured numbers and a recommendation; RF produces the
ranked plan. No promotion; the operator decides which findings graduate to a build wave.

## F. Per-agent prompt skeleton

```
You are research agent [LETTER] in the orcast ML-ops L2/L3 push research waveset.
Charter: .cca/catalogue/O0/20260627_mlops/RESEARCH_CHARTER.md. Locked decisions:
HANDOFF_CHARTER.md section B. Read W1/W2/W3 results in STEP_LOG.md and the existing studies
(modeling/studies/{salmon_lag,time_rescaling_diag,cross_station_consistency}.py) read-only.

GOAL: investigate [question] and return a findings doc with MEASURED numbers + a ranked
recommendation. Investigation-first; at most a small local experiment.

RULES: no convergence-file edits; any fit uses fk._maybe_write_s3 = lambda: None + write_outputs=
False; no production store/model write; no confidence promotion; an honest "no gain" is valid;
commit nothing. External feeds that are DNS-blocked locally: use the aimez EC2 (WIRING-salmon-albion.md).

OWN ONLY: research/<topic>.md (+ an optional modeling/studies/reports/<topic>.json if you run a study).
RETURN: the findings doc path, the key measured numbers, the recommendation, risks. No commit.
```

## G. Gates / return contract

Operator gates: launch this research wave; promote any finding to a build/integrate wave; any commit
or push; any confidence promotion (unchanged: gate pass + supervisor decision). Per-agent return:
findings doc + measured numbers + recommendation, no commit. Wave exit: RF's ranked plan + one
orchestrator integration step (commit only on explicit operator ask).

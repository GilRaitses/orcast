# W4 build dispatch (graduate research findings)

Status: READY. NOT launched. Launch is the next operator gate. Model: inherit (both).
Two integrators, single convergence-file editor per file, disjoint files run in parallel. Validate
with the stdlib gate + one local memory-store refit (S3 upload disabled, `write_outputs=False`); no
production store/model write; no concurrent heavy fit; NO confidence promotion; no agent commits.

Shared context (both prompts embed this):
- Charter: `.cca/catalogue/O0/20260627_mlops/W4_BUILD_CHARTER.md`. Research inputs:
  `.cca/catalogue/O0/20260627_mlops/research/` (esp. `SYNTHESIS_L2_L3.md`,
  `L2_data_volume.md`, `L2_burstiness_timing.md`, `L3_conditioning.md`, `L3_response_variable.md`).
  Locked decisions: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
- Repo: `/Users/gilraitses/orcast`. The `modeling/` fit pipeline + `data/models/` are LOCAL-ONLY /
  untracked (B.6); only `modeling/studies/**` + reports and `tide_harmonic.py` are tracked. Heavy
  fits/studies under `.venv-modeling`; stdlib gate under system python3.
- AWS store (B.4): bucket `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, `us-west-2`.
  Reference safe-fit pattern: `modeling/studies/level2_multistation.py` (builds the 4-station memory
  store, sets `fk._maybe_write_s3 = lambda: None`, runs `write_outputs=False`).
- HONESTY (B.1): nothing in this wave may raise `effective_confidence`. The bin-level timing gate
  (item 3) is written behind a default-OFF flag and is adopted only by a recorded supervisor
  decision; do not flip it on. After every change, `tools/waves/run-gate.sh mlops-gate` must stay
  green with served confidence 0.0 consistent with the ladder.

---

## Integrator M -- modeling (items 1 + 3; SOLE editor of fit_kernels.py + cross_station_consistency.py)

You are the MODELING INTEGRATOR in W4. [Embed shared context.]

ITEM 1 (UNGATED, APPLY) -- cross-station consistency re-score. Per RE/RB, the 24-bin scoring is too
fine for the data volume. Update `_cross_station_consistency` in `modeling/fit_kernels.py` and the
standalone `modeling/studies/cross_station_consistency.py` to score at 8-12 PSTH bins with a minimum
per-bin count, add partial pooling and burst-dedup to encounter onsets, and report within-station
split-half reliability as the ceiling alongside the cross-station correlation. Expected (verify):
diel split-half ~0.08 -> ~0.42 at 12 bins; lunar clears 0.5 on the dense stations; tide stays
unstable -> keep it flagged, do not force it. Re-run the multi-station fit (memory store, upload
disabled, `write_outputs=False`) and update `modeling/studies/reports/level2_multistation.json` +
`cross_station_consistency.json` honestly. This is a reproducibility-criterion fix; it does NOT by
itself promote confidence.

ITEM 3 (GATED, WRITE-ONLY, DO NOT ADOPT) -- bin-level timing gate + Hawkes diagnostic. Per RD, add:
(a) a Hawkes self-exciting event-level GOF DIAGNOSTIC to `_time_rescaling_report` (report the
compensator KS + branching ratio; keep the event-level Exp(1) verdict WITHHELD); (b) a BIN-LEVEL
timing-gate definition (held-out NB PIT calibrated AND CV mean-deviance-skill > climatology) behind
an explicit flag that DEFAULTS OFF in `_confidence_from_gates`, so the served gate and
`effective_confidence` are UNCHANGED (stay 0.0). Write a clear spec comment that adoption is a
recorded supervisor decision (B.1), framed honestly as "event-level Exp(1) is inappropriate for a
detector-chatter stream", and that the CV-skill pairing is load-bearing (NB alpha makes the PIT
near-automatic alone). DO NOT flip the flag on; DO NOT change served confidence.

VALIDATION: run `tools/waves/run-gate.sh mlops-gate` (system python3) -> must stay green, served
confidence 0.0. Report the measured consistency before/after, the Hawkes branching ratio + bin-level
gate state (OFF), and confirm confidence unchanged.

COLLISION-AVOIDANCE: you are the sole editor of `modeling/fit_kernels.py` and
`modeling/studies/cross_station_consistency.py` this wave; do NOT touch `modeling/studies/salmon_lag.py`
(the study integrator owns it) or `src/aws_backend/**`. Commit nothing.

RETURN: diffs/specs, measured consistency numbers, Hawkes + bin-level-gate state (OFF, confidence
0.0), mlops-gate result, risks. No commit.

---

## Integrator S -- study (item 2; SOLE editor of salmon_lag.py)

You are the STUDY INTEGRATOR in W4. [Embed shared context.]

ITEM 2 (UNGATED, APPLY) -- pre-registered SRKW-summer L3 conditioning + held-out year. Per RB/RA,
add to `modeling/studies/salmon_lag.py` a PRE-REGISTERED, summer-conditioned scan on the real Albion
feed: fix the window (Jun-Sep) and the lag sign (run leads presence, +lag) BEFORE scanning, restrict
to that window, and add a held-out-year evaluation (fit/choose nothing on the held-out year; report
its out-of-sample correlation/p). Keep the existing full-span scan as-is; add the conditioned result
as an explicit, separately-labeled section so the exploratory nature is clear (window multiplicity,
36-63 summer presence-days). Honor the existing stock-alignment guard (`_STOCK_ALIGNED_SOURCES`) and
`real_feed_only`. L3 verdict: stays WITHHELD unless the held-out year ALSO beats the null at the
pre-registered window/lag; do not promote. Update `modeling/studies/reports/salmon_lag.json` with the
pre-registered + held-out result.

Optional: re-run RA's counts response variable on the Jun-Sep conditioned subset only (RA owed a
summer re-test); report whether counts help within the window. Keep it informational.

VALIDATION: run under `.venv` (salmon_lag imports the salmon adapter which needs requests) or system
python3 if the cached Albion suffices; report the pre-registered Jun-Sep result and the held-out-year
out-of-sample verdict. Confirm L3 stays WITHHELD (or, if the held-out year holds, flag it for an
operator/supervisor decision -- do NOT self-promote).

COLLISION-AVOIDANCE: sole editor of `modeling/studies/salmon_lag.py`; do NOT touch
`modeling/fit_kernels.py`, `cross_station_consistency.py`, or `src/aws_backend/**`. Commit nothing.

RETURN: the pre-registered + held-out L3 numbers, the verdict (withheld vs flag-for-decision), the
optional summer counts result, risks. No commit.

---

## W4 exit (orchestrator, operator-gated)

UNGATED exit: items 1 + 2 landed, `mlops-gate` green, served confidence still 0.0, the bin-level
timing gate present but OFF. The orchestrator collects the diffs, refreshes `wave_shape.yml` + the
STEP_LOG, and (only on an explicit operator ask) does one surgical commit. CONFIDENCE gate: prepare
the supervisor-decision packet for item 3 (the bin-level timing gate); `effective_confidence` rises
only on that recorded decision (B.1).

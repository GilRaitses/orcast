# Wave 1 dispatch, ML-ops frontier waveset

Status: READY. NOT launched. Launch is the next operator gate. Model: inherit (all five).
Five parallel agents, disjoint scopes, none edits a convergence file
(`modeling/fit_kernels.py`, `modeling/studies/level2_multistation.py`,
`src/aws_backend/sources/salmon.py`, `src/aws_backend/ingest_timeseries.py`), validation only
(stdlib ladder OR one local memory-store fit with the S3 model-artifact upload disabled and
`write_outputs=False`; backend harness runs), local-only artifacts stay untracked. No commit/push
by any agent; each returns a wiring spec + measured results, and the orchestrator does one
integration step at wave end (also operator-gated).

Shared context (every agent prompt embeds this):
- Charter: `.cca/catalogue/O0/20260627_mlops/WAVESET_CHARTER.md`. Decision record:
  `.cca/catalogue/O0/20260627_mlops/DECISION_RECORD.md`. Locked decisions:
  `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B. Methodology:
  `docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/CALIBRATION_STUDIES.md`.
- GOAL: push Level 2 off 0% effective confidence honestly. The multi-station experiment already
  flips held-out skill positive (+0.078, 4/5 folds) vs the single-station baseline (-0.047); the two
  remaining L2 blockers are (1) time-rescaling GOF fails (pooled KS p=0.0), which points at
  per-station effort / `log E` and the conditional-intensity timing, and (2) cross-station kernel
  consistency is testable but not met (per-kernel PSTH correlations 0.14-0.34, below 0.5). In
  parallel, de-risk the 3-node production ingest and the real Chinook (Albion/DART) feed. No
  confidence promotion in any wave.
- Repo: `/Users/gilraitses/orcast` (git `main`). The `modeling/` fit pipeline (`fit_kernels.py`,
  `design.py`, `estimator.py`, `bases.py`, `tide_phase.py`, `validation/`) and `data/models/` are
  LOCAL-ONLY / untracked (charter B.6); only `modeling/studies/**` + reports and
  `modeling/tide_harmonic.py` are tracked. Heavy fits/studies under `.venv-modeling`; the stdlib
  ladder/gate under system `python3`; backend under `.venv`.
- AWS store (charter B.4): bucket `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, region
  `us-west-2`, NOT the config default. Reproduce a fit with:
  `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2 PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels`.
  acoustic_detections has `haro_strait`; env_currents has `pug1701/1702/1703`.
- Refit safety (charter B.5): set `fk._maybe_write_s3 = lambda: None` and call with
  `write_outputs=False`. Never write the production model bucket or the production store from a Wave
  1 agent. The multi-station study `modeling/studies/level2_multistation.py` already does this and is
  the reference pattern.
- Cached indexes (charter B.9): `.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json`
  (3 nodes: orcasound_lab, andrews_bay, north_san_juan_channel), `orcahello_index.confidence.cache.json`
  (4 nodes with confidence). The OrcaHello history API 403s/SSL-EOFs on heavy paging and returns
  oldest-first; prefer the reviewed-outcome endpoints + the caches.
- Convergence files (DO NOT EDIT this wave): `modeling/fit_kernels.py`,
  `modeling/studies/level2_multistation.py`, `src/aws_backend/sources/salmon.py`,
  `src/aws_backend/ingest_timeseries.py`.
- Honesty (charter B.1-B.3): no confidence promotion as a side effect; report measured results, not
  estimates; if blocked by data, report withheld with the reason rather than faking
  coverage/skill/a kernel. Be explicit about what you verified vs assumed.

---

## Agent A -- Per-station effort / log E model (ROOT CAUSE for time-rescaling)

You are agent A in Wave 1 of the orcast ML-ops frontier waveset.
[Embed shared context above.]

YOUR TASK: own the NEW module `modeling/effort.py` (local-only, untracked like the rest of the fit
pipeline). Build a per-station effort / `log E` model that the conditional intensity can consume so
the time-rescaling timing is effort-corrected. Today `build_design` in `modeling/fit_kernels.py`
sets `df.attrs["effort_assumed_continuous"] = True` when no per-station uptime binds; the
`station_uptime` stream exists in S3 but the effort offset is effectively flat, which is a prime
suspect for the pooled KS p=0.0. Deliver:
- a function that turns the per-station `station_uptime` series (and detection density where uptime
  is missing) into a per-(station, time-bin) effort/exposure and a `log E` offset, with a documented
  fallback when uptime is absent (state it; do not fabricate uptime),
- a pure, testable API the integrator can call from `build_design` / `_station_intensity_fn`
  (e.g. `station_log_effort(uptime, station, grid_times) -> np.ndarray`,
  `exposure_for_bins(...) -> np.ndarray`),
- a short note on how the effort offset changes the per-station conditional intensity used by
  `_time_rescaling_report` (`_station_intensity_fn`).

DELIVERABLES: `modeling/effort.py` + `WIRING-effort.md` telling the modeling integrator exactly how
to wire it into `build_design` (`modeling/design.py`) and `_station_intensity_fn` /
`_time_rescaling_report` (`modeling/fit_kernels.py`): what to import, where, what it replaces.

VALIDATION: one local run under `.venv-modeling` against the S3 store with `_maybe_write_s3`
disabled and `write_outputs=False` (or against the multi-station memory store from
`level2_multistation.py`), showing the per-station `log E` series is non-degenerate and the
exposure is sane. Report the real per-station effort summary.

COLLISION-AVOIDANCE: do NOT edit any convergence file or `modeling/design.py`. Do NOT write the
production store or model bucket. Commit nothing.

RETURN: exported API signatures, the per-station effort summary, the wiring spec, decisions, risks.
No commit.

---

## Agent B -- Time-rescaling diagnostic

You are agent B in Wave 1 of the orcast ML-ops frontier waveset.
[Embed shared context above.]

YOUR TASK: own the NEW file `modeling/studies/time_rescaling_diag.py` + a report under
`modeling/studies/reports/` (e.g. `time_rescaling_diag.json`). Characterize WHY the pooled
time-rescaling KS is p=0.0. Read the existing primitive `modeling/validation/time_rescaling.py`
(`run_time_rescaling`, `time_rescaling_test`) and the per-station intensity construction in
`modeling/fit_kernels.py` `_time_rescaling_report` / `_station_intensity_fn`, but DO NOT edit them.
Produce a diagnostic that isolates the cause among: per-station vs pooled KS (is one station
dragging the pool?), effort sensitivity (rerun with vs without a flat effort offset), grid/bin
resolution (`grid_step` / `bin_hours`), and the conditional-intensity construction (does the
station intensity miss structure). Coordinate with agent A's `log E` model via `WIRING-effort.md`
if ready; otherwise test with the current flat-effort intensity and state that.

DELIVERABLES: the study file + the JSON report (per-station KS table, pooled KS, the sensitivity
findings) + a `recommended-fix` block in the report naming the most likely fix (effort offset,
finer grid, per-station vs pooled scoring) for the Wave 2 integrator.

VALIDATION: run it under `.venv-modeling` against the S3 store (upload disabled, `write_outputs=False`)
or the multi-station memory store. Report the real per-station and pooled KS p-values.

COLLISION-AVOIDANCE: do NOT edit any convergence file or `modeling/validation/time_rescaling.py`.
No production store / model bucket write. Commit nothing.

RETURN: the per-station/pooled KS findings, the recommended fix, risks. No commit.

---

## Agent C -- Cross-station kernel consistency

You are agent C in Wave 1 of the orcast ML-ops frontier waveset.
[Embed shared context above.]

YOUR TASK: own the NEW file `modeling/studies/cross_station_consistency.py` + a report under
`modeling/studies/reports/` (e.g. `cross_station_consistency.json`). The joint fit's
`_cross_station_consistency` (`modeling/fit_kernels.py` ~line 802) reports per-kernel mean PSTH
correlations of 0.14-0.34 across the 4 stations, below the 0.5 bar. Build a standalone study
(mirroring that logic, NOT editing it) that diagnoses the inconsistency: per-kernel, per-station
PSTH curves; which station pairs and which kernels drag the mean correlation down; the effect of
effort normalization (use agent A's `log E` if ready) and of partial pooling across stations
(station random effect / shrinkage). Distinguish genuine station heterogeneity from an effort or
small-sample artifact, honestly.

DELIVERABLES: the study file + the JSON report (per-kernel cross-station correlation matrix,
the worst kernels/stations, the effort-normalized comparison) + a `recommendation` block on whether
and how the 0.5 bar can be cleared (and if it cannot honestly, say so).

VALIDATION: run it under `.venv-modeling` against the multi-station data (the
`level2_multistation.py` memory store is the right input; do not write the production store). Report
the real per-kernel correlations.

COLLISION-AVOIDANCE: do NOT edit any convergence file. No production store / model bucket write.
Commit nothing.

RETURN: the per-kernel cross-station correlations, the recommendation, risks. No commit.

---

## Agent D -- Multi-station production ingest recipe (dry-run only)

You are agent D in Wave 1 of the orcast ML-ops frontier waveset.
[Embed shared context above.]

YOUR TASK: own the NEW module `src/aws_backend/ingest_multistation.py` + `WIRING-ingest.md`. The
production `acoustic_detections` stream has only `haro_strait`; the cached OrcaHello index carries
three more in-region nodes (orcasound_lab, andrews_bay, north_san_juan_channel). Build a recipe +
thin driver that ingests those three nodes into the `acoustic_detections` stream via the
reviewed-outcome endpoints + the cached indexes (charter B.9), reusing the existing
`_put_grouped_by_station` grouping from `src/aws_backend/ingest_timeseries.py` (records keyed by
`record["station"]`). The OrcaHello history API 403s on heavy paging, so prefer
`ingest_acoustic_reviewed_outcomes` + the caches over `fetch_history`.

IMPORTANT: DRY-RUN ONLY this wave. Do NOT write the production store. Validate against the cached
index and/or a `MemoryTimeSeriesStore`, and report the per-station record counts you would write.
The actual production store write is operator/deploy-gated for Wave 2.

DELIVERABLES: `src/aws_backend/ingest_multistation.py` (a callable that takes a store + the cached
index path and groups by station; with a `dry_run=True` default) + `WIRING-ingest.md` telling the
backend integrator how to wire it into `ingest_timeseries.py` and how the deploy-gated production
run is invoked.

VALIDATION: run the dry-run under `.venv` against the cached index; report the per-station counts
(expect roughly orcasound_lab ~1029, andrews_bay ~265, north_san_juan_channel ~34 from the cache,
verify against the actual cache).

COLLISION-AVOIDANCE: do NOT edit `src/aws_backend/ingest_timeseries.py` or any other convergence
file. Do NOT write the production store. Commit nothing.

RETURN: the dry-run per-station counts, the wiring spec, risks. No commit.

---

## Agent E -- Salmon Albion/DART parser validation

You are agent E in Wave 1 of the orcast ML-ops frontier waveset.
[Embed shared context above.]

YOUR TASK: own the NEW file `src/aws_backend/sources/salmon_validation.py` (a validation harness +
captured real payloads). `src/aws_backend/sources/salmon.py` has `_fetch_fraser` (Albion, Fraser
River DFO) and `_fetch_columbia` (DART Bonneville), both marked UNCONFIRMED in the module docstring;
both currently fall through to the climatology placeholder, which keeps L3 withheld. Hit the real
Albion and DART feeds, capture the ACTUAL payload shapes (HTML/CSV/JSON, which vary year to year),
and validate or repair the parse paths (`_parse_daily_payload`, `_row_date`, `_row_value`,
`_extract_rows`) against them. Determine whether a real feed now yields a usable daily Chinook
run-timing index that beats the climatology fallback.

DELIVERABLES: `salmon_validation.py` (the harness + a small captured sample of each real payload) +
a findings note + a patch spec for `salmon.py` (the exact changes to `_fetch_fraser` /
`_fetch_columbia` / the parse helpers). Do NOT edit `salmon.py` this wave (it is a convergence file;
the backend integrator applies the patch in Wave 2).

VALIDATION: run the harness under `.venv` against the live feeds; report whether each feed returned
a parseable daily series, the row count, and a sample of the parsed `{date: value}`. If a feed is
unreachable or unparseable, say so plainly; that leaves L3 withheld (honest), not promoted.

COLLISION-AVOIDANCE: do NOT edit `salmon.py` or any other convergence file. Commit nothing.

RETURN: per-feed parse result (reachable? parseable? row count? beats climatology?), the patch spec
for `salmon.py`, risks. No commit.

---

## Wave 1 exit (orchestrator, operator-gated)

Gate to Wave 2: agents B and C pinpoint the time-rescaling fix and the cross-station path, agent A's
effort module is ready to wire, and agents D and E report honest dry-run / validation findings. On
gate pass, the orchestrator collects the five wiring specs / patch specs, prepares the Wave 2
dispatch (single convergence-file editor per file: modeling integrator on `fit_kernels.py` +
`level2_multistation.py`; backend integrator on `salmon.py` + `ingest_timeseries.py`), and does one
integration step + commit only on an explicit operator ask (B.10). No confidence promotion occurs at
the Wave 1 exit.

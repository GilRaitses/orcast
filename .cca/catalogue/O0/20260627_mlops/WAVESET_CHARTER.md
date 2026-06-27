# ML-ops frontier waveset charter (parallel subagent dispatch)

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (MLM + MLO)
Home: `.cca/catalogue/O0/20260627_mlops/`
Authority above this doc: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B
(the locked decisions). Methodology canon: `docs/methodology/FORECAST_KERNELS.md`,
`docs/methodology/CALIBRATION_STUDIES.md`.

This charter externalizes the locked L2/L3 frontier as a parallel-subagent waveset, in the same
execution model as the terrain-bathymetry project home
(`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`). It is the execution plan that clears the
frontier; the methodology level ladder (M-L0..M-L3 in `MLM_CHARTER.md` / `wave_shape.yml`) stays
the gate definition. W1/W2/W3 here are execution waves, not new levels.

## A. Purpose

Push Level 2 off 0% effective confidence honestly. The breakthrough is already in hand: the
multi-station experiment flips held-out skill positive (+0.078, 4/5 folds) versus the
single-station baseline (-0.047). Two L2 blockers remain, both concrete:

1. Time-rescaling goodness-of-fit fails (pooled KS p=0.0). This points at per-station effort /
   `log E` and the conditional-intensity timing, not the covariate list.
2. Cross-station kernel consistency is testable (4 stations) but not yet met (per-kernel PSTH
   correlations 0.14-0.34, below the 0.5 bar).

In parallel, two disjoint backend tracks de-risk the next steps: productionizing the 3 extra
Orcasound nodes into the `acoustic_detections` stream, and validating the Albion/DART salmon
parsers for a real L3 Chinook feed. No confidence promotion happens in any wave; promotion is a
recorded supervisor decision after a passing gate.

## B. Locked decisions carried in (restated; do not reopen, source HANDOFF_CHARTER section B)

1. Honesty / promotion gate. Effective confidence is 0% and shown with the gate caveat. It rises
   only on a passing gate plus a recorded human decision via
   `src/aws_backend/promotion/supervisor.py`. Never render sharper than the gates earn.
2. Effort-bias design. Temporal kernels come from continuous acoustic detections (effort-stable)
   with an explicit `log E` offset. Visual sightings (OBIS, iNaturalist, community, CAND) are
   validation and `s_space` only, never the temporal-kernel heat. Acoustic presence is not a
   visual encounter; a hydrophone is a fixed position, not a whale GPS fix.
3. Coverage honesty. Insufficient phase/data coverage reports `withheld` with the reason, never a
   fabricated kernel. An agent may legitimately conclude blocked / withheld.
4. AWS store footgun (B.4). The timeseries data is in S3 bucket
   `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, region `us-west-2`, NOT the config
   default `orcast-raw-payloads`. Reproduce any fit with:
   `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2 PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels`.
5. Refit safety (B.5). When refitting against S3, DISABLE the production model-artifact upload
   (`fk._maybe_write_s3 = lambda: None`, or run with `write_outputs=False`). A confidence change
   is a recorded supervisor decision, not a refit side effect.
6. Repo layout (B.6). The `modeling/` fit pipeline (`fit_kernels.py`, `design.py`, `estimator.py`,
   `bases.py`, `tide_phase.py`, `validation/`, ...) and `data/models/` are local-only (untracked).
   Only `modeling/studies/**` (incl. `modeling/studies/reports/*.json`) and `modeling/tide_harmonic.py`
   are tracked. The harmonic-tide integration lives in the local tree; do not expect it on a clean
   checkout.
7. Environments (B.7). `.venv-modeling/bin/python` runs the heavy fit and heavy studies
   (`level2_multistation.py`, `tide_coverage.py`). `modeling/studies/` is otherwise pure stdlib and
   runs `run_studies.py` / the ladder under system `python3`. `.venv` (python3.14) has the backend
   deps.
8. mlops-gate (B.8). Local gate (`tools/waves/run-gate.sh mlops-gate`), not GitHub CI. Runs the
   stdlib ladder (L0-L3) + the honesty guard (served confidence must not exceed earned). Heavy
   studies are NOT in `run_studies` / the gate; run them by hand under `.venv-modeling`.
9. External flake (B.9). The OrcaHello history API 403s / SSL-EOFs on heavy paging and
   `fetch_history` returns oldest-first (early pages all Haro Strait). For multi-station use the
   reviewed-outcome endpoints + the cached indexes
   (`.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json`, 3 nodes;
   `orcahello_index.confidence.cache.json`, 4 nodes with confidence).
10. Write policy (B.10). No commit or push without an explicit operator ask. Surgical staging only
    (SD-024, never `git add -A`); single-author voice (SD-006); restore timestamp-only report churn
    before committing.

## C. Waveset execution model (keep this discipline; adapted from the terrain-bathymetry home)

Work is chartered as sequential waves. Each wave runs several subagents fully in parallel. Wave
N+1 starts only after Wave N integrates and the stated gate is met.

Parallelism discipline (prevents write collisions and silent promotion):

1. One file, one owner per wave. Each agent owns a distinct NEW file or directory. No two agents in
   the same wave edit the same file.
2. The convergence files have exactly one editor per wave, the integrator. Every other agent ships
   a standalone module plus a thin wiring spec, and the integrator applies the wiring. The
   convergence files for this lane are:
   - modeling: `modeling/fit_kernels.py` and `modeling/studies/level2_multistation.py`.
   - backend: `src/aws_backend/sources/salmon.py` and `src/aws_backend/ingest_timeseries.py`.
   Wave 1 agents do NOT edit any convergence file.
3. Foundation agents (Wave 1) create new files only. They never touch a convergence file, so they
   cannot collide.
4. No concurrent heavy fit and no production store write during a parallel wave. Two heavy fits
   racing against S3, or two agents writing the same stream, collide. Each modeling agent validates
   with the stdlib ladder OR a single local memory-store run with the S3 model-artifact upload
   disabled (`fk._maybe_write_s3 = lambda: None`) and `write_outputs=False`. This is the analog of
   "no shared dev server / full build."
5. Environments are fixed per agent: heavy fits and heavy studies under `.venv-modeling`; the
   stdlib ladder and the gate under system `python3`; backend tracks under `.venv`.
6. Large / local-only artifacts (`data/models/**`, `fit_report.json`, model pickles, figures) stay
   untracked by repo convention (B.6) and are never committed. Only `modeling/studies/**` + reports
   and `modeling/tide_harmonic.py` are tracked.
7. No agent commits or pushes. Each agent returns its wiring spec + measured results (section F).
   The orchestrator does one integration step per wave, and a commit only on an explicit operator
   ask (B.10).
8. Honesty constraint carried into every wave (B.1-B.3): no confidence promotion as a side effect;
   no faked coverage, skill, or kernels; an agent blocked by data reports withheld with the reason.

## D. The three waves

### Wave 1: de-risk and characterize (5 parallel, disjoint, no convergence-file edits)

Operator-confirmed scope: the L2-unblock modules plus the disjoint backend tracks, all in parallel.

- A, effort / `log E` model (modeling, `.venv-modeling`). Owns NEW `modeling/effort.py`. Derive a
  per-station effort/uptime series to a `log E` offset and exposure that the conditional intensity
  consumes, so the time-rescaling timing is effort-corrected. Root-cause owner for blocker (1).
  Ship `WIRING-effort.md` for how `build_design` (`modeling/design.py`) and `_station_intensity_fn`
  / `_time_rescaling_report` (`modeling/fit_kernels.py`) should consume it.
- B, time-rescaling diagnostic (modeling, `.venv-modeling`). Owns NEW
  `modeling/studies/time_rescaling_diag.py` + a report under `modeling/studies/reports/`.
  Characterize WHY the pooled KS is p=0.0 (per-station vs pooled, effort sensitivity, grid/bin
  resolution, conditional-intensity construction) without editing `modeling/validation/time_rescaling.py`
  or the fit. Ship a recommended-fix spec.
- C, cross-station consistency (modeling, `.venv-modeling`). Owns NEW
  `modeling/studies/cross_station_consistency.py` + report. Standalone per-kernel cross-station PSTH
  correlations with diagnostics (which stations/kernels drag the 0.14-0.34; effect of effort
  normalization and station partial pooling). Ship a recommendation to clear the 0.5 bar for
  blocker (2).
- D, multi-station ingest recipe (backend, `.venv`). Owns NEW `src/aws_backend/ingest_multistation.py`
  + `WIRING-ingest.md`. Recipe to ingest orcasound_lab, andrews_bay, north_san_juan_channel into the
  production `acoustic_detections` stream via the reviewed-outcome endpoints + cached indexes (B.9),
  reusing `_put_grouped_by_station`. Dry-run against the cached index only; the production write is
  operator/deploy-gated for Wave 2.
- E, salmon Albion/DART validation (backend, `.venv`). Owns NEW
  `src/aws_backend/sources/salmon_validation.py` (harness + captured real payloads). Hit the real
  Albion + DART feeds, capture the actual payload shapes, validate/repair the parse paths against
  them, and report whether a real feed beats the climatology fallback. Ship a patch spec for
  `salmon.py` (no edit this wave).

Gate to Wave 2: the diagnostics (B, C) pinpoint the time-rescaling fix AND the effort module (A) is
ready to wire AND the ingest dry-run (D) + salmon validation (E) report honest findings.

### Wave 2: integrate (single convergence-file editor per file)

- modeling integrator (sole editor of `modeling/fit_kernels.py` + `modeling/studies/level2_multistation.py`).
  Wire the effort / `log E` module and the time-rescaling fix per the Wave 1 wiring specs, land the
  cross-station consistency change, refit against S3 with the upload disabled and `write_outputs=False`,
  and produce the updated L2 verdict in `modeling/studies/reports/level2_multistation.json`.
- backend integrator (sole editor of `src/aws_backend/sources/salmon.py` + `ingest_timeseries.py`).
  Land the validated Albion/DART parsers and wire the multi-station ingest. The actual production
  store write (ingesting the 3 nodes) is operator/deploy-gated.
- cross-station consistency landed into the report (via the modeling integrator).

Gate to Wave 3: the multi-station refit runs with effort-corrected timing; time-rescaling and
cross-station results are recorded honestly (pass or, if still short, withheld with the reason);
no confidence promotion occurred.

### Wave 3: gate, L3, promotion prep

- L3 real Chinook lag scan: re-run `modeling/studies/salmon_lag.py` / `level3_prey_space.py` on the
  validated real feed; verdict pass or withheld.
- mlops-gate + honesty guard re-run (`tools/waves/run-gate.sh mlops-gate`); served confidence must
  not exceed earned.
- Promotion packet for the supervisor decision (operator-gated), prepared ONLY if a gate actually
  passes. Promotion itself is a recorded supervisor decision (B.1), not part of this wave's
  automation.

MLO platform (feature store, registry, scheduled gated retrain, monitoring, CI) remains chartered
in `MLO_CHARTER.md` and is operator/deploy-gated; it is a later track, not folded into W1-W3.

## E. Per-agent prompt skeleton (copy-paste)

Every parallel agent gets a self-contained prompt. It has no conversation history, so include all
context. Fill the brackets.

```
You are agent [LETTER] in Wave [N] of the orcast ML-ops frontier waveset.
Charter: .cca/catalogue/O0/20260627_mlops/WAVESET_CHARTER.md.
Locked decisions: .cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md section B.
Methodology: docs/methodology/FORECAST_KERNELS.md, CALIBRATION_STUDIES.md.

GOAL OF THE WAVESET: push Level 2 off 0% effective confidence honestly (effort/log E so
time-rescaling passes; cross-station kernel consistency), and de-risk the 3-node production ingest
and the real Chinook (Albion/DART) feed. No confidence promotion in any wave.

REPO: /Users/gilraitses/orcast (git main). Modeling pipeline is LOCAL-ONLY/untracked (B.6); heavy
fits/studies under .venv-modeling; stdlib ladder/gate under system python3; backend under .venv.
AWS store: bucket 198456344617-us-west-2-orcast-aws-backend-raw-payloads, region us-west-2 (B.4).

PRIOR-WAVE OUTPUTS YOU BUILD ON (all landed): [module APIs with exact signatures, report paths,
commit hashes if any]. (Wave 1 agents: none.)

YOUR TASK: own NEW file/dir [path]. [Exact deliverable and exported API / report contract.]

DELIVERABLES: [the file(s)] + [WIRING-<name>.md telling the integrator exactly how to wire it].

VALIDATION: [the stdlib ladder OR a single local memory-store run with fk._maybe_write_s3 = lambda:
None and write_outputs=False; backend: unit/harness run]. Report the real measured result.

COLLISION-AVOIDANCE:
- Do NOT edit any convergence file: modeling/fit_kernels.py, modeling/studies/level2_multistation.py,
  src/aws_backend/sources/salmon.py, src/aws_backend/ingest_timeseries.py.
- Do NOT run a second heavy fit concurrently and do NOT write the production store. Disable the S3
  model-artifact upload and use write_outputs=False for any fit.
- Local-only artifacts (data/models/**, fit_report.json, pickles, figures) stay untracked; commit
  nothing.
- Be honest about what you verified vs assumed; if blocked by data, report withheld with the reason
  rather than faking coverage/skill/a kernel.

When done, return: exported API / report contract, decisions made, measured validation result,
risks. No commit.
```

## F. Gates and return contract

Operator approval gates (the orchestrator pauses for these):
- Wave 1 launch (this dispatch is READY; launch is the next operator gate).
- Wave N to Wave N+1 promotion, after the stated gate is met.
- The production `acoustic_detections` store write for the 3 nodes (deploy-gated).
- Any commit or push (orcast write policy B.10: only on explicit operator request).
- Any confidence promotion: a passing gate + a recorded supervisor decision (B.1).

Per-agent return contract:
- files owned, wiring spec (if its output must be wired), measured results, risks. No commit.

Per-wave exit:
- the named gate met, one integration step by the orchestrator, no auto-promotion.

## G. Open questions to confirm before launching

- Subagent model: inherit the orchestrator's, or pin a model for the heavy modeling agents (A, B,
  C run under `.venv-modeling` and touch S3)? Default: inherit.
- Whether agents A/B/C may each read S3 once (one local memory-store fit each), or whether the
  orchestrator runs a single shared S3 fit and hands the fit report to A/B/C to keep S3 reads
  serialized. Default: one local read each, upload disabled, no production write.
- Wave 1 launch go.

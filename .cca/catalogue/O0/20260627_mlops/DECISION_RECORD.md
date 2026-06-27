# Decision record, ML-ops frontier waveset

Date: 2026-06-27 (America/New_York). Lane: O0 orchestrator, forecast ML-ops (MLM + MLO).
Home: `.cca/catalogue/O0/20260627_mlops/`. Status: CONFIRMED by operator 2026-06-27.
Externalizes the locked L2/L3 frontier (HANDOFF_CHARTER section B) into the parallel-subagent
execution model of `WAVESET_CHARTER.md`.

No commit, no push, and no agent launch happen on this document. Wave 1 launch is the next operator
gate.

## 0. Code surface this waveset acts on (verified by reading the repo 2026-06-27)

- L2 convergence point: `modeling/fit_kernels.py` (local-only). Effort enters via
  `build_design(acoustic, uptime, tide_phase=..., bin_hours=...)` and `df.attrs["effort_assumed_continuous"]`
  (around line 612-614); the time-rescaling verdict is assembled in `_time_rescaling_report` via a
  per-station `_station_intensity_fn(model, station, lat, lng, tide)` (line 882-911); cross-station
  consistency is computed in `_cross_station_consistency(df, covariates)` (line 802-837, the 0.5
  bar). The S3 model-artifact upload is `_maybe_write_s3` (line 1003) and is guarded by
  `write_outputs`.
- Multi-station experiment driver: `modeling/studies/level2_multistation.py`. It already sets
  `fk._maybe_write_s3 = lambda: None` and calls `fk.run_fit(mem, ..., write_outputs=False, make_figures=False)`,
  reading `haro_strait` from S3 and the other 3 nodes from the cached OrcaHello index into a
  `MemoryTimeSeriesStore`. This is the integration study; the modeling integrator owns it in Wave 2.
- Time-rescaling primitive: `modeling/validation/time_rescaling.py` (`run_time_rescaling`,
  `time_rescaling_test`, KS vs Exp(1)). Local-only; the Wave 1 diagnostic reads it, does not edit it.
- Salmon parsing: `src/aws_backend/sources/salmon.py`. `_fetch_fraser` (Albion), `_fetch_columbia`
  (DART), `_parse_daily_payload`, all marked UNCONFIRMED against live feeds in the module docstring;
  both currently fall through to `_climatology_series`. The backend integrator owns it in Wave 2.
- Multi-station ingest: `src/aws_backend/ingest_timeseries.py`. `ingest_acoustic_reviewed_outcomes`
  (line 93), `_put_grouped_by_station` (line 443) group records by `record["station"]` into the
  `acoustic_detections` stream. Today only `haro_strait` is in the production stream.
- Cached indexes (B.9): `.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json`
  (3 nodes), `orcahello_index.confidence.cache.json` (4 nodes with confidence).

Key observation: the L2 frontier and the two backend tracks touch disjoint files, so Wave 1 can run
all five agents in parallel with no convergence-file edits. The collisions only appear at Wave 2
integration, where each convergence file gets a single editor.

## 1. Decision record (confirmed)

| Decision | Choice | Rationale / source |
|----------|--------|--------------------|
| Honesty / promotion gate | locked: gate + recorded supervisor decision only | HANDOFF_CHARTER B.1. No wave promotes confidence. |
| Effort-bias design | locked: acoustic-first temporal kernels + `log E`; visual is validation + `s_space` | HANDOFF_CHARTER B.2. Wave 1 agent A owns the per-station effort/`log E`. |
| Coverage honesty | locked: insufficient coverage reports withheld | HANDOFF_CHARTER B.3. An agent may conclude blocked/withheld. |
| AWS store | locked: `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, `us-west-2` | HANDOFF_CHARTER B.4. Not the config default. |
| Refit safety | locked: disable `_maybe_write_s3`, `write_outputs=False` on any S3 refit | HANDOFF_CHARTER B.5. No promotion as a refit side effect. |
| Repo layout | locked: `modeling/` pipeline + `data/models/` local-only; only `studies/**` + reports + `tide_harmonic.py` tracked | HANDOFF_CHARTER B.6. Agents commit nothing; local artifacts untracked. |
| Environments | locked: `.venv-modeling` heavy; system `python3` ladder/gate; `.venv` backend | HANDOFF_CHARTER B.7. Fixed per agent. |
| Wave 1 scope | run all five Wave 1 agents (L2-unblock A/B/C + backend D/E) in parallel | Operator-confirmed 2026-06-27. |
| Waveset home | extend the existing `.cca/catalogue/O0/20260627_mlops/` (do not overwrite the level ladder) | Operator-confirmed 2026-06-27. |
| Subagent model | inherit the orchestrator's | Operator default (terrain-bathymetry precedent); revisit if the modeling agents need a pinned model. |
| Production ingest run | the actual 3-node `acoustic_detections` store write is operator/deploy-gated | HANDOFF_CHARTER dispatch table; deploy-gated. Wave 1 D dry-runs only. |

## 2. Wave 1 shape (CONFIRMED scope, NOT yet launched)

Five parallel agents, none edits a convergence file, validate-only, no agent commits. Full
per-agent prompts are in `WAVE1_DISPATCH.md`.

1. A, effort / `log E` model (new `modeling/effort.py`): per-station effort/uptime to a `log E`
   offset + exposure; root-cause owner for time-rescaling. `.venv-modeling`.
2. B, time-rescaling diagnostic (new `modeling/studies/time_rescaling_diag.py`): characterize why
   pooled KS p=0.0; recommend a fix. `.venv-modeling`.
3. C, cross-station consistency (new `modeling/studies/cross_station_consistency.py`): per-kernel
   cross-station PSTH correlations + diagnostics; recommend how to clear the 0.5 bar. `.venv-modeling`.
4. D, multi-station ingest recipe (new `src/aws_backend/ingest_multistation.py`): ingest the 3 extra
   nodes via reviewed-outcome endpoints + cached indexes; dry-run only. `.venv`.
5. E, salmon Albion/DART validation (new `src/aws_backend/sources/salmon_validation.py`): validate
   the real feeds, patch spec for `salmon.py`. `.venv`.

Gate to Wave 2: diagnostics pinpoint the time-rescaling fix AND the effort module is ready to wire
AND the ingest dry-run + salmon validation report honest findings.

## 3. Risks

- Time-rescaling may not pass even with an effort model. The pooled KS p=0.0 may reflect the
  sparse-count single/four-station regime (NOTES section 4), not just effort. If so, the honest
  outcome is withheld with the reason, not a tuned gate (B.3).
- Cross-station correlations may stay below 0.5 because of genuine station heterogeneity, not effort
  normalization. Agent C must distinguish the two and not force consistency.
- Salmon live feeds (Albion/DART) are published as varying HTML/CSV and may resist parsing; a real
  feed that does not beat climatology leaves L3 withheld (honest), not promoted.
- S3 read contention: if A/B/C each read S3 concurrently, serialize via the orchestrator handing
  one shared fit report, or stagger the reads. No production write in any case.
- The modeling pipeline is local-only/untracked (B.6); a fresh actor must reproduce the fit from S3
  (B.4) before Wave 2 integration is meaningful.

## 4. Recorded supervisor decision -- adopt the bin-level L2 timing gate (2026-06-27)

Operator instruction: "commit and approved adoption". This is the recorded supervisor decision
required by HANDOFF_CHARTER B.1 for the W4 item-3 bin-level timing gate.

- DECISION: ADOPT the bin-level timing criterion as the served L2 timing gate. In
  `modeling/fit_kernels.py`, `ADOPT_BIN_LEVEL_TIMING_GATE` flipped `False -> True` (local-only/untracked,
  B.6; the flip is recorded here, which IS tracked).
- HONEST FRAMING (recorded as such, not as "time-rescaling passed"): event-level Exp(1) time-rescaling
  is inappropriate for a detector-chatter stream. The self-exciting Hawkes branching ratio is 0.79-0.96
  across stations and the pooled compensator KS p=3.3e-33, i.e. the event-level timing is dominated by
  self-excited detector repeat-triggering, not the animal signal. The GOF is therefore scored at the
  served per-bin-count target: held-out NB PIT calibrated (ks_pval 0.85 on the served fit) AND held-out
  CV mean-deviance-skill > climatology. The CV-skill half is load-bearing and non-automatic.
- EFFECT ON CONFIDENCE (verified empirically 2026-06-27, flag ON):
  - Served single-station fit (haro_strait, n=761): CV mean-deviance-skill = -0.047 (< 0), so the
    load-bearing CV-skill half FAILS, `bin_level_verdict = fail`, `timing_gate = False`, and
    `_confidence_from_gates` returns **0.0**. `mlops-gate` = ALL PASS, honesty guard
    `served_confidence=0.0 l2_gate=fail OK`. NO promotion occurred. Adoption is data-earned, not
    automatic.
  - Counterfactual: if a SERVED fit had CV mean-deviance-skill = +0.078 (the value the 4-station
    EXPERIMENT shows, NOT served), `_confidence_from_gates` would jump to **1.0** (all four 0.25
    quarters). The +0.078 only exists in `level2_multistation.json`; it becomes served only after the
    deploy-gated 3-node production acoustic_detections ingest lands.
- CONSEQUENCE / RISK now armed: with the flag ON, the NEXT served fit whose held-out CV-skill is
  positive will earn timing credit. On the original 4-quarter scoring that meant a hard cliff to 1.0.
  MITIGATED 2026-06-27 by P0 (forward-path campaign): `_confidence_from_gates` is now effect-size-scaled
  and capped at 0.75, so a served +0.078 fit maps to 0.49 (HOLD, below the supervisor 0.6 threshold) and
  crossing 0.6 requires CV-skill ~+0.144. Until a served fit earns it, confidence stays 0.0. The
  remaining precondition is data/deploy-bound (3-node ingest), not a code gate; and the ingest alone
  (~+0.078) lifts served confidence to ~0.49 but does NOT auto-promote.
- NOT decided here: the L3 summer-conditioned held-out flag (2021 OOS r=0.390, p=0.027) remains
  FLAGGED-FOR-DECISION and L3 stays WITHHELD; the operator did not approve an L3 promotion.

# Handoff charter, forecast ML-ops lane orchestrator

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `88849e1` (in sync with
`origin/main`). This charters a fresh thread that continues the forecast modeling ML-ops lane
(MLM covariate modeling + MLO platform). The 3d-twin lane is handed off separately
(`.cca/catalogue/O0/20260627_3d-twin/`) and is not in scope here. Hydrate from files, not from
the transcript linearly.

## A. Purpose

The new thread owns the forecast ML-ops lane: bring the aggregated weather and wildlife
covariates into the leveled, gated kernel model honestly, and push Level 2 off 0% effective
confidence. The biggest recent finding is that multi-station acoustic coverage flips held-out
skill positive, so the frontier is now productionizing multi-station and clearing the two
remaining L2 blockers (time-rescaling GOF and cross-station kernel consistency), then validating
a real Chinook feed for L3. The MLO platform (feature store, registry, scheduled gated retrain,
monitoring, CI) follows. No confidence promotion without a passing gate plus a recorded human
decision via the supervisor.

## B. Decisions that are LOCKED, do not reopen

1. Honesty gate. Effective confidence is 0% and is shown with the gate caveat. `effective_confidence`
   only rises on a passing gate plus a recorded human decision via
   `src/aws_backend/promotion/supervisor.py`. Never render sharper than the gates support.
2. Effort-bias design. Temporal kernels are estimated from continuous acoustic detections
   (effort-stable) with an explicit `log E` offset. Visual sightings (OBIS, iNaturalist, community,
   CAND) are validation and `s_space` only, never the temporal-kernel heat. Acoustic presence is
   not a visual encounter and the hydrophone is a fixed position, not a whale GPS fix.
3. Coverage honesty. A covariate whose phase coverage or data coverage is insufficient reports
   `withheld` with the reason, never a fabricated kernel.
4. AWS store location (the footgun that cost a session). The timeseries data is in S3 bucket
   `198456344617-us-west-2-orcast-aws-backend-raw-payloads` (region `us-west-2`), NOT the config
   default `orcast-raw-payloads`. Reproduce any fit with:
   `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2 PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels`.
5. Refit safety. When refitting against S3, DISABLE the production artifact upload
   (`fit_kernels._maybe_write_s3 = lambda: None` in a driver, or run with `write_outputs=False`):
   a confidence change must be a recorded supervisor decision, not a refit side effect.
6. Repo layout. The `modeling/` fit pipeline (`fit_kernels.py`, `design.py`, `estimator.py`,
   `bases.py`, `tide_phase.py`, `validation/`, ...) and `data/models/` are local-only (untracked)
   by repo convention. Only `modeling/studies/**` and `modeling/studies/reports/*.json` are
   tracked, plus `modeling/tide_harmonic.py` (committed). The harmonic-tide integration
   (`HarmonicTidalPhase` in `tide_phase.py`, the tide selection in `fit_kernels.py`) lives in the
   local tree; do not expect it on a clean checkout.
7. Environments. `.venv-modeling/bin/python` (numpy 2.4.6, pandas, scipy, matplotlib, boto3) runs
   the heavy fit and the heavy studies. `modeling/studies/` is otherwise pure stdlib and runs
   `run_studies.py` / the ladder under system `python3`. `.venv` (python3.14) has the backend deps.
8. mlops-gate is a LOCAL gate (`tools/waves/run-gate.sh mlops-gate`), not in GitHub CI. It runs the
   stdlib ladder (L0-L3) + the honesty guard (served confidence must not exceed earned). Heavy
   studies (`level2_multistation.py`, `tide_coverage.py`) import the pipeline, so they are NOT in
   `run_studies` / the gate; run them by hand under `.venv-modeling`.
9. External flake. The OrcaHello history API 403s / SSL-EOFs, especially on heavy paging, and
   `fetch_history` returns oldest-first (early pages are all Haro Strait). For multi-station use the
   reviewed-outcome endpoints and the cached index
   (`.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json`, 3 nodes;
   `orcahello_index.confidence.cache.json`, 4 nodes with confidence).
10. Write policy. No commit or push without an explicit operator ask. Surgical staging only
    (SD-024, never `git add -A`); single-author voice (SD-006); restore timestamp-only report churn
    before committing. CI (aws-backend-ci) only triggers on backend paths and is currently green.

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| FIX-CI | python-multipart + governance test helper + stale-test alignment; origin CI green | done, pushed (`c546a31`) |
| M-L0 detector | ROC AUC 0.879 (CI 0.856-0.902), d' 1.62 from live confidence cache (758 paired) | done, PASS (`d4e6b06`) |
| M-L1 diel | PSTH modulation 1.79, permutation p=0.0005 | done, PASS |
| M-TIDE | harmonic M2/S2/N2/K1/O1 model; tide phase coverage 0.42 to 1.00 | done (`d4e6b06`, `70526ee`) |
| M-L2 single-station refit | k_tide enters the fit; held-out skill -0.047, time-rescaling fail | done, FAIL/0% (`70526ee`) |
| M-L2 multi-station experiment | 4 nodes, 2089 det, all 4 kernels; held-out skill +0.078 (4/5 folds) | done, FAIL/0% (`79f863b`) |
| M-L3 salmon lag | lag scan on climatology placeholder; withheld | done, WITHHELD (`d4e6b06`) |
| WILDLIFE | 4-lane source research + ranked register | done (`70526ee`) |
| MLO | mlops-gate + honesty guard | done; platform chartered |

## D. PRIMER, open items

The operator's live intent is to push the forecast off 0% honestly and to mature the covariate
modeling with PIML (`.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md`). The
multi-station experiment is the breakthrough: skill is now positive. The two remaining L2 blockers
are concrete: (1) time-rescaling GOF fails (pooled KS p=0.0), which points at per-station effort /
`log E` and the conditional-intensity timing, not the covariate list; (2) the cross-station kernels
are testable but not yet consistent (PSTH correlations 0.14-0.34, below 0.5). L3 needs a real
Chinook run-timing feed to replace the climatology placeholder.

## E. Dispatch table

| Lane | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| M-L2 productionize multi-station | orchestrator | ingest the 3 extra Orcasound nodes into the production `acoustic_detections` stream; per-station effort/uptime so `log E` binds; cross-station consistency | held-out skill beats climatology AND time-rescaling passes AND cross-station consistent | open (frontier) |
| M-L3 real Chinook feed | orchestrator | validate the Albion/DART parsers in `src/aws_backend/sources/salmon.py` (both wired, both fall through to climatology); re-run the lag scan | lag scan on a real feed beats the permutation null | open |
| WILDLIFE ingest follow-on | orchestrator/operator | `WILDLIFE_SOURCES_REGISTER.md` P0 order (multi-station acoustic, real Chinook, held-out visual) | adapters validated, not climatology | open |
| MLO platform | operator/deploy-gated | FEAT/REG/SCHED/MON/CI | scheduled gated retrain without auto-promotion | chartered |
| Promotion | operator | a passing L2 gate + supervisor decision | `effective_confidence` raised on the record | gated (no gate passes yet) |
| DEMO capture | dormant | B.8 target decision | A/B narrated videos | blocked (operator) |
| BSIDE B-SKILLS.. | dormant | ORCAST_BSIDE_DESIGN section 6 | per-wave gate | chartered |

## F. Open gate / metric state (numbers)

- Effective confidence 0.0. L0 PASS (ROC AUC 0.879). L1 diel PASS. L2 FAIL: single-station skill
  -0.047; multi-station experiment skill +0.078 (4/5 folds, beats climatology) but time-rescaling
  pooled KS p=0.0 (fail) and cross-station PSTH correlations 0.14-0.34 (not consistent). L3
  WITHHELD (climatology salmon placeholder). PIT calibrated (NB2) but credit is gated on
  time-rescaling. The multi-station experiment's internal gate score would be 0.5; it is NOT
  promoted (`modeling/studies/reports/level2_multistation.json`).

## G. Pending uncommitted local state

Everything this session is committed and pushed (`c546a31..88849e1`). The `modeling/` fit pipeline
and `data/models/` stay local-only (untracked) by repo convention (section B.6); the harmonic
integration and the last refit's `fit_report.json` are local. A cross-actor rehydration that needs
to reproduce the fit must re-run it from S3 (section B.4) since those artifacts are not in git.

## H. Return contract (ack on first response)

The new thread returns, before acting:
- Hydration confirmed, list of files read.
- The locked items (section B) restated in your own words, especially the honesty/promotion gate,
  the effort-bias design, the AWS bucket footgun (B.4), the refit-upload-disable rule (B.5), and
  the local-only modeling pipeline (B.6).
- Current gate state in one line (effective confidence 0%, L2 frontier: multi-station skill
  positive but time-rescaling + cross-station block).
- Next 3 steps and which need operator approval.
- One risk still needing attention.

## I. Transcript / provenance pointer

Originating session: `~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/b67452d8-e353-4eb2-b95f-48cd71b286d6/b67452d8-e353-4eb2-b95f-48cd71b286d6.jsonl`.
Search by keyword (multistation, harmonic, L2, WILDLIFE, NoSuchBucket, time-rescaling), do not read
linearly. Prior rotation: `.cca/catalogue/O0/20260627_orcast-handoff/`.

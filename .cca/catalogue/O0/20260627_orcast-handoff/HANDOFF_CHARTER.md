# Handoff charter, orcast-lane orchestrator

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `17400b0` (in sync with
`origin/main`). This charters a fresh thread that resumes the orcast B-side build, the demo
capture, and the forecast ML ops. Hydrate from files, not from the transcript linearly.

## A. Purpose

The new thread continues the orcast research-workbench build: it owns the forecast modeling
ML ops (MLM/MLO), the whale-tagger B-side build (BSIDE), the forecast-candidate data
foundation (CAND, done), and the A/B-side demo capture (DEMO, blocked on a target decision).
It also lands the already-fixed CI once the operator approves a commit. The operator's
near-term intent is to mature the covariate modeling and decide how to combine the kernel ML
ops with physics-informed machine learning (PIML); see `ORCHESTRATOR_NOTES.md`.

## B. Decisions that are LOCKED, do not reopen

1. Honesty gate. The forecast effective confidence is 0% and must be shown with the gate
   caveat. The live map path is a hotspot heuristic, not the validated kernel model. Never
   render sharper than the gates support; `effective_confidence` only rises on a passing gate
   plus a recorded human decision via `src/aws_backend/promotion/supervisor.py`.
2. Confirmed sighting = `cross_validation.status` in {verified, likely} (`/api/verified-sightings`);
   community rows require moderator `approved`. Coordinates+timestamp are the anchor.
3. Effort-bias design (the central methodological risk). Estimate temporal kernels from
   continuous acoustic detections (effort-stable) with an explicit `log E` offset. Visual
   sightings (OBIS, iNaturalist, community, the CAND set) are validation and `s_space` only,
   never the temporal-kernel heat. See `docs/methodology/FORECAST_KERNELS.md` section 6.
4. Acoustic presence is not visual encounter, and acoustic detections sit at a fixed
   hydrophone position, not a whale GPS fix. Keep them as honest layers.
5. DTAG is partnership-gated. The whale-tagger ships only the bundled SIMULATED example
   (flagged `simulated: true`); the feeding classifier returns `not_trained` with the
   uniform-probability caveat (no trained weights in-repo). tagtools is not installed and is
   R/MATLAB-native; any python port must be numerically validated against CRAN tagtools.
6. CI footgun (now fixed locally, not yet committed). `.github/workflows/aws-backend-ci.yml`
   must install `python-multipart` or the whole pytest run fails at collection. The fix
   installs from `tools/deployment/aws/requirements.txt`. A stale test in
   `tests/aws_backend/test_decision_records.py` was also fixed (it needed `governance_headers`
   on `/api/promotion/apply`). Local suite is green: 225 passed.
7. External flake. The OrcaHello history API (`aifororcasdetections.azurewebsites.net`)
   intermittently returns 403 / SSL EOF, especially after heavy paging. A successful fetch is
   cached at `.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index.cache.json` and
   reused; do not assume a live fetch will succeed.
8. Frontend route drift (blocks demo capture). The console (`AdaptiveExplore`,
   `data-demo="explore-scene/console/active-surface"`) is at `/`. The provenance modal
   ("Why is this cell hot?") is NOT at `/`; it moved to `ExploreGuidePanel` (`/explore`) and
   `MapHero`. The deployed site's `/` console did not return plan panels under agent auth
   within 60s. Re-capture needs a local dev stack matching `main`, or a redeploy, or
   retargeting the provenance beats to `/explore`.
9. Write policy. No commit or push without an explicit operator ask. Do not write pax gated
   surfaces. Orcast writes follow orcast workspace rules.
10. Environments. `.venv` (python3.14) has the backend deps (fastapi, python-multipart);
    `modeling/studies/` is pure stdlib and runs under system `python3`. numpy is NOT in
    `.venv`.

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| FIX-CI | python-multipart in CI workflow + stale test fix; 225 pytest pass locally | done, uncommitted (red on origin until pushed) |
| CAND | `tools/forecast_candidates/build_candidates.py` + `candidates.targets.json` (200 candidates, 166 tier-A) | done |
| BSIDE B-API | `src/aws_backend/routers/dtag.py` (`/api/dtag/*`), registered, supersedes 410; `test_dtag.py` 6 pass | done; B-SKILLS..B-MCP chartered |
| DEMO | 4 B-side beat specs + W-STORY + B-DATA data-lineage beat | specs ready; capture blocked (decision B.8) |
| MLM | `modeling/studies/` L0-L3 ladder runs honestly (L1 diel passes) | scaffolding done; science gates open |
| MLO | `mlops-gate` + honesty guard wired into `tools/waves/run-gate.sh` | CI gate done; AWS platform chartered |

Machine registry: `docs/devpost/waves.registry.yaml`; prose: `docs/devpost/WAVES_REGISTRY.md`.

## D. PRIMER, open items (operator framing preserved)

The operator asked, verbatim, for the incoming orchestrator to have "any more context and
recommended literature ... about my intent and the best way to ... use the ml ops together
with PIML or what your opinions are of this architecture about what you would have done
differently." That is captured in `ORCHESTRATOR_NOTES.md` (intent, PIML+MLOps strategy,
architecture critique, recommended reading). Treat advancing the covariate modeling and the
PIML decision as the live design question.

Other open items:
- Demo capture target decision (B.8). Needed before W-CAPTURE/W-VOICE/W-ASSEMBLE.
- Commit/push of this session's work (operator ask pending).
- MLM frontier: Level 0 detector ROC needs the confidence-scored detection feed; Level 2
  needs fuller annual + lunar acoustic coverage to lift tide/season.

## E. Dispatch table

| Lane | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| Commit + push | operator-gated | this session's uncommitted files | green CI on origin | pending ask |
| DEMO capture | orchestrator | W-STORY, bside-*.spec.ts, target decision | A/B narrated videos + gifs | blocked (B.8) |
| MLM L0/L2 | orchestrator | scored detection feed; more acoustic coverage | gate pass | open |
| MLM L3 + PIML | orchestrator | salmon series, effort model, NOTES PIML plan | beats density baseline, calibrated | open |
| MLO platform | operator/deploy-gated | EventBridge/Step Functions | scheduled gated retrain | chartered |
| BSIDE B-SKILLS.. | orchestrator | ORCAST_BSIDE_DESIGN section 6 | per-wave gate | chartered |

## F. Open gate / metric state (numbers)

- Effective confidence 0.0. Held-out CV mean deviance skill -0.018 (does not beat
  climatology). Time-rescaling pooled KS p=0.0 (fails). Tide phase coverage 0.42, season
  0.75 (both below the 0.90 inclusion threshold, so withheld). PIT calibrated (ks p=0.99) but
  credit is gated on time-rescaling.
- MLM ladder: L0 withheld (effort known; ROC needs scores), L1 diel PASS (modulation 1.79,
  permutation p=0.0005 on 1359 cached detections), L2 FAIL, L3 withheld.
- CI: red on `origin/main` until the FIX-CI commit is pushed (the test job dies at collection
  without python-multipart).

## G. Pending uncommitted local state

`git status` shows ~497 entries, but most are pre-existing `ORCAST_Project_Overview*`
deletions from before this session, not this work. This session added/edited (all uncommitted):
- `.github/workflows/aws-backend-ci.yml`, `tests/aws_backend/test_decision_records.py` (FIX-CI)
- `src/aws_backend/routers/dtag.py`, `main.py`, `routers/deprecated.py`, `tests/aws_backend/test_dtag.py` (B-API)
- `tools/forecast_candidates/build_candidates.py`, `tools/waves/gates/mlops-gate.sh`, `tools/waves/run-gate.sh`
- `modeling/studies/**`
- `web/e2e/beats/bside-*.spec.ts`
- `docs/devpost/waves.registry.yaml`, `docs/devpost/WAVES_REGISTRY.md`
- `.cca/catalogue/O0/20260627_{demo-waveset,forecast-candidates,bside-build,mlops,orcast-handoff}/**`

Same-machine rehydration: these files are on disk now, so a fresh thread on this machine sees
them. If the operator commits, update the hashes here. Cross-actor rehydration requires the
commit first.

## H. Return contract (ack on first response)

The new thread returns, before acting:
- Hydration confirmed, list of files read.
- The locked items (section B) restated in your own words, especially the honesty gate, the
  effort-bias design, and the CI/route-drift footguns.
- Current gate state in one line (effective confidence 0%, MLM frontier at L0/L2).
- Next 3 steps and which need operator approval.
- One risk still needing attention.

## I. Transcript / provenance pointer

This session: `~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/a62854cc-5a6a-4bf0-9400-402527dc80eb/a62854cc-5a6a-4bf0-9400-402527dc80eb.jsonl`. Search by keyword (CAND,
dtag, mlops, python-multipart, provenance), do not read linearly. Three read-only data-mining
subagents under that uuid's `subagents/` mapped the sources, covariates, and hydrophones.

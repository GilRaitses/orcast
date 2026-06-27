# BSIDE, whale-tagger B-side build order charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orcast-lane orchestrator
Home: `.cca/catalogue/O0/20260627_bside-build/`
Family id: BSIDE

Mirrors `ORCAST_BSIDE_DESIGN.md` section 6 and `WHALE_TAGGER_API_DESIGN.md`. Builds the
research-backend whale tagger on top of the working orcast stack, on the orcast Central
Casting pattern. Greenfield; nothing existing is removed.

## Locked honesty constraints (do not reopen)

- DTAG data is partnership-gated. The only deployment until a data-sharing agreement lands is
  the bundled SIMULATED example, flagged `simulated: true`.
- The feeding classifier has no trained weights in-repo. The endpoint returns
  `model_state: not_trained` with the uniform-probability caveat (the minGRU collapses to
  uniform under annotation scarcity; the honest near-term path is a Random Forest at 84.38%,
  not yet wired).
- tagtools is not installed; the feeding math is R/MATLAB-native. Any ported function must be
  numerically validated against CRAN tagtools before its outputs are trusted.
- Telemetry dive/feeding analysis is distinct from acoustic hydrophone context and from
  visual sightings. Do not conflate.

## Build order and status

| Wave | Status | Scope | Exit bar |
|------|--------|-------|----------|
| B-API | done | `src/aws_backend/routers/dtag.py` cache-backed read path over `data/dtag_analysis_results.json` and `dtag_cache/`; registered in `main.py`; supersedes the 410 `/api/dtag-data` | `tests/aws_backend/test_dtag.py` green; deployments flagged simulated; feeding not_trained |
| B-SKILLS | chartered | skill manifest entries + dispatch in `casting/skills.py`; seed `casting/seeds/whale-tagger-v1.json`; register in `registry.py` | `run-gate.sh m`/`ic6` style gate |
| B-REPLAY | chartered | `compute_pseudotrack` + `build_replay_scene` over the bathymetry asset | pseudotrack numeric check; scene contract |
| B-ANNOT | chartered | annotation span schema + versioned taxonomy registry + prediction provenance envelope | schema validates; taxonomy versioned |
| B-PANELS | chartered | console panels (tag_series, dive_panel, replay_scene, label editor) via `uiIntent.ts` + `ActiveSurfaceHost.tsx` + planner keywords | panels render; ic6-style gate |
| B-INGEST | chartered (operator-gated) | partnership ingest to populate `dtag_cache/` with real animaltags files | ingest validates a real deployment |
| B-MCP | chartered (optional) | MCP wrapper over the same tool ids | tools/list + tools/call parity |

B-API unblocks demo beats B4 (tag deployment + dive detection), B5 (3D replay), and B6 (label
provenance). Each wave past B-API is operator-gated and sequenced.

## B-API surface (delivered)

- `GET /api/dtag/deployments` list (simulated example + any `dtag_cache/` deployments).
- `GET /api/dtag/deployments/{id}` summary or `not_available`.
- `GET /api/dtag/dives/{id}` per-dive metrics or `not_available`.
- `GET /api/dtag/feeding/{id}` `model_state: not_trained` with the uniform-probability caveat.

Taxonomy reported as `unratified-0` until the 11/9/5-class sets are unified into one versioned
registry (B-ANNOT).

## Out of scope

- Training any classifier. Writing into the live sighting store. pax surfaces.
- Installing tagtools without numeric validation against CRAN.

## Cross-links

- Design source (read-only): pax orchestrator-rotation catalogue.
- Registered as family `BSIDE` in `docs/devpost/waves.registry.yaml` and `WAVES_REGISTRY.md`.

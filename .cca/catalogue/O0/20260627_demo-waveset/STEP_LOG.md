# STEP_LOG, DEMO capture waveset

All times America/New_York.

## 2026-06-27

- Hydrated from the pax orchestrator-rotation charter set (read-only) and acked section H.
- Confirmed DTD migration effectively complete: beacon stale at PROC-DEAD 99.7%, but
  `aws s3 ls s3://aimez-data` shows 400 objects / 18.36 GB including both formerly-inflight
  files. DTD lane owns it.
- Chartered the orcast-side DEMO waveset home with `DEMO_CAPTURE_CHARTER.md` and
  `wave_shape.yml`. Registered family `DEMO` in `docs/devpost/waves.registry.yaml` and the
  prose `docs/devpost/WAVES_REGISTRY.md`.
- W-STORY: locked beat order, shot lists, one-line narration, and on-screen honesty captions
  for the three capturable B-side beats (B1, B2, B3) in `W-STORY.md`.
- Prepared the B1 Playwright capture spec `web/e2e/beats/bside-b1-console.spec.ts` against the
  root console (`AdaptiveExplore` -> `ActiveSurfaceHost` -> `OrchestratorTrace`). Held for
  operator green-light; not run.

## 2026-06-27 (later)

- Enriched W-STORY with a Data lineage section (sighting sources and feature-pipeline tables,
  grounded in the source inventory) and added capturable beat B-DATA "data sources and the
  feature pipeline" (route `/`, `GET /api/realtime/events` + `GET /api/provenance`). Prepared
  `web/e2e/beats/bside-bdata-sources.spec.ts` (held for green-light).
- Chartered the CAND forecast candidate-preparation waveset
  (`.cca/catalogue/O0/20260627_forecast-candidates/`) to assemble ~40 confirmed-sighting
  candidates prioritized near in-region hydrophones with OrcaHello annotation records. B-DATA
  sharpens once CAND lands the prioritized 40.

## 2026-06-27 (W-CAPTURE attempt against deployed orcast-h0.vercel.app)

- Prepared all four B-side specs (B1, B-DATA, B2, B3); lint clean. Environment verified:
  agent creds present, Playwright chromium + ffmpeg installed, deployed site 200.
- Ran W-CAPTURE (DEMO_RECORD=1, 1280x900) against the default deployed base URL. Result:
  B3 passed; B1, B2, B-DATA failed. Raw webms recorded under web/e2e/.results/ but do not
  show the intended UI.
- Root cause (route drift, not a flaky run):
  1. The console scene/console DID render on `/` (B1 passed the explore-scene/console
     asserts), but "Send turn" did not produce `[data-demo="active-surface"]` within 60s on
     the deployed backend (plan call returned no panels under agent auth).
  2. The provenance modal "Why is this cell hot?" no longer lives on `/`. It is in
     `ExploreGuidePanel` (`/explore`) and `MapHero`, not in `AdaptiveExplore` (current `/`).
     The B2/B-DATA specs were modeled on the older map-centric `beat-02` pattern.
- Decision needed before re-capture (operator):
  a. Capture target: the current repo (console at `/`) requires a LOCAL dev stack
     (next dev + backend) since the deployed build's plan call did not return panels; OR
     redeploy current `main`; OR retarget the provenance beats to `/explore`
     (ExploreGuidePanel + ProvenanceModal) and trigger via a map-cell click.
  b. Confirm the console plan endpoint returns panels under the capture auth on the chosen
     target.
- W-VOICE and W-ASSEMBLE are downstream-blocked on usable silent webms.

## Open / awaiting operator

- Pick capture base URL (deployed `orcast-h0.vercel.app` versus local) before W-CAPTURE.
- Green-light to record B1 (and then B2, B3).
- Commit/push only on explicit request.

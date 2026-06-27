# orcast DEMO capture waveset, orcast-side execution charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orcast-lane orchestrator
Home: `.cca/catalogue/O0/20260627_demo-waveset/`

This is the orcast-side execution charter for the DEMO capture waveset. It runs in the
orcast workspace and follows orcast workspace rules, not pax doctrine. It does not write
to pax surfaces. The design source of truth lives in the pax catalogue and is read-only
here:

- `pax/.cca/catalogue/O0/20260626_orchestrator-rotation/DEMO_WAVESET_CHARTER.md` (beat list, capture pipeline, wave model)
- `pax/.cca/catalogue/O0/20260626_orchestrator-rotation/ORCAST_BSIDE_DESIGN.md` (section 7 beat mapping, section 2 honesty constraints, section 8 viewer)
- `pax/.cca/catalogue/O0/20260626_orchestrator-rotation/HANDOFF_CHARTER.md` (locked items, return contract)

The pax registry already lists family `DEMO` (status chartered) pointing at the design
home. This charter is the orcast execution mirror; the orcast machine-readable entry is in
`docs/devpost/waves.registry.yaml`.

## Purpose

Produce two narrated videos plus gif loops, one A-side (public encounter forecasting) and
one B-side (research console). This waveset opens with W-STORY (the script lock) and the
first capturable beat. Needs-build beats wait on the B-side build order in
`ORCAST_BSIDE_DESIGN.md` section 6.

## Locked decisions, do not reopen

1. Honesty. Nothing unbuilt is shown as live. The forecast effective confidence is 0% and
   the gate caveat stays on screen wherever a forecast value appears. The live map forecast
   path is a hotspot heuristic, not the kernel model, so narration must not imply a
   validated forecast.
2. Capturable now versus needs build. Only B1, B2, B3 (and the A-side beats that already
   have surfaces) are capturable now. B4, B5, B6 wait on the build order.
3. Voice. Narration uses the orcast XTTS voice via `tools/testing/tts_narrate.py`.
4. Capture. Playwright at the fixed 1280x900 viewport (`web/playwright.config.ts`,
   `DEMO_RECORD=1`). Assembly uses the demo-video-assembly skill.
5. Surface. The console renders at the web app root route `/` (`web/app/page.tsx` ->
   `AdaptiveExplore.tsx` -> `ActiveSurfaceHost.tsx`), where the orchestrator trace,
   provenance pin, and hydrophone panels slot in by ui_intent.

## Waves

| Wave | Mode | Surface | Exit bar |
|------|------|---------|----------|
| W-STORY | build (docs) | `W-STORY.md` in this home | Beat order, per-beat shot list, one-line narration, and on-screen honesty captions locked for B1, B2, B3 |
| W-CAPTURE | build (capture) | `web/e2e/beats/bside-*.spec.ts`, webms to `docs/devpost/figures/_demo-run/beats/` | One silent webm per capturable beat at 1280x900, duration at least the narration length |
| W-VOICE | build (audio) | `docs/devpost/figures/_demo-run/narration/` | One mp3 per beat from the orcast XTTS voice, length at most the beat video |
| W-ASSEMBLE | build (mux) | `docs/devpost/figures/_demo-run/` | Two narrated videos (A-side, B-side) plus a gif-only set, A/V sync spot-checked |

W-STORY runs first and locks the script. W-CAPTURE and W-VOICE run in parallel after the
lock. W-ASSEMBLE runs last and depends on both. See `wave_shape.yml`.

## Operator approval gates

- Capture base URL: deployed `orcast-h0.vercel.app` (default `PW_BASE_URL`) versus a local
  stack. Operator picks before W-CAPTURE.
- Green-light to record any beat (W-CAPTURE).
- Any commit or push (orcast write policy: only on explicit operator request).
- The B-side build order (FastAPI tag endpoints and beyond) is a separate effort and is not
  authorized by this charter.

## Out of scope

- pax surfaces and the pax camera CV beats (B7, B8, B9); those belong to the pax lane.
- B4, B5, B6 capture until their build lands.
- The bathymetry viewer upgrade (design section 8), which gates A2 and B5.

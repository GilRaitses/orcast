# WS-INTENT step log

## 2026-06-27, Research and Discovery waves

Ran the Research wave then the Discovery wave, waves 1 and 2 of the six-wave
lifecycle. Read-only on code. Doc-producing only. No code or config touched, no dev
server, no commit, no other subagents.

### Read

- Program charter `PROGRAM_WAVESETS_CHARTER.md`, the original intent dispatch
  `W2_DISPATCH.md`, and the Director composition `VISUAL_DEFICIENCY_REGISTER.md`.
- Live code, `web/app/components/scene/SalishScene.tsx`,
  `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/adaptiveConsole.ts`,
  `web/lib/uiIntent.ts`, `web/lib/sceneIntent.ts`,
  `web/lib/scene/camera/` director, types, index, easing,
  `web/app/(sandbox)/journey/JourneyScene.tsx`, `web/lib/geo/gazetteer.ts`,
  `web/lib/scene/atmosphere/transition.ts`,
  `web/app/components/scene/SearchAffordance.tsx`,
  `web/app/components/scene/SceneHost.tsx`, `web/app/components/AdaptiveExplore.tsx`,
  and `web/app/components/scene/realism/applyRealism.ts`.

### Findings

- The `map_viewport` panel is text-only for three reasons in the live path. The panel
  renders as a muted paragraph in `ActiveSurfaceHost.renderPanel`. The live shell
  `AdaptiveExplore` never reads `mapViewportFromIntent(resp.ui_intent)`, only the
  request viewport. `SalishScene` has no camera controller, `focus` only drops a
  `FocusMarker` and `OrbitControls` is static at the origin.
- The W1 Camera Director is pure three.js and is already attached in the sandbox
  `JourneyScene.DirectorRig` through a mutable handle advanced in `useFrame`. That is
  the template for a single-editor bridge in `SalishScene`.
- The intent transducer feeds `director.getState()` into each planner turn on a
  throttle, via a director registry plus `enrichTurnContext(base)`, with an additive
  call in `adaptiveConsole.runAdaptiveTurn`.
- `runPlaceJourney` factors the sandbox beat over the W1 modules, parameterized by a
  gazetteer place, with fog-only atmosphere in the first pass to avoid touching the
  shared rig.
- The live realism rig has fog and background on by default, so the fog mask has a
  valid target live.

### Decisions and risks raised for the operator

- Closing the planner-to-camera loop needs a small additive edit to
  `AdaptiveExplore.tsx`, which the charter did not name. Recommended to claim it for
  WS-INTENT, pending the gate. Reduced acceptance recorded if declined.
- The lighting dim through `descentLighting` is deferred to WS-SCENIC to avoid touching
  the shared rig mount in this waveset.
- The no-dunk wave headroom assumes water amplitude near 0.18 to 0.32 units, carry a
  note to WS-BATHY if amplitude rises.
- `SearchAffordance.__SearchAffordanceStory` is a W1 throwaway, not wired live,
  stripping it is out of WS-INTENT scope.

### Deliverables produced

- `README.md`, `RESEARCH_SYNTHESIS.md`, `DISCOVERY_MAP.md`, `IMPLEMENTATION_DISPATCH.md`,
  this `STEP_LOG.md`.

### Gate status

- Research wave exit, the synthesis names concrete techniques and the W1 modules the
  implementation will use. Met.
- Discovery wave exit, the map lists every file to create or edit, its owner, and the
  integration seam, with no unowned convergence-file edits. Met, with one ownership
  confirmation flagged for `AdaptiveExplore.tsx`.
- Implementation wave, PROPOSED, pending the program-orchestrator gate.

## 2026-06-27 — Implementation COMPLETE (program batch)

Operator chose option 1 (WS-INTENT next). Investigation shows implementation already
landed in the 2026-06-27 console-journey batch — do not re-run.

Code (verified in repo):
- `web/lib/intent/transducer.ts` + `transducer.test.ts` — director registry,
  throttled sampler, `enrichTurnContext`.
- `web/lib/journey/controller.ts` + `controller.test.ts` — `runPlaceJourney` +
  cancel handle.
- `web/lib/adaptiveConsole.ts` — calls `enrichTurnContext` in turn/narration paths.
- `web/app/components/scene/SalishScene.tsx` — Viewport Bridge (DirectorRig,
  SearchAffordance, transducer register/clear, focus → journey).
- `web/app/components/AdaptiveExplore.tsx` — `mapViewportFromIntent(resp.ui_intent)`
  after `setPlan` (operator granted ownership 2026-06-27).

Acceptance: program Director visual gate PASS
(`../20260627_console-journey-trips/acceptance_screenshots/gate_search_*`,
`gate_rest`, `gate_zoom_rest_canvas`). WS-INTENT catalog docs synced to COMPLETE.

Remaining (not WS-INTENT blockers): TRIPS live anonymous route wiring (planner
allowed_panels + served config redeploy); optional formal WS-INTENT-only adversarial
register if the program wants per-waveset paper trail.

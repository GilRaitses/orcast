# WS-INTENT implementation dispatch (PROPOSED)

Status PROPOSED, pending the program-orchestrator gate. Nothing in this file is
executed by the suborchestrator. It proposes the phase-A producers and the phase-B
convergence editor for the WS-INTENT implementation wave, with task, deliverables,
validation, and collision-avoidance for each.

Discipline. One file one owner in phase A. The convergence file
`web/app/components/scene/SalishScene.tsx` has a single editor in phase B, who runs
after the phase-A producers land and type-check. No dev server during the parallel
phase. Producers commit, deploy, and promote nothing. Never `git add -A`. Secrets stay
in `.env`.

Sequencing. Phase A, parallel, Producer A Intent Transducer and Producer B Fly-through
Controller. Phase B, after A, Producer E Viewport Bridge on `SalishScene`, plus the
additive `AdaptiveExplore.tsx` read pending the ownership confirmation in
`DISCOVERY_MAP.md` section 3.

## Phase A, Producer A, Intent Transducer

Owns `web/lib/intent/transducer.ts`. Also makes an additive edit to
`web/lib/adaptiveConsole.ts`.

TASK. Build a React-free transducer that holds the active Camera Director and feeds
its sampled state into each planner turn. Expose a director registry,
`setActiveDirector(director)` and a clear, so the bridge can register the live
director on mount and clear it on unmount. Keep a throttled snapshot of
`director.getState()`, leading plus trailing, around 200 to 300 ms, so a burst of
frames produces at most a few reads. Expose `enrichTurnContext(base)` that merges the
latest sampled `target`, `altitude`, and `subject` into the turn's `viewport` and
`focus`, and returns the base unchanged when no director is attached. Make the
additive edit to `runAdaptiveTurn` in `adaptiveConsole.ts` so it calls
`enrichTurnContext(ctx)` before building the request body.

DELIVERABLES. `web/lib/intent/transducer.ts`. A minimal additive edit to the
turn-context builder in `web/lib/adaptiveConsole.ts`, one import plus one call, no
change to `PUBLIC_PLANNER_SPEC` or existing fields.

VALIDATION. Type-check. Unit test that a focused state and an orbiting state each
produce an enriched `focus` and `viewport`, that an unattached transducer returns the
base unchanged, and that the sampler throttles, many reads collapse to few snapshots.
No dev server.

COLLISION-AVOIDANCE. Do not edit `SalishScene.tsx`. Keep the `adaptiveConsole.ts`
change additive. Do not edit the camera modules. Do not touch `ActiveSurfaceHost.tsx`.

RETURN. Diff plus test output.

## Phase A, Producer B, Fly-through Controller

Owns `web/lib/journey/controller.ts`.

TASK. Factor the sandbox `JourneyScene` beat into a pure controller. Export
`runPlaceJourney(place, director, atmosphere)` that runs the beat, roll fog in as a
soft mask, `flyTo` an establishing altitude derived from `place.bounds`, roll fog back
out, `descendTo` a cruising altitude, `followPath` an approach route ending at the
place center, then `orbit` the center as the resting state. Derive the approach
polyline from the place center and bounds for an arbitrary place, with the option to
use a curated route for a known corridor. Take the atmosphere context as the fog
target plus a push sink for tweens, mirroring the sandbox `push(t)` into a per-frame
list. Guard a missing fog so the journey still runs. Return a cancel handle that stops
the active move, the orbit, and pushed tweens, so a later search supersedes an earlier
one. Pure orchestration over the W1 modules, no React.

DELIVERABLES. `web/lib/journey/controller.ts`, exporting `runPlaceJourney(place, director, atmosphere)`
and its cancel handle type.

VALIDATION. Type-check. Unit test over a fake director that records calls, asserting
the beat order flyTo then descendTo then followPath then orbit, that a derived
approach path ends at the place center, and that the cancel handle stops the sequence.
Confirm it composes against the real sandbox journey route at acceptance, no dev
server during the parallel phase.

COLLISION-AVOIDANCE. Do not edit `SalishScene.tsx`, the W1 camera modules, the
atmosphere module, or the gazetteer. Compose them. Label derived waypoints as
approximate lane points, not surveyed.

RETURN. Diff plus test output.

## Phase B, Producer E, Viewport Bridge (convergence single editor)

Owns `web/app/components/scene/SalishScene.tsx`. Pending ownership confirmation, also
makes the additive read in `web/app/components/AdaptiveExplore.tsx`.

TASK. Attach the Camera Director to the live scene camera and OrbitControls through a
mutable handle, modeled on `JourneyScene.DirectorRig`, in an inner component mounted
ahead of `Water2Rig`. Set `fitRadius` and a fit-accurate `worldUnitsPerMeter` on fit,
and widen `camera.near` and `camera.far`. Make the `focus` prop and the search
affordance drive `runPlaceJourney` on the live director instead of only dropping a
marker, keep `FocusMarker` as a secondary cue, and disable then re-enable
OrbitControls around a scripted journey. Mount `SearchAffordance` as an overlay over
the canvas and wire `onSearch` to `resolvePlace` then `runPlaceJourney`. Register the
live director with the transducer on mount and clear it on unmount. Run the journey
atmosphere fog-only through `scene.fog` in this pass. In `AdaptiveExplore.tsx`, after
`setPlan(resp)`, read `mapViewportFromIntent(resp.ui_intent)` and set `focus` so a
planner-returned `map_viewport` reaches the camera.

DELIVERABLES. Edits to `SalishScene.tsx`, plus the additive read in
`AdaptiveExplore.tsx` if the ownership is confirmed. Register nothing else. Do not
refactor the rig section.

VALIDATION. Type-check. A real visual check at acceptance, read the rendered frames,
not just the code. Searching a gazetteer place flies the live console camera through
the beat. A planner turn returning `map_viewport` moves the camera. The marker still
appears as a secondary cue. The camera never dunks below the surface. Capture
screenshots of the search-driven journey and the turn-driven move and read them before
claiming the fix.

COLLISION-AVOIDANCE. Only WS-INTENT editor of `SalishScene.tsx` in this calendar slot,
run after phase A merges and type-checks. Touch only camera, controls, search, and
focus wiring. Leave `RealismRig`, `Water2Rig`, and the tiles mount stable for WS-SCENIC
and WS-BATHY. Do not edit `ActiveSurfaceHost.tsx`. Do not enable the realism lights
handle path in this pass, defer the lighting dim to WS-SCENIC.

RETURN. Diff plus inspected screenshots of the search-driven and turn-driven camera
moves.

## Gate checklist for the program orchestrator

- Confirm the `AdaptiveExplore.tsx` additive edit ownership for WS-INTENT, or accept
  the reduced acceptance in `DISCOVERY_MAP.md` section 3.
- Confirm phase A and phase B sequencing on the convergence calendar, INTENT first on
  `SalishScene.tsx`.
- Confirm the fog-only atmosphere scope for this pass, with the lighting dim deferred
  to WS-SCENIC.
- Confirm the honesty labels carried into any served camera or search copy.

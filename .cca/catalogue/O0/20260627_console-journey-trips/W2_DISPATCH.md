# W2 dispatch: intent loop + connections clients

Status: blocked on W1. Discipline unchanged from W1. Convergence file `SalishScene.tsx` has a single
editor (Viewport Bridge), who runs in phase B after the phase-A producers land.

## Sequencing
- Phase A (parallel): Intent Transducer, Fly-through Choreography, WSF Client, WSDOT Traffic Client.
- Phase B (after A): Viewport Bridge wires the Camera Director + choreography + search into `SalishScene`.

## Agent A — Intent Transducer (owns web/lib/intent/transducer.ts; phase A; also edits adaptiveConsole.ts turn builder)
YOUR TASK: Sample Camera Director `getState()` (target, altitude, dwell, orbit subject) and enrich each
planner turn's `focus` / `viewport` context. Throttle so it does not spam turns. Expose
`enrichTurnContext(base)`.
DELIVERABLES: `web/lib/intent/transducer.ts`; a minimal, clearly-scoped edit to the turn-context
builder in `web/lib/adaptiveConsole.ts` (additive only).
VALIDATION: type-check; unit test that a focused/orbiting state produces enriched `focus`.
COLLISION-AVOIDANCE: do not edit `SalishScene.tsx`. Keep the `adaptiveConsole.ts` change additive.
RETURN: diff + test output.

## Agent B — Fly-through Choreography (owns web/lib/journey/controller.ts; phase A)
YOUR TASK: A controller that, given a resolved place, runs the beat: `rollInFog` -> `descendTo(~50 ft)`
-> `followPath(ferryRoute)` -> `orbit(center)`. Pull the ferry route geometry from the gazetteer / a
static polyline. Pure orchestration over the W1 modules.
DELIVERABLES: `web/lib/journey/controller.ts`. Exports `runPlaceJourney(place, director, atmosphere)`.
VALIDATION: type-check; runs end to end in the sandbox journey route.
COLLISION-AVOIDANCE: do not edit `SalishScene.tsx` or the W1 modules; compose them.
RETURN: diff + inspected sandbox recording of the full beat.

## Agent C — WSF Client (owns src/aws_backend/sources/wsf.py; phase A)
YOUR TASK: Implement `vessel_locations()`, `schedule(route_id, date)`, `sailing_space(terminal_id=None)`,
`wait_times(terminal_id=None)` against the WSF REST API; access code from `WSDOT_ACCESS_CODE` env.
Parse the fields listed in `CONNECTIONS_RESEARCH.md`. Graceful failure when the code is absent.
DELIVERABLES: `src/aws_backend/sources/wsf.py` + a pytest using recorded fixtures (no live calls in CI).
VALIDATION: pytest green on fixtures; one manual live smoke documented (not in CI).
COLLISION-AVOIDANCE: own ONLY this file + its test.
RETURN: diff + pytest output.

## Agent D — WSDOT Traffic Client (owns src/aws_backend/sources/wsdot_traffic.py; phase A)
YOUR TASK: `travel_times()` and `traffic_flows()` against the Traveler API; plus `append_history(record)`
that writes corridor readings to an appendable log (gitignored data path) for the W3 model. Access code
from env.
DELIVERABLES: `src/aws_backend/sources/wsdot_traffic.py` + fixture pytest.
VALIDATION: pytest green on fixtures; the SeaTac<->Anacortes travel-time route ids resolved and logged.
COLLISION-AVOIDANCE: own ONLY this file + its test.
RETURN: diff + pytest output.

## Agent E — Viewport Bridge (owns web/app/components/scene/SalishScene.tsx; phase B; single editor)
YOUR TASK: Attach the Camera Director to the scene camera + OrbitControls via a ref; make the
`map_viewport` ui_intent and the search affordance drive `runPlaceJourney` instead of only dropping a
marker. Keep the marker as a secondary cue. Mount `SearchAffordance`.
DELIVERABLES: edits to `SalishScene.tsx` only; register nothing else.
VALIDATION: type-check; on the live console, searching a gazetteer place flies the camera through the
beat, and a planner turn returning `map_viewport` moves the camera. Read the rendered result.
COLLISION-AVOIDANCE: you are the ONLY W2 editor of `SalishScene.tsx`; run after phase A merges.
RETURN: diff + inspected screenshots of search-driven and turn-driven camera moves.

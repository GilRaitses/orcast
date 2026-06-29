# WS-INTENT, the console intent loop (the spine)

Suborchestrator home for waveset WS-INTENT in the Console Journey + Trips program.
This waveset makes the dead `map_viewport` ui_intent and the search affordance drive
the live console camera, by attaching the W1 Camera Director to `SalishScene` and
factoring the sandbox fly-through into a reusable controller.

## Scope of THIS task

Research, Discovery, Implementation, and program-level Acceptance are **COMPLETE**.
The code landed in the 2026-06-27 console-journey batch implementation (phase A +
SalishScene convergence). Formal per-waveset Adversarial/Remediation were folded
into the program Director visual gate (`../20260627_console-journey-trips/STEP_LOG.md`,
`acceptance_screenshots/gate_search_*`).

## The six-wave lifecycle (this waveset)

1. Research. **DONE** — `RESEARCH_SYNTHESIS.md`.
2. Discovery. **DONE** — `DISCOVERY_MAP.md`.
3. Implementation. **DONE** — `web/lib/intent/transducer.ts`, `web/lib/journey/controller.ts`,
   additive `adaptiveConsole.ts`, Viewport Bridge in `SalishScene.tsx`, additive
   `AdaptiveExplore.tsx` (`mapViewportFromIntent` after `setPlan`).
4. Adversarial. **Folded into program batch** (no separate `DEFECT_REGISTER.md` here).
5. Remediation. **N/A** (no WS-INTENT-specific defects filed separately).
6. Acceptance. **PASS** at program level — search-driven journey screenshots
   `gate_search_00..05`; turn-driven camera via `map_viewport` wiring in
   `AdaptiveExplore.tsx`.

## Convergence file and calendar position

The convergence file is `web/app/components/scene/SalishScene.tsx`, edited in
implementation phase B by a single editor (the Viewport Bridge). In the program
convergence calendar this file is serialized INTENT first, then SCENIC, then BATHY.
WS-INTENT runs first, so the bridge touches only camera, controls, search, and focus
wiring and leaves the realism and water rig mount stable for the later visual
wavesets.

## Locked decisions carried in

- B.1 extend the live console, no new route or engine.
- B.2 make the dead `map_viewport` seam live (this is the waveset).
- B.6 honesty labels travel with every served surface.
- B.7 implicit-intent feed from sampled camera state into each planner turn.
- B.8 one file one owner, convergence single editor, no dev server in a parallel phase.
- B.9 no promotion.
- B.10 agents commit, deploy, and promote nothing.

## Acceptance criteria (for later waves)

- Searching a gazetteer place flies the live console camera through the beat.
- A planner turn returning `map_viewport` moves the live camera.
- The marker stays as a secondary cue, not the only response.
- Honesty labels hold. Approach waypoints are approximate lane points, not surveyed.

## Files in this home

- `README.md` this overview.
- `RESEARCH_SYNTHESIS.md` how the seam works today and the bridge techniques.
- `DISCOVERY_MAP.md` the integration seams and the one file one owner table.
- `IMPLEMENTATION_DISPATCH.md` phase-A/B prompts (executed 2026-06-27 program batch).
- `STEP_LOG.md` the running log for this waveset.

## Status: COMPLETE

Implementation + acceptance recorded under
`../20260627_console-journey-trips/STEP_LOG.md` (2026-06-27 late). Do not
re-run implementation unless a regression is found.

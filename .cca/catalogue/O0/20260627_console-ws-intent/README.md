# WS-INTENT, the console intent loop (the spine)

Suborchestrator home for waveset WS-INTENT in the Console Journey + Trips program.
This waveset makes the dead `map_viewport` ui_intent and the search affordance drive
the live console camera, by attaching the W1 Camera Director to `SalishScene` and
factoring the sandbox fly-through into a reusable controller.

## Scope of THIS task

Research wave and Discovery wave only (waves 1 and 2 of the six-wave lifecycle).
Read-only on code. The deliverables are Markdown docs in this folder plus a PROPOSED
implementation dispatch for the program orchestrator to gate. No code or config is
created or edited, no dev server is run, nothing is committed, and no other
subagents are launched.

## The six-wave lifecycle (this waveset)

1. Research. Done here. Output `RESEARCH_SYNTHESIS.md`.
2. Discovery. Done here. Output `DISCOVERY_MAP.md`.
3. Implementation. PROPOSED here in `IMPLEMENTATION_DISPATCH.md`, pending the gate.
4. Adversarial. Not started.
5. Remediation. Not started.
6. Acceptance. Not started.

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
- `IMPLEMENTATION_DISPATCH.md` PROPOSED phase-A and phase-B prompts, pending gate.
- `STEP_LOG.md` the running log for this waveset.

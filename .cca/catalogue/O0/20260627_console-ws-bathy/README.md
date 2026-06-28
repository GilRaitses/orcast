# WS-BATHY, bathymetry layout (special teams, below the water)

Home: `.cca/catalogue/O0/20260627_console-ws-bathy/`
Suborchestrator scope: the seafloor and the water-over-terrain reading of the live console scene.
Date opened: 2026-06-27.
Status: Research wave and Discovery wave COMPLETE (read-only). Implementation is PROPOSED and held for the program orchestrator gate. No code, config, dev server, commit, or subagent launched by this task.

## What this waveset owns

Make the seafloor and the depth-driven water read correctly and truthfully. Four special teams, per `PROGRAM_WAVESETS_CHARTER.md` section 2.

- Bathy Data Engineer. Source and curate seafloor bathymetric data for the served extent, label measured vs modeled provenance.
- Bathy Terrain Builder. Represent the underwater terrain field the depth-driven water reads, reconciled with the CUDEM substrate.
- Water and Depth Stylist. Tune the depth-driven water and substrate so shoals, channels, and depth read truthfully.
- Honesty Labeler. Ensure measured vs modeled bathymetry is labeled on every surface, no invented depths presented as measured.

## Locked constraints carried into this waveset

- B.1 extend the live console, no new engine.
- B.6 honesty, measured vs modeled bathymetry must be labeled, no invented depths presented as measured.
- B.8 one file, one owner.
- B.10 agents commit, deploy, and promote nothing.
- Convergence calendar, section 4: `SalishScene.tsx` is edited by one waveset at a time in the order INTENT then SCENIC then BATHY. WS-BATHY mounts its pure modules LAST, after SCENIC. `water2/` and `substrate/` internals stay owned by their existing modules. WS-BATHY adds new sibling modules and reads the existing public surface, it does not edit internals.

## Headline finding (resolved from the data)

The served CUDEM tileset IS topobathy. The seafloor geometry is already baked into the render tiles, so the depth-driven water reads a real modeled seabed, not a flat floor. No separate measured seabed mesh is required for the water to read depth. See `RESEARCH_SYNTHESIS.md` section 1 and `DISCOVERY_MAP.md` section 1.

## Documents in this home

- `RESEARCH_SYNTHESIS.md`. Research wave output. The live underwater stack read, the bathy data source survey with provenance and licence, and the depth-rendering technique recommendation, all cited.
- `DISCOVERY_MAP.md`. Discovery wave output. What water2 and substrate already provide and their public surface, where the new bathy modules slot, the one-file-one-owner table with owners and seams, and the honesty label each surface must carry.
- `IMPLEMENTATION_DISPATCH.md`. PROPOSED phase-A producer prompts plus the phase-B scene-mount step, each with task, deliverables, validation, and collision avoidance. Held for the gate.
- `STEP_LOG.md`. Wave-by-wave log.

## Gate state

- Research gate: PASSED. The synthesis names concrete techniques and sources the implementation can use, with citations.
- Discovery gate: PASSED. The map lists every file to be created or edited, its owner, and the integration seam, with no unowned convergence-file edits proposed.
- Implementation gate: NOT ENTERED. This task ends with the proposed dispatch for the program orchestrator to gate and serialize on `SalishScene.tsx`.

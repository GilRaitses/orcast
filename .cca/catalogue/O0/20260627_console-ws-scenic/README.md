# WS-SCENIC, scene realism and decoration above the water (waveset home)

Suborchestrator home for WS-SCENIC in the orcast Console program. WS-SCENIC makes
the world look right above sea level. Two roles report to the Director.

- Terrain Stylist. Land materials, landcover and vegetation treatment, terrain
  texturing and shading so the CUDEM islands read as living land rather than bare
  tan relief. Owns a new terrain material module. Reads the realism public
  surface and the tiles material hooks. Does not own realism internals.
- Scenic Decorator. Horizon surrounding geometry beyond the served CUDEM extent so
  the horizon is not empty water, atmospheric depth, and sky/fog/haze refinement
  as set dressing. Owns a new horizon and atmosphere decor module.

## Files

- `README.md`, this file.
- `RESEARCH_SYNTHESIS.md`, the Research wave output. Cited external techniques and
  open-data sources for land materials, vegetation, horizon geometry, and sky/fog,
  with a recommendation per problem and the licensing and performance notes.
- `DISCOVERY_MAP.md`, the Discovery wave output. What the live realism rig already
  provides and its public surface, where the two new modules slot, the SalishScene
  rig-mount seam, and the one-file-one-owner table with owners, seams, and honesty
  labels.
- `IMPLEMENTATION_DISPATCH.md`, the proposed phase-A producer prompts and the
  phase-B scene-mount step for the program orchestrator to gate. Marked PROPOSED.
- `STEP_LOG.md`, the wave trace, newest last.

## State (2026-06-27)

Research wave and Discovery wave COMPLETE, read-only, doc-producing. No code or
config was created or edited. No dev server ran. Nothing committed. The next gate
is the program orchestrator's go on the proposed implementation dispatch, and the
convergence calendar slot for the SalishScene rig mount, which runs after INTENT
and before BATHY.

## Locked constraints carried into this waveset

- B.1, extend the live console, no new engine.
- The scene is the real CUDEM tileset at sea level Y equals 0.
- Any added distant geometry is labeled decorative, not surveyed.
- Fog is a labeled atmosphere effect.
- B.6, no invented place data.
- B.8, one file, one owner.
- B.10, agents commit, deploy, and promote nothing.

## Lineage

- Program charter, `.cca/catalogue/O0/20260627_console-journey-trips/PROGRAM_WAVESETS_CHARTER.md`.
- Director standard, `.cca/catalogue/O0/20260627_console-journey-trips/VISUAL_PROGRAM_CHARTER.md`.
- Deficiency register, `.cca/catalogue/O0/20260627_console-journey-trips/VISUAL_DEFICIENCY_REGISTER.md`.

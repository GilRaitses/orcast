# WS-SCENIC Step Log

Newest last. Read-only, doc-producing waveset. No code or config edited, no dev
server, no commit.

## 2026-06-27, Research wave

- Read the program charter, the visual program charter, and the visual deficiency
  register to fix scope, the Director standard, and what is already present.
- Read the live visual stack. Realism rig `applyRealism`, `atmosphere.ts`,
  `sun.ts`, `palette.ts`, `index.ts`. Tiles hook `useTilesLayer.ts` and its wiring
  doc. The convergence scene `SalishScene.tsx`. The journey scene `JourneyScene.tsx`.
  The water2, substrate, camera, and atmosphere-transition public surfaces, and
  `sceneIntent.ts` for the scene frame math.
- Established the scene frame, `SCENE_WIDTH` 120, tileset fit to diameter 120, true
  relief, about 0.0024 units per metre, live far plane 800, served footprint lat
  48.40 to 48.70, lng -123.25 to -122.75, about 24.8 km half-diagonal. These anchor
  the horizon-ring distance and height numbers.
- Web-searched current techniques and confirmed sources for, terrain biome tinting
  by slope and height shaders, ESA WorldCover and USGS NLCD landcover with licenses,
  AWS Terrain Tiles open DEM for distant geometry, instanced and impostor
  vegetation, the core three Preetham `Sky` object, and `@takram/three-atmosphere`
  precomputed scattering.
- Wrote `RESEARCH_SYNTHESIS.md` with a recommendation per problem, licensing and
  provenance, and the performance budget.
- Gate. The synthesis names concrete techniques and open-data sources the
  implementation can use. Passed.

## 2026-06-27, Discovery wave

- Mapped the realism rig public surface the new modules reuse, and confirmed the
  files WS-SCENIC must not touch, `realism/` internals, `tiles/` internals,
  `water2/`, `substrate/`.
- Confirmed the tiles material override path, register an extra `load-model` and
  `dispose-model` listener and use `forEachLoadedModel` on the returned
  `TilesRenderer`, so the tiles hook stays a single owner.
- Placed the two new modules, `web/lib/scene/terrain/` for the Terrain Stylist and
  `web/lib/scene/decor/` for the Scenic Decorator, matching the existing
  framework-free factory layout.
- Identified the SalishScene rig-mount seam inside `TwinScene`, phase B, single
  SCENIC editor, scheduled after INTENT and before BATHY, plus the parallel journey
  mount in the sandbox `JourneyScene.tsx`.
- Wrote `DISCOVERY_MAP.md` with the one-file-one-owner table, owners, seams, and the
  honesty label each surface carries, and the open seams for the gate.
- Gate. The map lists every file to create or edit, its owner, and the integration
  seam, with no unowned convergence-file edit. Passed.

## 2026-06-27, Proposed dispatch

- Wrote `IMPLEMENTATION_DISPATCH.md`, two phase-A producer prompts and the phase-B
  scene-mount step, each with task, deliverables, type-check validation, a deferred
  real rendered-frame check at acceptance read by the Director, and
  collision-avoidance. Marked PROPOSED.
- Recorded the decisions and risks for the operator, landcover imagery source,
  horizon source, sky model, background ownership, and the vegetation performance
  tradeoff.
- Next gate. Program orchestrator go on the dispatch and the SCENIC convergence-
  calendar slot for the SalishScene edit.

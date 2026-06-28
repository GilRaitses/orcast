# WS-SCENIC Implementation Dispatch (PROPOSED)

Status PROPOSED. Nothing here is launched. The program orchestrator gates this and
schedules the phase-B SalishScene edit into the SCENIC slot of the convergence
calendar, after INTENT and before BATHY.

Execution shape. Two phase-A producers build pure modules in parallel under
one-file-one-owner. They share no files, so they run at the same time. One phase-B
mount step then wires both into the scene, as the single SCENIC editor of the
convergence file. Validation in phase A is type-check only, no dev server. The
real rendered-frame visual check happens at the phase-B acceptance gate and is read
by the Director.

Locked constraints for every producer. Extend the live console, no new engine, B.1.
The scene is the real CUDEM tileset at sea level Y equals 0. Added distant geometry
is labeled decorative, not surveyed. Fog is a labeled atmosphere effect. No invented
place data, B.6. One file, one owner, B.8. Commit, deploy, and promote nothing,
B.10. Do not add an npm dependency. Do not edit `realism/` internals, `tiles/`
internals, `water2/`, `substrate/`, or `SalishScene.tsx` in phase A.

## Phase A, producer 1, Terrain Stylist (owns `web/lib/scene/terrain/`)

TASK. Build a pure, framework-free module that makes the streamed CUDEM tile
surface read as living, materially-correct land instead of bare tan relief, by
restyling tile materials with an elevation-and-slope biome tint, without changing
tile geometry, transforms, or the tiles hook. Reuse the realism palette so the tint
stays in the live color family. Consume the `TilesRenderer` instance through the
public `3d-tiles-renderer` API only.

DELIVERABLES.
- `web/lib/scene/terrain/terrainStylist.ts` exporting
  `applyTerrainStyle(tiles, opts)` that returns `{ dispose(): void }`. It registers
  a `load-model` listener and a `dispose-model` listener on `tiles`, calls
  `forEachLoadedModel` once to restyle tiles already streamed, and for each tile
  mesh injects, by `material.onBeforeCompile`, a fragment tint that blends a forest
  green near `LAND_LOW` on low flat ground, a drier grass-tan at mid elevation, a
  rock gray on steep slope using a `dot(worldNormal, up)` slope term, and a narrow
  shoreline band just above Y equals 0. Expose options for the slope threshold and
  softness, the shoreline band height, roughness, and an optional normal scale.
  `dispose()` removes the listeners and disposes any material the module created.
- `web/lib/scene/terrain/index.ts`, barrel.
- `web/lib/scene/terrain/WIRING-terrain.md`, the integrator contract, the mount
  steps, and the honesty statement that the tint is derived from the rendered CUDEM
  height and slope and is interpretive color, not a vegetation survey.
- Do not build `landcover.ts` unless the operator approves the ESA WorldCover drape
  decision. If approved, add `web/lib/scene/terrain/landcover.ts` and carry the
  CC BY 4.0 attribution string in `WIRING-terrain.md` and in the sampler
  `userData`.

VALIDATION.
- `cd web && npm run typecheck` exits 0, or `cd web && npx tsc --noEmit` exits 0.
- A unit-level check that `applyTerrainStyle` registers and, on `dispose`, removes
  its listeners against a stub `TilesRenderer`, and that a stub mesh material runs
  through `onBeforeCompile` without throwing.
- The real rendered-frame check is deferred to the phase-B acceptance gate, read by
  the Director, no screenshot claimed unseen.

COLLISION-AVOIDANCE. You own only `web/lib/scene/terrain/`. Do not edit
`useTilesLayer.ts` or anything in `tiles/`, do not edit `realism/`, do not edit
`SalishScene.tsx` or `JourneyScene.tsx`. Access tiles only through the instance the
caller passes. Return a diff summary and the type-check output.

## Phase A, producer 2, Scenic Decorator (owns `web/lib/scene/decor/`)

TASK. Build a pure, framework-free module that frames the horizon and refines the
sky and haze as set dressing. Add a physical sky with a sun disc and horizon glow, a
true-scale decorative terrain ring beyond the served extent so the horizon is not
empty water, and optional fog tuning. Drive everything from the existing
`makeSun().direction` and the realism sky and haze tints so the sky, the light, and
the water agree. Label all added distant geometry decorative, not surveyed, and the
fog an atmosphere effect.

DELIVERABLES.
- `web/lib/scene/decor/sky.ts` exporting `makeSkyDome(opts)` returning
  `{ object3D, setSun(direction): void, dispose(): void }`, wrapping
  `three/addons/objects/Sky.js`, the core Preetham sky, configured with
  `turbidity`, `rayleigh`, `mieCoefficient`, `mieDirectionalG`, and `sunPosition`
  from the passed sun direction, with a flat-gradient fallback dome option for
  low-end devices. One dome mesh, no post-processing. No new npm dependency, the Sky
  object is a vendored three addon.
- `web/lib/scene/decor/horizonRing.ts` exporting `makeHorizonRing(opts)` returning
  `{ object3D, dispose() }`, a low-poly decorative terrain ring built once from a
  small low-zoom AWS Terrain Tiles DEM fetch, placed at true bearing and true scale
  around the origin using the `worldUnitsPerMeter` convention, outer edge skirted
  below sea level, sharing the scene fog so it fades into the horizon. Tag
  `object3D.userData.decorativeNotSurveyed = true`, `object3D.userData.label`, and
  `object3D.userData.source` with the AWS Terrain Tiles provenance, exactly as
  `buildSubstrateOverlay` tags its overlay. Provide a billboard-silhouette fallback
  behind an option for low-end devices. Default the ring radius at or below about
  300 units so it stays inside the live far plane.
- `web/lib/scene/decor/fogTuning.ts` optional, exporting a helper that retunes the
  passed `scene.fog` near, far, and color, or swaps to `THREE.FogExp2`, reusing the
  tweens in `web/lib/scene/atmosphere/transition.ts`. Operates on the passed fog
  only.
- `web/lib/scene/decor/index.ts`, barrel.
- `web/lib/scene/decor/WIRING-decor.md`, the integrator contract, the mount steps,
  the background-ownership recommendation, and the honesty statements.

VALIDATION.
- `cd web && npm run typecheck` exits 0, or `cd web && npx tsc --noEmit` exits 0.
- A unit-level check that `makeSkyDome().setSun(dir)` updates the sky `sunPosition`
  uniform, and that `makeHorizonRing()` returns an object tagged
  `userData.decorativeNotSurveyed === true` with a non-empty provenance label.
- The real rendered-frame check is deferred to the phase-B acceptance gate, read by
  the Director.

COLLISION-AVOIDANCE. You own only `web/lib/scene/decor/`. Do not edit `realism/`,
do not edit `tiles/`, do not edit `SalishScene.tsx` or `JourneyScene.tsx`. Read
`makeSun`, `skyColor`, `fogColorForSky` from the realism barrel and
`projectToScene`, `SCENE_WIDTH` from `sceneIntent`. Return a diff summary and the
type-check output.

## Phase B, scene-mount step, single SCENIC editor (owns the SalishScene edit)

Runs only after both phase-A producers land green, and only in the SCENIC slot of
the convergence calendar, after INTENT, before BATHY.

TASK. Wire the two new modules into the live scene and the journey scene without
editing any module internals. Mount the terrain stylist on the live `tiles`
instance, mount the Sky dome and the horizon ring, optionally retune the fog, and
set background ownership.

DELIVERABLES.
- Edit `web/app/components/scene/SalishScene.tsx`, inside `TwinScene`. Add a
  terrain-stylist effect that calls `applyTerrainStyle(tiles, opts)` once `tiles`
  exists and disposes on unmount. Add a `<primitive>` for the Sky dome and a
  `<primitive>` for the horizon ring, both driven by the pinned `SCENE_TIME` sun the
  rig already builds. Recommended background ownership, call
  `applyRealism({ background: false })` in `RealismRig` and let the Sky dome own the
  background, so the two do not fight. Optionally call the fog tuning against
  `scene.fog`.
- Edit `web/app/(sandbox)/journey/JourneyScene.tsx`, the parallel mount of the same
  three rigs so the journey beats show the same vegetated land and framed horizon.
- Update the deficiency register rows for terrain materials, horizon geometry, and
  sky once the frames are read.

VALIDATION.
- `cd web && npm run typecheck` exits 0.
- Real rendered-frame visual check at acceptance, read by the Director, not the
  builder. The Director inspects captured frames for, one, low flat CUDEM ground
  reading as vegetated green and steep faces reading as rock with a shoreline band,
  two, a framed horizon with surrounding terrain in the Olympics, Cascades, and
  Vancouver Island bearings rather than empty water, three, a coherent sky with a
  sun disc and horizon glow and haze that matches the sun side, four, the honesty
  note holding, real CUDEM, fog labeled atmosphere, distant geometry labeled
  decorative. No fix is claimed without reading the frame.

COLLISION-AVOIDANCE. This is the single SCENIC edit to `SalishScene.tsx`. Confirm
INTENT has released the file and BATHY has not started it. Do not edit `realism/`,
`tiles/`, `water2/`, or `substrate/` internals. No commit, no deploy, no promote.

## Decisions and risks needing operator input

- Landcover imagery source. Ship the derived biome tint alone, the cheapest honest
  path, or approve the optional ESA WorldCover 2021 drape, CC BY 4.0, which adds a
  hosted cropped raster and an attribution surface and richer place-true cover. ESA
  WorldCover is recommended over USGS NLCD because NLCD stops at the US border and
  the extent includes Canadian Gulf Islands.
- Horizon source. True-scale decorative DEM ring from AWS Terrain Tiles, recommended
  because the journey's high establishing shot would expose flat billboards, versus
  the lighter billboard-silhouette fallback for low-end devices.
- Sky model. Core three Preetham `Sky` object, recommended, no new dependency,
  versus `@takram/three-atmosphere` precomputed scattering, which is more physical
  but adds a dependency and a post-processing pipeline that collides with the
  water2 depth pre-pass and the no-new-engine lock, so it is deferred.
- Background ownership at the SalishScene seam. Sky dome owns the background with
  realism `background: false`, recommended, versus keeping the realism flat
  background behind the dome.
- Performance tradeoff on vegetation. Discrete instanced or billboard vegetation is
  deferred because it competes with tile streaming and the water depth pre-pass for
  the frame budget. If the operator wants it, scope it small, chunked, impostor in
  the far field, behind a toggle, and labeled decorative.

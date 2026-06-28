# WS-SCENIC Discovery Map

Discovery wave for WS-SCENIC. Read-only, doc-producing. This map grounds the
research in the live codebase. It records the realism rig public surface the two
new modules reuse, the tiles material hook they consume, where the new modules
slot, the SalishScene rig-mount seam, and the one-file-one-owner table with owners,
seams, and honesty labels. No unowned convergence-file edit is proposed here.

## 1. What the realism rig already provides, and its public surface

The realism rig is `web/app/components/scene/realism/`, mounted imperatively by
`applyRealism(scene, opts)`. WS-SCENIC reuses it through the barrel
`web/app/components/scene/realism/index.ts` and does not edit any file inside
`realism/`.

Public surface, what the decorator and stylist may import.

- `applyRealism(scene, opts)` returns a `RealismHandle` with `sunLight`,
  `ambientLight`, `hemisphereLight`, `water`, `sun`, `update(elapsedSeconds)`,
  `setDate(date)`, and `dispose()`. The handle is the supported way to read the
  live sun and lights.
- `makeSun(date, lat, lng)` returns a `SunResult` with `direction`, `elevationDeg`,
  `azimuthDeg`, `color`, `intensity`, and `ambientIntensity`. This is the single
  sun source. The decorator drives the Sky `sunPosition` from `direction` and tints
  the horizon haze from `elevationDeg` and `azimuthDeg`.
- `skyColor(elevationDeg)` and `fogColorForSky(sky)` give the elevation-driven sky
  color and the sea-haze fog tint. The decorator reuses these so the new sky dome
  and the new fog tuning agree with the rest of the scene.
- `makeFog(opts)` returns a linear `THREE.Fog`. `applyRealism` sets `scene.fog` and
  `scene.background` itself. The decorator must not re-enter `applyRealism`; it
  either reads and retunes the live `scene.fog` object, or the phase-B integrator
  passes `background: false` to `applyRealism` and lets the sky dome own the
  background. This is a seam decision recorded in section 4.
- Palette, `LAND_LOW` `#3f6b3a`, `LAND_HIGH` `#9aa886`, `WATER_SHALLOW`,
  `WATER_DEEP`, `WATER_SURFACE_TINT`, plus `landElevationColor(elevMeters)` and
  `oceanDepthColor(depthMeters)`. The Terrain Stylist reuses `LAND_LOW`,
  `LAND_HIGH`, and `landElevationColor` so the biome tint stays in the live family.

What WS-SCENIC must not touch. Every file inside `realism/`, the water2 module
`web/lib/scene/water2/`, and the substrate module internals. WS-SCENIC adds new
sibling modules and reads these public surfaces only.

## 2. The tiles material hook the Terrain Stylist consumes

The tiles layer is `web/lib/scene/tiles/useTilesLayer.ts`, owned by
`web/lib/scene/tiles/`. It constructs a `3d-tiles-renderer` `TilesRenderer`, mounts
`tiles.group` with a `<primitive>`, and returns the live `TilesRenderer` instance.
Tile meshes load with their glТF standard materials, and the hook already attaches a
`load-model` listener to set `castShadow` and `receiveShadow`.

The Terrain Stylist consumes the returned `TilesRenderer` through the public
`3d-tiles-renderer` API, not by editing the hook. The supported override pattern,
documented in the NASA-AMMOS 3DTilesRenderer USAGE guide, is to register an
additional `load-model` listener and traverse `scene` to restyle or replace each
mesh material, and a `dispose-model` listener to dispose any material the stylist
created. The stylist also reuses `forEachLoadedModel` to restyle tiles already
streamed when it mounts. Because the stylist only calls `addEventListener` and
`forEachLoadedModel` on the instance the hook returns, the tiles hook stays a single
owner and is never edited.

Frame note. The tiles fit math and the journey altitude derivation depend on the
tile bounding sphere, so the stylist must not change tile geometry or transforms. It
restyles materials only.

## 3. Where the new modules slot

Two new sibling module trees, both under `web/lib/scene/`, matching the existing
`water2`, `substrate`, and `camera` layout and the framework-free factory style of
`makeWater2` and `applyRealism`.

### 3.1 Terrain Stylist module, new, `web/lib/scene/terrain/`

- `terrainStylist.ts`, exports `applyTerrainStyle(tiles, opts)` returning a handle
  with `dispose()`. It registers a `load-model` and `dispose-model` listener on the
  passed `TilesRenderer`, restyles each tile `MeshStandardMaterial` with an
  elevation-and-slope biome tint by `onBeforeCompile` injection, sets roughness and
  optional normal scale, and reuses the realism palette. Pure with respect to
  `realism/` and `tiles/`, framework-free, no React.
- `index.ts`, barrel re-export of `applyTerrainStyle` and its options type.
- `WIRING-terrain.md`, the integrator-facing contract and mount steps, mirroring
  `WIRING-tiles-layer.md`.
- Optional `landcover.ts`, only if the operator approves the ESA WorldCover drape.
  Loads the cropped landcover raster, builds a projected color and roughness
  sampler keyed to `projectToScene`, and feeds the biome tint. Flagged in the
  dispatch, not built by default.

The module reads the realism public surface for palette and the `3d-tiles-renderer`
public API for material access. It depends on `web/lib/sceneIntent.ts` only for
`projectToScene`, `SCENE_WIDTH`, and the bounds type if the optional landcover drape
is built.

### 3.2 Scenic Decorator module, new, `web/lib/scene/decor/`

- `sky.ts`, exports `makeSkyDome(opts)` returning `{ object3D, setSun(direction),
  dispose() }`, wrapping `three/addons/objects/Sky.js` configured from
  `makeSun().direction` and the realism sky and haze tints, with a flat-gradient
  fallback dome for low-end devices. One dome mesh, no post-processing.
- `horizonRing.ts`, exports `makeHorizonRing(opts)` returning `{ object3D,
  dispose() }`, a true-scale decorative low-poly terrain ring built once from a
  small low-zoom AWS Terrain Tiles DEM, placed at true bearing and scale around the
  origin, sharing `scene.fog`, tagged `userData.decorativeNotSurveyed = true` and
  `userData.label` exactly as `buildSubstrateOverlay` tags its overlay, so any UI
  built from the scene graph surfaces the honesty label. A billboard-silhouette
  fallback is documented behind an option.
- `fogTuning.ts` optional, a thin helper that retunes the live `scene.fog` near,
  far, color, or swaps to `THREE.FogExp2`, reusing the existing
  `web/lib/scene/atmosphere/transition.ts` tweens. Operates on the passed fog
  object only, never on `realism/`.
- `index.ts`, barrel.
- `WIRING-decor.md`, the integrator-facing contract and mount steps.

The module reads `makeSun`, `skyColor`, `fogColorForSky` from the realism public
surface, `projectToScene` and `SCENE_WIDTH` from `sceneIntent`, and the
`worldUnitsPerMeter` and `geoRadiusMeters` convention the journey scene already uses
so the ring lands at true scale.

## 4. The SalishScene rig-mount seam, phase B, serialized after INTENT before BATHY

`web/app/components/scene/SalishScene.tsx` is the convergence file. Per the program
convergence calendar it is edited by one waveset at a time in the order INTENT, then
SCENIC, then BATHY. WS-SCENIC owns the single phase-B edit to this file in its slot,
after INTENT has landed the Viewport Bridge and before BATHY mounts water and bathy.

The composition point is the `TwinScene` component, which already mounts
`<RealismRig />`, `<Water2Rig />`, and `<primitive object={tiles.group} />` and
holds the live `tiles` instance. The SCENIC edit adds, inside `TwinScene`, two small
inline rig wrappers that call the new pure modules.

- A terrain-stylist effect that calls `applyTerrainStyle(tiles, opts)` once `tiles`
  exists and disposes on unmount.
- A `<primitive>` for `makeSkyDome(...)` and a `<primitive>` for
  `makeHorizonRing(...)`, both driven by the same pinned `SCENE_TIME` sun the rig
  already uses, plus the optional `fogTuning` call against `scene.fog`.

Background ownership decision at this seam. Either keep
`applyRealism({ background: true })` and add the Sky dome as a far dome behind the
terrain, or set `applyRealism({ background: false })` so the Sky dome drives the
background. The integrator picks one at mount time. The dispatch recommends keeping
realism background false and letting the Sky dome own the background, because the
Sky dome already produces the horizon gradient and the two would otherwise fight.

Journey mount. The journey beats render in
`web/app/(sandbox)/journey/JourneyScene.tsx`, a sandbox file, not the convergence
file, but it composes the same realism and water2 rigs and must show the same
vegetated land and framed horizon for acceptance. WS-SCENIC owns the parallel mount
edit there in the same phase-B step. It is a separate file with the same single
owner, so there is no collision with the convergence calendar.

## 5. One-file-one-owner table

| File | New or edit | Owner | Phase | Seam, what it wires | Honesty label carried |
| --- | --- | --- | --- | --- | --- |
| `web/lib/scene/terrain/terrainStylist.ts` | new | Terrain Stylist | A | registers a `load-model`/`dispose-model` listener and `forEachLoadedModel` on the passed `TilesRenderer`, injects an elevation-and-slope biome tint into each tile material | derived tint, real CUDEM geometry, color interpretive |
| `web/lib/scene/terrain/index.ts` | new | Terrain Stylist | A | barrel | n/a |
| `web/lib/scene/terrain/WIRING-terrain.md` | new | Terrain Stylist | A | integrator contract and mount steps | states the tint is derived, not surveyed |
| `web/lib/scene/terrain/landcover.ts` | new, optional | Terrain Stylist | A | loads and projects an ESA WorldCover crop, feeds the tint | land cover from ESA WorldCover 2021, CC BY 4.0, color decorative |
| `web/lib/scene/decor/sky.ts` | new | Scenic Decorator | A | wraps `three/addons/objects/Sky.js`, driven by `makeSun().direction` | atmosphere effect, not a measured sky |
| `web/lib/scene/decor/horizonRing.ts` | new | Scenic Decorator | A | builds a true-scale decorative DEM ring from AWS Terrain Tiles, shares `scene.fog` | distant terrain decorative, not surveyed, sources tagged in `userData` |
| `web/lib/scene/decor/fogTuning.ts` | new, optional | Scenic Decorator | A | retunes the passed `scene.fog`, reuses the transition tweens | atmosphere effect |
| `web/lib/scene/decor/index.ts` | new | Scenic Decorator | A | barrel | n/a |
| `web/lib/scene/decor/WIRING-decor.md` | new | Scenic Decorator | A | integrator contract and mount steps | states ring is decorative, fog is atmosphere |
| `web/app/components/scene/SalishScene.tsx` | edit | SCENIC phase-B mount editor | B | mounts the terrain-stylist effect, the Sky dome, the horizon ring, and the optional fog tuning inside `TwinScene`; sets the background ownership | renders the labels above through scene-graph `userData` |
| `web/app/(sandbox)/journey/JourneyScene.tsx` | edit | SCENIC phase-B mount editor | B | parallel mount of the same three rigs for the journey beats | same labels |

Convergence-file rule check. The only convergence file touched is
`SalishScene.tsx`, by a single SCENIC phase-B editor, in the SCENIC slot of the
calendar. No producer in phase A touches `SalishScene.tsx`, `realism/` internals,
`tiles/` internals, `water2/`, or `substrate/`. No `git add -A`, no commit, no
deploy.

## 6. Open seams to confirm at the gate

- Landcover drape, build the optional `landcover.ts` with ESA WorldCover, or ship
  the derived biome tint alone. Adds a hosted cropped raster and an attribution
  surface if approved.
- Horizon source, true-scale DEM ring from AWS Terrain Tiles, the recommended
  primary, versus the lighter billboard-silhouette fallback for low-end devices.
- Background ownership at the SalishScene seam, Sky dome owns background with
  realism `background: false`, the recommended default, versus keeping the realism
  flat background and placing the Sky dome behind it.
- Sky model, the core three Preetham `Sky` object with no new dependency, the
  recommended default, versus `@takram/three-atmosphere` precomputed scattering,
  which needs a new dependency and a post-processing pipeline and is deferred.

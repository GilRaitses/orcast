# Wave 2 dispatch: integrate the real twin into the live scene

Home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`
Wave: W2 integrate-into-live-scene. Depends on W1 (closed). Charter: `WAVESET_CHARTER.md`,
machine shape: `wave_shape.yml`.
Gate: full-extent (pilot acceptable for first integration) tiles render in the live scene
with agent A realism at interactive frame rate, picking works, legacy placeholder removed
behind a fallback toggle. Visual verification at the gate (dev server now allowed for the
gate, never during the parallel producer phase).

## Discipline (unchanged from W1)

- One file one owner. Disjoint ownership below.
- Single convergence-file editor: the integrator, and only the integrator, edits
  `web/app/components/scene/SalishScene.tsx` and `web/lib/sceneIntent.ts`.
- Single manifest editor: only `picking-perf` edits `web/package.json`.
- Validate with `npm run typecheck` during the parallel phase. No `next dev`, no `next build`
  until the gate.
- Large artifacts to S3, never git. Honesty label "modeled, not measured" on derived data.
- No commit, no push without an explicit operator ask.

## Orchestrator-set reconciliation decisions (so agents agree)

1. Frame: KEEP the synthetic frame in `web/lib/sceneIntent.ts` (`SCENE_WIDTH = 120`). The
   integrator scales `tiles.group` to fit `SCENE_WIDTH` and applies `rotation.x = -Math.PI/2`.
   Sea level (elevation 0 m) maps to scene Y 0, so the water plane at Y 0 stays correct. A full
   migration to metric coordinates is deferred to W5 (precision-origin-shift). Do NOT migrate to
   meters in W2.
2. Scale and extent come from the tileset's RUNTIME bounding sphere
   (`tiles.getBoundingSphere`), exactly as the W1 standalone harness did. Do NOT trust
   `infra/3dtwin/pilot/pilot.bounds.json`: it is STALE (it still describes agent D's old GMRT
   pilot, 37 km and −377…+717 m). The served CUDEM pilot is ~11.3 km, −264…+273 m, local UTM
   origin 485245.194 E / 5377443.419 N. Derive everything at runtime.
3. Pilot URL for first integration:
   `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json`. The full-extent URL from
   `batch-conversion` lands under `/3dtwin/full/tileset.json`; the integrator swaps the single
   URL constant when it is ready.
4. Meshopt is required: register `MeshoptDecoder` via `GLTFExtensionsPlugin`, same as
   `useTilesRenderer.ts`.
5. Vertical exaggeration: uniform scale gives true-scale relief (about 5 percent over the
   pilot). The integrator may expose an optional vertical exaggeration factor on the tiles group
   Y for legibility, default 1.0, and record what it chose. Do not bake exaggeration into the
   tileset.

## Sequencing

Phase A (parallel, no convergence edits): `tiles-layer`, `science-substrate`, `picking-perf`,
`legacy-retirement`, `batch-conversion`. Launched as background subagents.
Phase B (after the four web producers land): `integrator`, solo, composes them and edits the
convergence files. `batch-conversion` runs async and need not block Phase B.

---

## Agents

### tiles-layer  (owns `web/lib/scene/tiles/`)
Productionize the sandbox `useTilesRenderer.ts` into a reusable library hook
`web/lib/scene/tiles/useTilesLayer.ts` plus `index.ts`. Same lifecycle: construct on url,
register `ImplicitTilingPlugin` and `GLTFExtensionsPlugin({ meshoptDecoder: MeshoptDecoder })`,
per-frame `setResolutionFromRenderer` + `update`, `needs-update` invalidate, shadows on
`load-model`, dispose on unmount. Add options: `errorTarget`, `maxDepth`, `enabled`,
`enableShadows`, `groupRotationX` (default `-Math.PI/2`), `fitScaleToWidth` (number or null) so
the caller can request the group be uniformly scaled so its bounding sphere diameter equals a
target width in scene units, plus `onFit(sphere)` callback. Expose the `TilesRenderer` instance
so the caller can wire picking. No new dependency (`3d-tiles-renderer` already present). Validate
with `npm run typecheck`. Do not edit `SalishScene.tsx` or `package.json`. Write a short
`WIRING-tiles-layer.md` in the same dir.

### science-substrate  (owns `web/lib/scene/substrate/`)
Turn agent F's modeled CUDEM depth field into a live, sampleable substrate. Read the sample at
`infra/3dtwin/science/sample_san_juan_bathymetry_cudem.json` (schema: source, dataset, bounds,
resolution_deg, points[{lat,lng,depth_m}], depth negative below sea level). Decide whether to
copy it under `web/public/geo/` for runtime fetch or import it; document the choice. Export
`loadSubstrate(): Promise<SubstrateField>`, `sampleSubstrate(field, lat, lng): number` (nearest,
mirrors `BathymetryAdapter.depth_at`), and an optional `buildSubstrateOverlay(field, opts):
THREE.Object3D` data layer (depth-tinted points or a low-res grid) the integrator can toggle.
Label everything modeled, not measured. No manifest edit, no convergence edit. Validate with
`npm run typecheck`. Write `WIRING-substrate.md`.

### picking-perf  (owns `web/lib/scene/picking/`, sole manifest editor)
Accelerated raycasting and a perf harness. Add `three-mesh-bvh` (latest compatible with
`three@0.169`) to `web/package.json` (you are the ONLY manifest editor this wave). Export
`accelerateTilesPicking(tiles)` that computes a BVH bounds tree on each tile mesh on
`load-model` and installs the BVH raycast, and `worldPointToLatLng(point, bounds, depth, group
inverse transform)` that inverts the integrator frame to lat/lng using the same math as
`unprojectFromScene`. Also provide a `<PerfHud />` overlay (frame time, draw calls, geometry
count) for the gate. No convergence edit. Validate with `npm run typecheck`. Write
`WIRING-picking.md`.

### legacy-retirement  (owns `web/app/components/scene/RETIREMENT.md`, no convergence edit)
Write the exact removal plan for the placeholder path in `SalishScene.tsx`: the
`salish_heightmap.json` fetch and `Heightmap` state, the `TerrainMesh` placeholder geometry, the
`WaterPlane` (superseded by realism water), and the `depthColor`/`WATER_*`/`LAND_*` constants
that move to `realism/palette.ts`. Specify a fallback toggle: keep the existing `assetError`
to-Maps fallback, and add a flag so that if the tileset fails to load the scene can still show a
minimal placeholder or the Maps fallback rather than an empty canvas. Quote the precise current
line ranges to remove and what replaces them. Do NOT edit `SalishScene.tsx`. This is a plan the
integrator applies.

### batch-conversion  (owns `infra/3dtwin/host/`, runs on aimez-services EC2, async)
Bake the FULL `SAN_JUAN_BOUNDS` extent (all CUDEM `wash_bellingham` tiles via agent B's
reprojected EPSG:32610 NAVD88 surface, `infra/3dtwin/reproject/`) to OGC 3D Tiles 1.1 with a
real LoD hierarchy (tile and decimate; the full extent is far larger than the single-tile pilot),
gltfpack meshopt, validate with the CesiumGS `3d-tiles-validator` (0 errors), upload to
`s3://aimez-data/3dtwin/full/`, and confirm CloudFront serves `/3dtwin/full/tileset.json` with
CORS. Reuse D's `make_tileset.py` z-up box mapping, NOT C's `10_mesh_to_3dtiles.py` (its tileset
box has swapped axes and fails validation). Report the live URL, validator output, tile count,
and total bytes. Heavy and long-running. No web edits, no commit.

### integrator  (owns `web/app/components/scene/SalishScene.tsx` AND `web/lib/sceneIntent.ts`) — Phase B
> FRAME UPDATE (S15, supersedes the pilot wording below): mount the FULL-EXTENT multi-LoD tileset
> `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json`, NOT the single-tile pilot. It is
> live, validated (85 tiles, 4 LoD levels, 0 errors), and orchestrator-verified to refine on zoom
> (models 1->9). Derive scale/extent/bounds from the runtime bounding sphere; the pilot AND the
> stale `pilot.bounds.json` are dead for integration. Keep `errorTarget`/`maxDepth` from
> `useTilesLayer` so LoD streams. The placeholder vanishing-land winding bug is already fixed in
> `SalishScene.tsx` (S14) — when you remove the placeholder `TerrainMesh`/`WaterPlane`, that fix
> retires with it. Water reframed to depth-driven (charter A3) lands in W3/W4, not here.

Compose the live scene from finished parts:
- Mount tiles with `useTilesLayer` (FULL-extent URL above, `groupRotationX = -PI/2`,
  `fitScaleToWidth = SCENE_WIDTH`, meshopt). Use the `onFit` bounding sphere to set camera framing
  and OrbitControls min and max distance.
- Mount realism per `WIRING-realism.md` (Option 1 RealismLayer or Option 2 RealismRig). Remove
  the hard-coded lights and `WaterPlane`. Water plane sits at Y 0.
- Apply `legacy-retirement` removal. Keep the Maps and placeholder fallback toggle.
- Wire picking with the `picking` module: raycast `tiles.group`, convert the world hit to lat
  and lng, emit the existing `SceneIntent` cell event. Use `science-substrate` `sampleSubstrate`
  for `depth_m` on the pick.
- Reposition hydrophone beacons and the focus marker into the tile frame by raycasting the
  tiles for surface Y at each lat and lng, or by sampling the substrate, instead of the old
  `sampleDepth` against the retired heightmap.
- Keep the geographic bounds used for project and unproject consistent with the served pilot.
  Since the pilot covers a sub-extent of `SAN_JUAN_BOUNDS`, document which bounds you use and
  why, and prefer deriving them from the tileset rather than the stale `pilot.bounds.json`.
Validate with `npm run typecheck`, then run the dev server on port 3005 (the local WorkOS dev
bypass in `web/.env.local` is in place) and visually verify: tiles render with realism, the
water animates at Y 0, a click picks a lat and lng with a depth, beacons sit on the surface.
Capture a screenshot for the gate. No commit.

## Validation matrix

| Agent | Validates with | Edits convergence file | Edits manifest |
|---|---|---|---|
| tiles-layer | typecheck | no | no |
| science-substrate | typecheck | no | no |
| picking-perf | typecheck | no | yes (sole) |
| legacy-retirement | n/a (doc) | no | no |
| batch-conversion | 3d-tiles-validator on EC2 | no | no |
| integrator | typecheck + dev-server visual | yes (sole) | no |

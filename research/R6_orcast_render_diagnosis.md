# R6 grounded diagnosis of why orcast land renders inconsistently and vanishes

Author: research agent R6
Scope: a code-grounded diagnosis of the "water always present, land renders inconsistently and vanishes" report, traced against the ACTUAL files in this repo and the served pilot tileset, cross-referenced to R1 (terrain rendering) and R4 (ocean water). Read-only. No code edits. No commit.
Date: 2026-06-27.

Stack under study: Next.js, react-three-fiber, three@0.169, `3d-tiles-renderer@0.4.28`. Pilot is OGC 3D Tiles 1.1 baked from NOAA NCEI CUDEM 1/9 arc-second topobathy, NAVD88 m, EPSG:32610, single root tile with no LoD.

---

## 0. The single most important fact, which reframes the whole report

The scene the operator is looking at is `web/app/components/scene/SalishScene.tsx`. That file does **not** use `3d-tiles-renderer`, the pilot tileset, the sandbox, or the Gerstner water in `realism/water.ts`. It renders two hand-built meshes:

- a `TerrainMesh` built from `/geo/salish_heightmap.json` (`SalishScene.tsx:40-93`),
- a plain `WaterPlane` (`SalishScene.tsx:95-108`).

The 3D Tiles path (`useTilesRenderer.ts`, `TilesSandboxScene.tsx`, `pilot.glb`) lives only in the `(sandbox)/tiles3d` route, which the de-risk note in `TilesSandboxScene.tsx:1-8` says is type-checked only and not visually run during the wave. So the symptom the operator filed is produced by the placeholder heightfield mesh plus the placeholder water plane, not by the tileset. The tileset hypotheses still matter for the Wave 2 integrator and are analyzed in section 2, but they are not what is vanishing today.

This matters because R1 and R4 both reasoned primarily about the tileset and the Gerstner water, neither of which is on screen yet. The live defect is simpler and is provable from the placeholder code.

---

## 1. Ranked hypotheses for the live scene (`SalishScene.tsx`)

### H1 (root cause). Inverted triangle winding makes the terrain back-facing from above, so default `FrontSide` culling hides it, while the water plane faces up and always shows

Evidence, from the actual mesh build:

- Vertex positions: `x` increases with column `c`, `z = -((r/(rows-1)) - 0.5) * depth` so `z` decreases as row `r` increases, `y = d * HEIGHT_SCALE` (`SalishScene.tsx:55-58`).
- Index winding: `indices.push(a, d, b, b, d, e)` where `a=(r,c)`, `b=(r,c+1)`, `d=(r+1,c)`, `e=(r+1,c+1)` (`SalishScene.tsx:63-71`, the push is line 70).

Compute the front-face normal of the first triangle `(a, d, b)` by the right-hand rule, `cross(d-a, b-a)`. With `d-a ≈ (0, *, -Δz)` (Δz greater than 0) and `b-a ≈ (Δx, *, 0)` (Δx greater than 0), the cross product is dominated by its Y term `-Δz*Δx`, which is negative. The geometric front face therefore points in **-Y, downward**. In three.js the front face is the one whose winding is counterclockwise toward the viewer, so a face whose normal points down is front-facing only when seen from below.

The material is `meshStandardMaterial` with no `side` prop (`SalishScene.tsx:89-91`), so it defaults to `THREE.FrontSide` with backface culling on. The camera sits above the surface at `[0, 70, 95]` looking at the origin, and `OrbitControls` is clamped to `maxPolarAngle={Math.PI / 2.05}` (`SalishScene.tsx:213, 253`), so the view is always from above the horizon. From above, the terrain's top is the **back** face and is culled. The terrain is therefore mostly invisible, and only steep slopes that happen to turn their downward face toward a near-grazing camera flicker in, which is exactly the "renders inconsistently and vanishes" character.

The asymmetry in the report is explained by the same mechanism. The `WaterPlane` is a `PlaneGeometry` rotated `rotation={[-Math.PI/2, 0, 0]}` (`SalishScene.tsx:97`). A `PlaneGeometry` front-faces +Z, and the -90 degree rotation about X turns +Z into +Y, so the water plane front-faces **up** and is visible from above on every frame. Water faces up and always shows. Land faces down and is culled. That is the literal "water always present, land vanishes" observation.

Corroborating defect, same code path. `geo.computeVertexNormals()` (`SalishScene.tsx:77`) derives normals from the same winding, so the vertex normals also point downward. The directional light is above the scene at `[60, 90, 40]` (`SalishScene.tsx:218`). Any terrain face that does render is lit from behind and reads dark, which matches the operator's separate "the look is wrong" note. Note that `dem_to_glb.py:102-105` explicitly flips winding and normals when the average normal points down, but the in-browser `TerrainMesh` has no such flip, so the placeholder regressed where the bake did not.

- Concrete test: set the material to `side={THREE.DoubleSide}` on `SalishScene.tsx:90` and reload. If the land becomes solid and stable from every orbit angle, winding/culling is confirmed as the cause.
- Concrete fix: reverse the index winding to `indices.push(a, b, d, b, e, d)` (`SalishScene.tsx:70`) and keep `computeVertexNormals()`, which will then yield upward normals and correct lighting. `DoubleSide` is an acceptable fast mitigation but leaves normals inverted, so prefer fixing the winding.

### H2 (strong contributor to the flicker character). Coplanar z-fighting between the terrain shoreline and the translucent water plane at Y=0

Evidence:

- The water plane is fixed at `position={[0, 0, 0]}` (`SalishScene.tsx:97`), so its surface is exactly scene Y=0.
- Terrain Y is `d * HEIGHT_SCALE` with `HEIGHT_SCALE = 0.04` (`sceneIntent.ts:65`). Every shoreline vertex where `d` crosses 0 sits at Y near 0, coincident with the water plane.
- The water material is `transparent` with `opacity={0.45}` and no `depthWrite` override (`SalishScene.tsx:99-105`), so `depthWrite` is the three.js default `true`. A transparent depth-writing plane coincident with terrain produces depth ties at the coastline, and three resolves transparent draw order by object-center distance, which flips as the camera moves.

The result is shoreline pixels that are sometimes water-over-land and sometimes land-over-water, so the coast flickers in and out independently of H1. This is the mechanism R4 section 3 describes, observed here on the placeholder plane rather than on the Gerstner shader R4 inspected.

- Concrete test: set the water plane to `position={[0, -0.5, 0]}` and `opacity={0.2}` temporarily. If the shoreline flicker stops, depth tie at Y=0 is confirmed.
- Concrete fix: give the water material `depthWrite={false}` and an explicit `renderOrder`, keep terrain opaque and drawn first, and bias the water plane slightly below Y=0 or add a small `polygonOffset`. The durable fix is R4's depth-driven alpha so shallow and dry areas go transparent instead of being painted over.

### H3 (amplifier, not a primary cause). Vertical compression by `HEIGHT_SCALE = 0.04` leaves low land barely above the water plane

Evidence: `HEIGHT_SCALE = 0.04` (`sceneIntent.ts:65`) maps meters to scene units, so 20 m of coastal land rises only 0.8 scene units above the Y=0 water, under a 0.45-opacity tint. Combined with H1 culling and H2 z-fighting, low terrain is both easy to cull and easy to wash out, so it disappears first. This is why the vanishing is reported as worst near the coast. It is an amplifier of H1 and H2, not an independent cause.

- Concrete test: raise `HEIGHT_SCALE` to 0.2 and observe whether more land stays visible.
- Concrete fix: keep true scale per the WIRING note but lower the water opacity or move to depth-driven alpha so low land is not washed out.

### H4 (not currently active, but a Phase-B trap). The realism water in `realism/water.ts` is single-sided and forced last

Evidence: `makeWater` sets `side: THREE.FrontSide`, `depthWrite: false`, `renderOrder: 1` (`water.ts:168-191`). `FrontSide` is fine for a plane the camera stays above, and `depthWrite:false` is correct transparency practice, but `renderOrder: 1` forces the water after default-order geometry. If the Phase-B integrator wires this in while terrain culling (H1) is unfixed, the same "water over everything" picture persists, now with a prettier surface. This is latent, not live, because Phase-B is on hold per the charter.

- Concrete test: when Phase-B wires it, verify with terrain made `DoubleSide` first so the two issues are not confused.
- Concrete fix: fix H1 and H2 before wiring `realism/water.ts`, and adopt R4's depth-driven alpha so `renderOrder` stops mattering.

---

## 2. The pilot tileset path and the Wave 2 integrator (`useTilesRenderer.ts`, `TilesSandboxScene.tsx`, served `tileset.json`)

These are not on screen today, but they will reproduce a different "vanish" the moment the integrator mounts the pilot, so they are diagnosed here with the fetched values.

Fetched from `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json`:

```json
{
  "asset": { "version": "1.1", "generator": "orcast make_tileset.py" },
  "geometricError": 25422.624,
  "root": {
    "boundingVolume": { "box": [0.0, 0.0, 170.0729, 18890.4, 0.0, 0.0, 0.0, 17013.6, 0.0, 0.0, 0.0, 558.3579] },
    "geometricError": 0.0,
    "refine": "REPLACE",
    "content": { "uri": "pilot.glb" }
  }
}
```

So the box is centered at (0, 0, 170.07) in the z-up tile frame with half extents 18890.4 m east, 17013.6 m north, 558.36 m vertical. That is a single tile roughly 37.8 km by 34.0 km, with a bounding sphere radius of about 25,420 m. These values come straight from `make_tileset.py:31-58`, where the root `geometricError` is hard-set to `0.0` (line 57) and the top-level `geometricError` is the horizontal diagonal (line 53).

### T1 (the structural cause R1 names). errorTarget cannot gate a single root tile, so display is frustum-only

The maintained renderer decides root display purely on frustum intersection, not on screen-space error. From NASA-AMMOS issue 1209: "the error target only applies to subdivisions of a root tile, not whether the root tile itself is displayed or not, that is only decided based on whether the tile volume is in the frustum or not." Source: https://github.com/NASA-AMMOS/3DTilesRendererJS/issues/1209 .

Consequences for the pilot:

- `errorTarget` (default 12 in `useTilesRenderer.ts:38`, overridden to 8 in `TilesSandboxScene.tsx:44`) and `maxDepth` (`useTilesRenderer.ts:39`) have **no effect** on whether the lone tile shows, because there are no children to refine into. The root `geometricError = 0.0` is therefore harmless for display, contrary to the natural suspicion, since a zero-error single tile simply never tries to refine and shows whenever it is in the frustum.
- Visibility becomes one binary frustum test on a 25 km sphere. The whole surface pops in and out as a unit when the camera moves, which is R1 failure mode 1.

- Concrete test: load the pilot in the sandbox with `DebugTilesPlugin` and watch the single bounds volume toggle in and out as the camera orbits and zooms.
- Concrete fix: the durable answer is R1 section 4, bake a multi-LoD implicit quadtree so culling is per sub-tile. The same-day workaround if it must ship as one tile is to keep it in the frustum at all times and bracket near/far around its bounds.

### T2 (the live trap if mounted as-is). A 25 km bounding sphere does not fit `SalishScene.tsx` near 0.1 / far 2000

Evidence:

- The live camera is `near: 0.1, far: 2000` (`SalishScene.tsx:213`) and `OrbitControls` is clamped `minDistance={20} maxDistance={400}` (`SalishScene.tsx:254-255`). The pilot's bounding sphere radius is about 25,420 m. Mounted unscaled, the geometry is entirely beyond the far plane and is frustum-culled, so it vanishes completely.
- `WIRING-pilot.md:71-77` already says the integrator must scale by about `120 / 37000` (about 0.00324) or migrate the scene to meters. At that scale the sphere radius becomes about 82 scene units, which fits inside far 2000.

- Concrete test: mount the pilot in `SalishScene` unscaled and confirm nothing renders, then apply the scale and confirm it appears.
- Concrete fix: apply the WIRING scale and set the live camera near/far to bracket the scaled bbox, or migrate the scene to meters and set far around 60,000.

### T3 (orientation, a "looks wrong" not a "vanish"). The sandbox never applies the documented rotation

Evidence: `WIRING-pilot.md:42-55` says the tiles need `tiles.group.rotation.x = -Math.PI/2` to map the tile z-up frame into the three.js y-up scene, but `TilesSandboxScene.tsx:78-86` mounts `tiles.group` with no rotation. The camera-fit on `load-tileset` (`TilesSandboxScene.tsx:49-70`) reframes from the bounding sphere, so the geometry is still in view, just stood up at the wrong orientation. This produces a wrong-looking surface, not a vanishing one.

- Concrete test: load the sandbox and check whether elevation points along scene +Y. It will not until the rotation is applied.
- Concrete fix: add `tiles.group.rotation.x = -Math.PI / 2` before mounting, then confirm visually per the WIRING note.

### T4 (lower-rank tileset risks carried from R1, listed for completeness)

- Float32 precision is not a live risk for the pilot, because `dem_to_glb.py:73-79` already recenters on the UTM centroid, so vertices are small offsets, not raw eastings. R1 failure mode 5 is therefore mitigated for the pilot as baked.
- `EXT_meshopt_compression` must have the decoder registered or the glb fails to load and only water would show. The hook registers it via `GLTFExtensionsPlugin({ meshoptDecoder: MeshoptDecoder })` (`useTilesRenderer.ts:60-62`), and `validation_report.json` confirms the glb uses that extension, so this is wired correctly, but it is the first thing to check in the console if the pilot shows nothing.
- LRU eviction (R1 mode 4) is unlikely for one tile, but worth confirming if the single glb is very large.
- `frameloop="demand"` is not in use, both Canvases use the default always loop, so the `invalidate` safety net in `useTilesRenderer.ts:79-80` is currently a no-op. It becomes load-bearing only if a future host switches to demand.

---

## 3. Prioritized fix list

1. Fix the live terrain so it faces the camera. Reverse the index winding at `SalishScene.tsx:70` to `indices.push(a, b, d, b, e, d)` and keep `computeVertexNormals()`. This makes land render from above the way the water plane already does and corrects the inverted lighting. This is the single change that addresses the actual report. Fast mitigation while validating: `side={THREE.DoubleSide}` at `SalishScene.tsx:90`.
2. Stop the shoreline flicker. Set the live `WaterPlane` material to `depthWrite={false}` with an explicit `renderOrder`, keep terrain opaque and drawn first, and bias the plane just below Y=0 or add `polygonOffset` (`SalishScene.tsx:95-108`). The durable version is R4's depth-driven water alpha so shallow and dry areas go transparent rather than being painted over.
3. Before the Wave 2 integrator mounts the pilot, fix the tileset for a single-tile frustum-only world. Apply `tiles.group.rotation.x = -Math.PI / 2`, scale by about `120/37000`, and set camera near/far to bracket the scaled bbox, because `SalishScene.tsx:213` far 2000 will otherwise clip the 25 km tile out entirely. Commit to R1 section 4, a real multi-LoD quadtree, as the production answer so culling is per sub-tile instead of one binary pop.

Lower priority and conditional: do not wire `realism/water.ts` until fixes 1 and 2 land; verify the meshopt decoder loads the glb in the console; raise `HEIGHT_SCALE` only if true-scale terrain reads too flat after fix 1.

---

## Implications for orcast

The filed bug is not the tileset and not the Gerstner shader. It is the placeholder `TerrainMesh` in `SalishScene.tsx`, whose triangles are wound so the surface front-faces downward and is backface-culled from the only camera angles the controls allow, while the water plane front-faces upward and always renders. That asymmetry is the "water present, land absent" report, line for line. Reversing the winding at `SalishScene.tsx:70` is the highest-value change and is cheap.

This refines R1 and R4 rather than contradicting them. R1 correctly diagnoses the tileset as structurally unfit for streaming, and R1 failure mode 8 anticipated inverted winding from a DEM export. The grounded finding is that the inverted winding is in the live placeholder mesh, not in the bake, which already flips it in `dem_to_glb.py:102-105`. R4 correctly diagnoses transparent-plane sorting, and the grounded finding is that it is already biting at the placeholder water plane at Y=0, before the Gerstner surface is even wired.

For the synthesis and the W2 frame decision: fix the live placeholder first so the operator sees stable land and water today, then carry R1's multi-LoD quadtree and R4's depth-driven water alpha into Phase-B, and require the integrator to apply the WIRING rotation and scale and to widen the camera far plane before mounting the pilot, because the current far 2000 guarantees the unscaled 37 km tile vanishes.

# RP1 — Load Performance (findings)

Lane: 3D-TWIN. Wave: W-PERFUX. Role: RP1 (read-only research). Reports to O0.
Date: 2026-06-28. repo_state_verified_against: `origin/main` @ `b9e2e13`.
Method: read-only. Sizes measured with `curl -s` for `tileset.json` and `curl -sI`
for each tile glb against the served CloudFront origin. No code edited, no dev
server, no browser automation.

## 1. What loads, measured

Served tileset root, taken from `FULL_TILESET_URL` in
`web/app/components/scene/SalishScene.tsx:84`:
`https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json`

`tileset.json` itself is 52,322 bytes. It declares an explicit quadtree, REPLACE
refinement, 4 levels, root `geometricError` 160, level errors 80 / 40 / 20 with a
10 m leaf ground sample distance. The 85 content URIs were parsed from the served
JSON and each glb was measured with `curl -sI`.

### Tile count and byte breakdown (measured over the wire, 85 of 85 tiles)

| Level | Tiles | Bytes | MiB | Share of bytes | Avg per tile |
|-------|-------|-------|-----|----------------|--------------|
| L0 root | 1 | 989,724 | 0.94 | 1.2% | 966.5 KiB |
| L1 | 4 | 3,900,052 | 3.72 | 4.9% | 952.2 KiB |
| L2 | 16 | 15,249,364 | 14.54 | 19.2% | 930.7 KiB |
| L3 leaves | 64 | 59,293,804 | 56.55 | 74.7% | 904.8 KiB |
| **Total** | **85** | **79,432,944** | **75.75** | **100%** | **~912 KiB** |

Largest single tile measured `tiles/L3_6_0.glb` at 1.04 MiB. Smallest leaf
`tiles/L3_7_6.glb` at 826,244 bytes. This matches the bake design in
`infra/3dtwin/host/README.md`: each tile carries a near constant vertex budget
because `bake_tree.py` decimates by stride 2^(LMAX−L) per level, so per-tile size
is roughly flat at ~900 KiB and total cost tracks tile **count**, not per-tile
weight. Repo-stated totals: 16,343,109 vertices and 32,537,090 triangles across
the tree.

### Tiles are geometry only, no textures

I downloaded `tiles/L3_6_0.glb` and parsed the glb JSON chunk. Result:
`extensionsUsed = [KHR_mesh_quantization, EXT_meshopt_compression]`, images 0,
textures 0, materials none, one mesh, one primitive with attributes POSITION and
NORMAL only, 192,654 positions in that leaf. There are no UVs, no vertex colors,
no embedded images anywhere in the tile payload. The terrain colour is painted at
runtime by `TerrainStylistRig` in `SalishScene.tsx`, not baked into the tiles.

### Other startup fetches, measured

| Asset | Source | Bytes | MiB |
|-------|--------|-------|-----|
| `/geo/sample_san_juan_bathymetry_cudem.json` (substrate field) | Next static | 288,198 | 0.27 |
| `/geo/horizon-ring.json` (decorative ring) | Next static | 72,683 | 0.07 |
| `/geo/salish_heightmap.json` | Next static | 2,655 | 0.00 |

These three are loaded at mount by `loadSubstrate` and `loadHorizonField` and sum
to about 0.34 MiB. They are negligible against the tile payload and are not a
bandwidth driver. They do, however, fire concurrently with the tile stream.

## 2. Dominant cost and why the twin loads slowly

The dominant cost is **leaf-level terrain geometry volume**. The 64 L3 leaves are
56.55 MiB, which is 74.7% of the 75.75 MiB total and 64 of 85 tiles. The reason
the renderer pulls them at startup is the **default framing**, not a tileset
defect.

Mechanism, grounded in the code:

1. `SalishScene.tsx:771` mounts `useTilesLayer` with `errorTarget: 16`. The
   per-frame `tiles.update()` refines any tile whose projected screen-space error
   exceeds 16 px. Leaf geometric error is 10 m.
2. The resting camera frames the **entire** extent. `RESTING_ORBIT_ALT_M = 2200`
   and the orbit radius is `max(fitRadius*0.9, 40)` around `SCENE_CENTER`
   (`SalishScene.tsx:547`), which is the midpoint of the full
   `TILESET_BOUNDS`. The full extent is about 36.9 km E-W by 33.3 km N-S
   (`WIRING-host.md`).
3. With the whole 36.9 km surface inside the frustum at a low error target, the
   scheduler drives refinement toward leaves across essentially the entire
   extent, so it streams up to all 85 tiles. REPLACE refinement also means
   ancestors load first and are then replaced, so the worst case transfers the
   full ~75.75 MiB before the view settles.

Secondary costs that stack on top during that stream:

- **Water2 depth pre-pass every frame.** `Water2Rig.useFrame` calls
  `handle.renderDepthPrepass(gl, scene, camera)` ahead of the auto-render
  (`SalishScene.tsx:306-311`). That is a second full opaque render of the scene
  each frame, so while 32.5 M triangles are arriving the GPU pays roughly twice
  per frame. This hurts time-to-interactive and frame pacing, not bytes.
- **meshopt decode.** 16.3 M vertices of POSITION and NORMAL are meshopt encoded
  and must be decoded on load through `MeshoptDecoder`. Decode is real CPU work
  that scales with the number of leaves pulled.
- `enableShadows` is already false at the call site, so shadow casting is not a
  current cost. The `useTilesLayer` default is true, so any future caller must
  keep it false.

## 3. Ranked levers

Win estimates are first-paint transfer and triangle load at the resting wide
view, derived from the per-level table in section 1.

| # | Lever | Expected win | Config-only or re-bake | Risk |
|---|-------|--------------|------------------------|------|
| 1 | Raise `errorTarget` at the wide resting view, from 16 toward 32, ideally driven down again as the camera zooms in | Drops most L3 leaves until zoom. First paint falls from 75.75 MiB toward the L0+L1+L2 set of 19.2 MiB, about 75% fewer bytes and triangles. Leaf detail is invisible from 2200 m anyway. | Config-only. `errorTarget` is a prop applied live by a `useEffect` in `useTilesLayer.ts:144`, no rebuild. | Low. Coarser relief if the value stays high after zoom-in. Mitigate by lowering it on close framing. |
| 2 | Tighter default framing (RP2). Lower `RESTING_ORBIT_ALT_M` and frame the San Juans core so fewer tiles sit in the frustum | Frustum culling removes outer leaves. If the core view covers about a third of the extent the in-view leaf set drops from 64 toward ~20, roughly 55 to 60% fewer leaf bytes, and it compounds with lever 1. | Config-only. Camera constants in `SalishScene.tsx`. Owned by RP2. | Low to medium. Must still allow zoom-out to the full extent on demand. |
| 3 | Cap `maxDepth` at startup, for example 2, then raise it on zoom or on focus | Hard cap at the 21-tile L0+L1+L2 set, 19.2 MiB, about 75% fewer bytes and triangles until the cap lifts. | Config-only. `maxDepth` is a prop applied live by `useTilesLayer.ts:144`. | Medium. Global detail cap, so close inspection is blocked until the cap is raised. Best paired with a zoom or focus trigger. |
| 4 | Defer non-critical rigs and the Water2 depth pre-pass until tiles settle | Removes a full extra opaque render per frame during the stream and frees a little startup bandwidth from the substrate and horizon fetches. Improves time-to-interactive, not total bytes. | Code-only in `web/`, mount gating in `SalishScene.tsx`. No re-bake, no infra. | Low to medium. Water reads flat and the seabed tint is absent for the first moment. Must restore on settle. |
| 5 | Gate streaming on the `enabled` flag and on LGC focus, so the twin stops refining when it is not the focused surface | Pauses `tiles.update()` entirely when the map is not in focus, so no tiles stream while a panel or chat holds attention. | Config-only. The `enabled` flag already exists in `useTilesLayer.ts:28` and short-circuits the per-frame update. | Low. Needs a focus signal source. LGC supplies one (section 4). |
| 6 | KTX2 or Basis texture compression (the chartered W5) | No win for the tileset. The tiles carry zero textures, so there is nothing to compress. W5 can only help non-tile scene textures, if any exist. | N/A for tiles. Adding textures at all would need a re-bake and would add bytes, not remove them. | N/A. Listed only to retire the assumption that W5 speeds the terrain load. |
| 7 | Drop or harder-quantize NORMAL, reconstruct shading from derivatives | NORMAL is roughly half the per-vertex attribute payload, so removing it could cut on the order of 30 to 40% of geometry bytes across all levels. | Re-bake on the EC2 host. Changes `bake_tree.py` and `03_compress.sh`, then re-validate and re-upload. | Medium. Flat or derivative normals change the lit look of the relief. Needs a visual gate. |
| 8 | Bake a small San Juans core subset tileset for the default load, full extent on demand | A dedicated core tileset would carry only the leaves inside the core, so the first load is a fraction of 75.75 MiB. | Re-bake on the EC2 host. A config-only approximation already exists via levers 1 to 3 plus RP2 framing, which is why this ranks last. | Medium. Two tilesets to maintain, plus a swap path when the user zooms past the core. |
| 9 | Swap meshopt for Draco geometry compression | Marginal and uncertain. `gltfpack -cc` already gives 9.85x with meshopt and quantization. Draco may match or slightly beat it on this geometry, with no guarantee. | Re-bake on the EC2 host. | Medium for low expected payoff. Not worth a re-bake on its own. |

Config-only levers, no EC2 work: 1, 2, 3, 4, 5. Re-bake levers: 7, 8, 9. Lever 6
is not applicable to the tiles.

## 4. LGC focus-model leverage

The Liquid-Glass Console charter
(`.cca/catalogue/O0/20260628_liquid-glass-console/WAVESET_CHARTER.md`) locks a
single-focus center model with a self-hiding chat and dock, and locked decision 8
states that the map is the focus sink, with `{kind:"map"}` binding to the live
scene host. That focus signal is exactly the trigger levers 1, 4, and 5 need.

When a non-map surface holds focus, for example the user is reading a panel or the
chat is expanded, the scene is not the center of attention and can down-clock
without any visible loss:

- Set `useTilesLayer`'s `enabled` to false so `tiles.update()` stops and no tiles
  stream while the map is backgrounded. The flag is already wired to skip the
  per-frame update.
- Raise `errorTarget` while backgrounded, and lower it again when the map
  regains focus, so refinement effort follows attention.
- Skip the Water2 per-frame depth pre-pass while the map is not focused, removing
  the second full render per frame.

The self-hiding chat and dock also reduce HUD and DOM overlay cost when the map is
the focus, which is consistent with the operator instinct that the LGC work helps
the model load and run better. The leverage is real and config-aligned. It needs
only a focus state read from the LGC focus model, which LGC is already building as
a typed TS module per its locked decision 2.

## 5. Notes and limits

- All byte numbers are content-length over the wire from the served CloudFront
  origin and match the repo-stated 75.9 MiB on S3 within rounding.
- The per-tile flatness, about 900 KiB at every level, is by design and is why
  tile count is the right cost axis. Cutting the count of refined leaves is the
  highest-leverage move, and it is config-only.
- I did not run the app, so the in-view leaf counts in levers 2 and 3 are
  geometric estimates from the extent and the level table, not a measured frame.
  RP2's framing math should firm them up.

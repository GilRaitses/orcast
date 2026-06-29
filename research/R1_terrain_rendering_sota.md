# R1 — State of the art: rendering large-area terrain + bathymetry on the web

Author: research agent R1
Scope: how production web systems render large DEM/bathymetry terrain; LoD, tiling,
streaming, screen-space error; why single-tile terrain "vanishes"; how to author a correct
multi-LoD tileset from a DEM.
Date: 2026-06-27. Sources are current (2026) where the topic is version-sensitive.

This brief is read-only research. Stack under study: Next.js + react-three-fiber +
three@0.169 + `3d-tiles-renderer@0.4.28`, with a pilot OGC 3D Tiles 1.1 tileset baked from
NOAA NCEI CUDEM 1/9 arc-second topobathy (NAVD88 m, EPSG:32610), currently a **single root
tile with no LoD**, plus a Gerstner water plane at scene Y=0.

---

## 1. How production systems render large terrain + bathymetry

### 1.1 CesiumJS + Cesium World Terrain (quantized-mesh)
Cesium streams global terrain as **quantized-mesh-1.0**, a binary format describing "a simple
multi-resolution quadtree pyramid of meshes." A `layer.json` manifest declares the tiling
scheme (TMS / slippy), projection (`EPSG:4326` default, two root tiles; `EPSG:3857`, one
root tile), and tile URL templates. Each tile is an *irregular* triangle mesh whose edge
vertices are shared with neighbors so adjacent tiles match exactly.
Source: https://github.com/CesiumGS/quantized-mesh/

The key design point for terrain specifically: heightmap formats (Heightmap-1.0, raw WMS/WMTS
DEM) sample on a uniform grid, so as you approach the root of the pyramid the sample spacing
grows and **terrain features are lost between samples**. Quantized-mesh instead places more
vertices on peaks/cliffs and fewer on flats, preserving features at coarse LoD; it also
carries extensions for per-vertex normals (lighting) and water masks.
Source: https://groups.google.com/g/cesium-dev/c/8oC6OtbbBGI (Cesium dev list, STK/quantized-mesh)

### 1.2 OGC 3D Tiles (glTF) for terrain
As of 2026 CesiumJS ships **experimental** `Cesium3DTilesTerrainProvider`, which loads terrain
authored as **3D Tiles (glTF/GLB)** rather than quantized-mesh. The structural requirements are
strict and illuminating: it must conform to the same WGS84 double-headed quadtree as
quantized-mesh (two root tiles, region bounding volumes, **implicit tiling**); tiles carry
`TILE_MINIMUM_HEIGHT`, `TILE_MAXIMUM_HEIGHT`, `TILE_BOUNDING_SPHERE`,
`TILE_HORIZON_OCCLUSION_POINT` metadata; each GLB has a single node/mesh/primitive with
`POSITION` (and `NORMAL` if normals requested); and edges are matched via the `CESIUM_tile_edges`
extension. Compression via `EXT_meshopt_compression` / `KHR_mesh_quantization` is allowed.
Sources: https://github.com/CesiumGS/cesium/pull/12963 ,
https://cesium.com/learn/cesiumjs/ref-doc/Cesium3DTilesTerrainProvider.html

In 3D Tiles 1.1, the old `.b3dm/.i3dm/.pnts` containers are unified into glTF + extensions
(`EXT_structural_metadata`, `EXT_mesh_gpu_instancing`), so all content goes through one `Model`
path and custom shaders work uniformly.
Source: https://cesium.com/blog/2022/10/05/tour-of-the-new-gltf-architecture-in-cesiumjs/

### 1.3 NASA-AMMOS 3DTilesRendererJS (our renderer)
This is the three.js/r3f reference renderer for OGC 3D Tiles. It performs its **own** frustum
culling and screen-space-error traversal, drives tile loading by `errorTarget`/`maxDepth`, and
manages GPU memory through an `LRUCache`. Camera-aware helpers exist to keep the camera off the
surface (`adjustHeight`, minimum-distance offsets). When it owns culling it sets each tile
mesh's `frustumCulled = false` itself (`autoDisableRendererCulling`).
Source: https://github.com/NASA-AMMOS/3DTilesRendererJS/blob/master/src/three/renderer/API.md
Best-practice test matrix: https://github.com/NASA-AMMOS/3DTilesRendererJS/blob/master/TESTCASES.md

### 1.4 MapTiler / Mapbox-GL terrain (raster-DEM)
Mapbox-GL / MapLibre-GL and MapTiler render 2.5D terrain by sampling a **Terrain-RGB / Terrarium
raster-DEM** (elevation encoded in R,G,B) on a tiled mesh, decoded with a known scale/offset.
This is camera-relative 2.5D over a basemap, not a glTF mesh tileset; it is excellent for
draped imagery but is not a true 3D mesh hierarchy and is weaker for submerged bathymetry where
you want a single continuous topobathy surface.
Decoder example (Mapbox Terrain-RGB): `rScaler 6553.6, gScaler 25.6, bScaler 0.1, offset -10000`.

### 1.5 deck.gl `TerrainLayer` / `Tile3DLayer`
deck.gl has two relevant paths:
- **`TerrainLayer`** reconstructs a mesh from a height-map image (Mapzen/Terrarium/Mapbox-RGB).
  Critical detail for our failure mode: *"If `elevationData` is an absolute URL, a single mesh is
  used, and the `bounds` prop is required."* With a URL **template** (`{x}/{y}/{z}`) it instead
  builds a tiled `TileLayer` of meshes that refines on demand. So deck.gl's own docs distinguish
  the "single mesh" case (must hand it bounds) from the "tiled, refining" case.
  Source: https://deck.gl/docs/api-reference/geo-layers/terrain-layer
- **`Tile3DLayer`** consumes OGC 3D Tiles / Google Photorealistic 3D Tiles, with
  `operation: 'terrain+draw'` so other layers drape on the surface via `TerrainExtension`, and a
  `maximumScreenSpaceError` (~16–20) plus `memoryAdjustedScreenSpaceError` for memory pressure.
  Sources: https://deck.gl/docs/developer-guide/base-maps/using-with-3d-tiles ,
  https://github.com/visgl/deck.gl/blob/master/examples/website/google-3d-tiles/app.jsx

### 1.6 Google Photorealistic 3D Tiles
A globally-served OGC 3D Tiles 1.1 tileset (mesh + texture, implicit tiling) consumed by both
CesiumJS and deck.gl `Tile3DLayer`. It is the canonical proof that the 3D-Tiles-glTF path scales
to planet size when the hierarchy and geometric errors are authored correctly. Not a
bathymetry source, but the structural reference for "large area, many LoDs, streaming."

### 1.7 Tangram
Tangram (Mapzen) was an early WebGL terrain/vector renderer; it is now legacy/largely
unmaintained and not recommended for new large-DEM work. Mentioned for completeness; the live
ecosystem is Cesium, 3DTilesRendererJS, deck.gl, and MapLibre/Mapbox-GL.

### 1.8 quantized-mesh vs 3D Tiles (glTF) for terrain — direct comparison
| Aspect | quantized-mesh-1.0 | 3D Tiles 1.1 (glTF/GLB) |
|---|---|---|
| Purpose | Purpose-built terrain streaming | General 3D geospatial; terrain is a special case |
| Hierarchy | Fixed WGS84 quadtree pyramid via `layer.json` | Quadtree/octree, implicit or explicit, `tileset.json` |
| Mesh | Irregular, feature-adaptive, edge-shared | Arbitrary glTF mesh; edges matched via `CESIUM_tile_edges` |
| Materials | Limited (normals, water mask extensions) | Full glTF PBR + custom shaders + metadata |
| Renderers | CesiumJS (native), some others | CesiumJS, **3DTilesRendererJS (three.js)**, deck.gl |
| Compression | Built-in quantization | `KHR_mesh_quantization`, `EXT_meshopt_compression`, Draco |
| Fit for orcast | Not consumed by our three.js renderer | **Yes** — what we already chose |

Conclusion: for a three.js / `3d-tiles-renderer` app, **3D Tiles (glTF)** is the correct format
(quantized-mesh is essentially a Cesium-internal optimization). The orcast format choice is
right; the problem is the *structure* of the tileset, not the format.

---

## 2. LoD / screen-space error / geometric error — how a tileset MUST be built

The 3D Tiles standard structures tiles as a tree with **Hierarchical Level of Detail (HLOD)**.
Each tile carries a `geometricError`: "a nonnegative number that specifies the error, in meters,
of the tile's simplified representation of its source geometry." The root has the **largest**
geometric error; each child level is smaller; **leaf tiles are at or near 0**.
Source: https://docs.ogc.org/cs/22-025r4/22-025r4.html (3D Tiles 1.1) and
https://docs.ogc.org/cs/18-053r2/18-053r2.html (1.0).

At runtime the client projects `geometricError` (meters) to **Screen-Space Error (SSE)**
(pixels) using camera distance to the tile's bounding volume and the viewport resolution. If the
tile's SSE **exceeds** the maximum allowed (`maximumScreenSpaceError` in Cesium, `errorTarget`
in 3DTilesRendererJS), the tile is **refined** and its children are considered; otherwise the
tile is considered detailed enough and traversal **stops there**.
Source: https://cesium.com/learn/cesium-native/ref-doc/selection-algorithm-details.html

Implicit tiling (promoted to core in 3D Tiles 1.1) lets a single root declare a `QUADTREE`
subdivision plus `availableLevels`/`subtreeLevels`, and the client computes descendant bounding
volumes and geometric errors automatically: **each child's `geometricError` is half its
parent's**, overridable per tile via the `TILE_GEOMETRIC_ERROR` semantic. Tile content URIs are
templated as `content/{level}/{x}/{y}.glb`.
Sources: https://github.com/CesiumGS/3d-tiles/blob/main/specification/ImplicitTiling/README.adoc ,
https://github.com/CesiumGS/3d-tiles/tree/main/extensions/3DTILES_implicit_tiling

**Why a multi-level hierarchy is mandatory.** SSE-driven refinement only does anything if there
are children to refine into and the error decreases down the tree. A **single untiled tile** has:
- no children, so the renderer can never add detail;
- one bounding volume, so it is a binary in/out decision under frustum culling;
- one `geometricError` that, if wrong, breaks the SSE comparison entirely.

So the single-root pilot is outside the regime the standard and the renderers are built for.

---

## 3. Common failure modes: "terrain tiles vanish / render inconsistently"

These are documented, reproducible causes — several map directly onto a single-tile pilot.

1. **Frustum culling of one large tile (binary visibility).** With a single tile there is one
   bounding volume. If the camera is close, looking across/along the surface, or the bounds are
   slightly off, the whole tile is culled in or out at once — it "pops" and "vanishes" as the
   camera moves. A correct hierarchy culls per sub-tile, so most of the surface stays visible.
   3DTilesRendererJS owns culling and normally sets tile meshes `frustumCulled=false`
   (`autoDisableRendererCulling`); a misconfigured single mesh re-enabling three.js culling
   makes this worse.
   Source: https://github.com/NASA-AMMOS/3DTilesRendererJS/blob/master/src/three/renderer/API.md

2. **Wrong / zero `geometricError`.** If a content tile's error is `0` (the leaf convention) but
   it is actually the *only* tile, or if errors don't decrease down the tree, SSE math collapses.
   The renderer's traversal was corrected (≈v0.4.13) to **respect the error calculation and stop
   at tiles that meet the threshold** — including empty/internal tiles — which is spec-correct but
   leaves **holes** when the tileset is poorly structured. The maintainer's explicit workaround:
   on `load-tile-set`, set non-content/parent tiles' `geometricError` to a very large value
   (e.g. `1e100` / `Infinity`) so the error target is never met and traversal always refines into
   contentful children.
   Sources: https://github.com/NASA-AMMOS/3DTilesRendererJS/issues/1517 ,
   https://github.com/NASA-AMMOS/3DTilesRendererJS/issues/1304

3. **`errorTarget` / `maxDepth` misconfiguration.** In #1304 the external root and children all
   shared `geometricError = 0.9` while `errorTarget = 16`; the computed SSE (~10) fell *below*
   the target, so the renderer correctly stopped and everything "disappeared." Fix: give the
   empty/external root `Infinity` and ensure a monotonically decreasing GE ladder. `maxDepth` too
   low also truncates refinement.
   Source: https://github.com/NASA-AMMOS/3DTilesRendererJS/issues/1304

4. **Cache eviction / LRU too small.** In #1178, four tiles each used a ~5k×7k texture (~185 MB
   with mipmaps); the LRU cap (~430 MB) filled after ~3 tiles and rejected further loads, so the
   root could never refine and tiles never appeared. Fixes: raise `tiles.lruCache.maxBytesSize`
   (and set `minBytesSize=0`), reduce texture size (≤256² typical), or disable mipmaps via
   `TileCompressionPlugin`. A single tile with a huge baked DEM texture is exactly this trap.
   Source: https://github.com/NASA-AMMOS/3DTilesRendererJS/issues/1178

5. **Camera near/far clipping & depth precision at large coordinates.** A `near` plane too close
   to 0 collapses depth precision; a very large `far` with EPSG:32610 UTM coordinates (hundreds
   of thousands of meters) causes z-fighting and parts of the surface to drop out as you zoom.
   Remedies: push `near` out as far as tolerable, keep `far` tight, enable
   `logarithmicDepthBuffer` (note: it writes `gl_FragDepth`, disabling early-Z and hurting
   overdraw-heavy scenes), and/or shift the geometry to a **local origin (geometry rebase) +
   relative-to-eye** so GPU math stays in Float32-safe range. UTM eastings/northings uploaded raw
   into `Float32Array` already lose precision before any transform.
   Sources: https://stackoverflow.com/questions/37858464/ ,
   https://discourse.threejs.org/t/beware-of-logarithmic-depth-buffer-it-can-degrade-scene-performance/88495 ,
   https://github.com/mlightcad/large-coordinate-rendering

6. **NaN / degenerate bounds.** A bounding volume with NaN or zero extent makes culling and SSE
   undefined; the tile flickers in/out or never selects. Verify min/max heights and the bounding
   region/box/sphere are finite and non-degenerate (validate with `DebugTilesPlugin` bounds
   display). Source: https://github.com/NASA-AMMOS/3DTilesRendererJS/issues/1517 (bounds-display discussion).

7. **Transparent objects painting over opaque terrain / depth sorting.** A transparent or
   `depthWrite:false` water plane (Gerstner at Y=0) drawn after the terrain can paint over land
   that is technically above it, making land appear to "vanish" beneath water. Transparent
   materials don't write depth, so draw order, not geometry, decides the winner. Ensure terrain is
   opaque with `depthWrite:true`, water is sorted/drawn correctly, and consider `renderOrder` and
   the actual Y of land vs the water plane.

8. **Double-sided / backface.** A single-sided terrain mesh with inverted winding (common after
   DEM→mesh export with flipped axes/Y-up vs Z-up) renders only from below, so from a normal
   top-down view the land is invisible. Check `side: DoubleSide` during diagnosis and fix winding
   for production.

---

## 4. Authoring a correct multi-LoD tileset from a DEM

### 4.1 Pipeline shape
1. **Prep the DEM (gdal).** Reproject/clip the CUDEM topobathy to working CRS, fill/handle
   nodata, optionally build a single vertically-exaggerated, NAVD88-referenced grid. `gdalwarp`,
   `gdal_translate`, `gdalbuildvrt`, `gdaldem` for derivatives.
2. **Tile spatially (quadtree).** Cut the DEM into a quadtree pyramid. At each level produce a
   mesh per tile covering that tile's footprint, with consistent edge vertices to neighbors.
3. **Decimate per level.** Coarser levels use fewer triangles (mesh simplification / TIN or
   regular-grid decimation). The decimation amount determines the level's `geometricError`.
4. **Assign `geometricError` per level.** Root largest; halve down the tree (implicit default) or
   set explicitly so it decreases monotonically; **leaves ≈ 0**. A common practical estimate is
   the vertical/feature error introduced by simplification (e.g. Hausdorff distance between the
   simplified tile and the full-res DEM), not an arbitrary constant.
   Sources: https://github.com/CesiumGS/3d-tiles/issues/162 ,
   https://community.cesium.com/t/how-to-compute-the-geometricerror-in-3d-tiles/4171
5. **Emit GLB content + tileset.json** (prefer **implicit tiling** so you only declare the root
   error and subdivision; the client derives the rest). Add `KHR_mesh_quantization` /
   `EXT_meshopt_compression` to shrink payloads and avoid the cache trap in §3.4.

### 4.2 Tools
- **gdal** — DEM reprojection, clipping, nodata, hillshade/derivatives (preprocessing).
- **py3dtiles** — Python; build tilesets and set per-tile geometric error
  (`Tile(geometric_error=..., bounding_volume=bv)`); useful for custom DEM→glTF pipelines.
- **CesiumGS 3D Tiles tools / `3d-tiles-tools`** — validate, convert, upgrade 1.0→1.1, combine
  tilesets, inspect implicit subtrees.
- **pg2b3dm** — PostGIS→3D Tiles; `geometricerror` parameter takes a list matching LoD levels;
  with implicit tiling only the first value is needed and the rest are computed.
  Source: https://github.com/Geodan/pg2b3dm (geometricerror docs).
- **cdb2tiles** — OGC CDB (which is inherently multi-LoD terrain/imagery) → 3D Tiles; good when a
  CDB-style elevation store already exists.
- **QGIS** — DEM inspection, reprojection, clipping, visual QA of the source grid and isobaths.
- **Cesium ion / STK Terrain** — managed quantized-mesh generation (Cesium-native path; not our
  three.js renderer, but a benchmark for correctness).

### 4.3 Validation checklist before wiring into the scene
- Multi-level hierarchy exists (root + ≥2 refinement levels), not one tile.
- `geometricError` strictly decreases root→leaf; leaves ≈ 0; root large.
- Bounding volumes finite, non-degenerate, spatially coherent parent⊇child.
- Tile textures small (≤256–512²) or compressed; total within LRU budget.
- Run through `DebugTilesPlugin` (SSE / GEOMETRIC_ERROR / bounds color modes) per the
  3DTilesRendererJS `TESTCASES.md` recipes before integration.

---

## Implications for orcast

Our pilot is a **single root tile, no LoD**, in EPSG:32610 (large UTM coordinates), with a
Gerstner water plane at Y=0, rendered by `3d-tiles-renderer@0.4.28` (post-0.4.13, i.e. it
contains the corrected traversal that **stops at tiles meeting the error threshold**). Every
documented "vanishing terrain" mode in §3 is reachable from this configuration. Mapped fixes,
ordered by likelihood and cost:

1. **The root cause is structural: a single untiled tile is outside the SSE/HLOD regime.** The
   correct, durable fix is §4 — bake a **multi-LoD implicit-tiling quadtree** from the CUDEM DEM
   with monotonically decreasing `geometricError` and small/compressed per-tile textures. This is
   the recommendation to carry into the W2 integrator decision. (This is the same conclusion the
   3DTilesRendererJS maintainer reaches for poorly-structured single/empty-root tilesets in
   issues #1517 and #1304.)

2. **Immediate unblock without re-baking (matches the documented workaround):** on
   `load-tile-set`, force refinement so the lone tile is never culled away by SSE —
   `tiles.addEventListener('load-tile-set', ({ tileSet }) => { tileSet.root.geometricError = Infinity; })`
   — and raise the cache so a large baked texture cannot starve loading:
   `tiles.lruCache.maxBytesSize = Infinity; tiles.lruCache.minBytesSize = 0;` (cesiumCompare-style).
   Refs: issues #1517, #1304, #1178.

3. **Verify culling/visibility of the single mesh.** Confirm `autoDisableRendererCulling` is
   leaving the tile's `frustumCulled=false`; if not, the whole surface flips in/out as one unit.
   Use `DebugTilesPlugin` bounds display to confirm the bounding volume is finite (no NaN) and
   actually contains the geometry. Ref: API.md, issue #1517.

4. **Depth/coordinate precision in EPSG:32610.** UTM eastings/northings (~5–6e5) uploaded into
   Float32 lose precision and z-fight against the water plane. Recenter the terrain on a **local
   origin** (subtract a fixed datum) so coordinates are small, tighten camera `near`/`far`, and
   only then consider `logarithmicDepthBuffer` (watch the early-Z/overdraw cost from the water and
   any foliage). Refs: large-coordinate-rendering; three.js depth-buffer discourse/SO.

5. **Water vs land paint order (very likely contributor given "water always present, land
   vanishes").** Make the terrain **opaque with `depthWrite:true`**, ensure the transparent
   Gerstner plane sorts/draws after terrain and does not `depthWrite:false`-overwrite land above
   Y=0, set `renderOrder` explicitly, and during diagnosis flip terrain to `DoubleSide` to rule
   out inverted winding from the DEM→GLB export. This is consistent with R4/R6 territory and
   should be cross-checked there.

Recommended sequencing: apply (2)+(3)+(5) as a same-day diagnostic to confirm the surface can be
made stable; then commit to (1) — a real multi-LoD tileset — as the production answer before the
W2 Phase-B integrator runs. Items (4) and (5) are required regardless of tiling.

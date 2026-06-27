# Decision record draft, orcast terrain+bathymetry coastal twin

Date: 2026-06-27 (America/New_York). Lane: O0 orchestrator, 3d-twin only.
Home: `.cca/catalogue/O0/20260627_3d-twin/`. Status: DRAFT, operator-gated.

This instantiates `WAVESET_CHARTER_TEMPLATE.md` section 1 (decision record) and answers
section 7 (open questions) for the orcast worked example: a San Juan / Salish Sea coastal
twin where one land DEM joined to seafloor bathymetry renders in the existing Three.js
scene and the same geometry feeds the depth/habitat science consumer.

This is a draft for operator confirmation. Cells marked **OPERATOR DECISION** are the ones
that are genuinely the operator's to set; the rest carry a recommended fill plus rationale
grounded in the existing code surface. No wave launches and no commit happen on this draft.

---

## 0. Code surface this twin extends (verified by reading the repo)

- Convergence file (render, single editor target): `web/app/components/scene/SalishScene.tsx`.
  It is the only file in `web/` that imports `three` / `@react-three/fiber`, builds the
  terrain `BufferGeometry` from a depth grid, mounts a water plane, hydrophone beacons, a
  focus marker, lights, and `OrbitControls`. Entry chain: `web/app/page.tsx` ->
  `AdaptiveExplore.tsx` -> `web/app/components/scene/SceneHost.tsx` (WebGL check + Google
  Maps fallback) -> `SalishScene`.
- Geographic projection / sampling: `web/lib/sceneIntent.ts` (`projectToScene`,
  `unprojectFromScene`, `sampleDepth`, `sceneDepth`, `HEIGHT_SCALE = 0.04`,
  `SCENE_WIDTH = 120`).
- Render geometry asset (current): `web/public/geo/salish_heightmap.json`, a 31x19 grid
  (`step_deg 0.0166667`, ~1 arc-minute, ~1.85 km posting), `min_depth -320`, `max_depth 621`.
- Science consumer side: `src/aws_backend/sources/bathymetry.py` (`BathymetryAdapter`,
  nearest-grid depth lookup, the `s_space` depth covariate in
  `docs/methodology/FORECAST_KERNELS.md`), reading the committed asset
  `data/geo/san_juan_bathymetry.json` (same ETOPO1 source, point-list form). Consumed by
  `src/aws_backend/spatial_enrichment.py` over `SAN_JUAN_BOUNDS`.
- Region of record: `SAN_JUAN_BOUNDS` in `src/aws_backend/geo_region.py` =
  `min_lat 48.40, max_lat 48.70, min_lng -123.25, max_lng -122.75`.
- Web dependency manifest: `web/package.json`. Present: `three ^0.169.0`,
  `@react-three/fiber ^8.18.0`, `@react-three/drei ^9.122.0`,
  `@vis.gl/react-google-maps ^1.5.0`. **`3d-tiles-renderer` is NOT present** (must be added
  by the single designated manifest editor in the wave that mounts tiles).

Key observation: render and science already read the SAME ETOPO1 relief source (positive
altitude = land, negative = seafloor on one axis), so the "single source of truth" principle
is already partly realized, but only at ETOPO1's coarse ~1 arc-minute posting and as a raw
grid rather than tiled glTF. This twin upgrades that one shared source to a higher-resolution
welded land+bathymetry mesh served as 3D Tiles, without splitting it into two pipelines.

---

## 1. Decision record (charter section 1)

| Decision | Choice | Rationale / source |
|----------|--------|--------------------|
| Geometry source | self-hosted owned/public data | Locked (charter B.2). The `s_space` science consumer in `bathymetry.py` extracts depth values; managed photoreal tiles commonly forbid measurement/geodata extraction. Use owned DEM + owned bathymetry. |
| Tile format | OGC 3D Tiles 1.1 (glTF) | Locked (charter B.3). Renders in plain Three.js via `3d-tiles-renderer`, no Cesium runtime, so the existing `SalishScene` overlays (beacons, focus, picking) stay native. |
| Render runtime | extend existing Three.js scene | Locked (charter B.4). Extend `web/app/components/scene/SalishScene.tsx`; preserve `OrbitControls`, hydrophone beacons, focus marker, click-to-`SceneIntent` picking, and the `SceneHost` Maps fallback. |
| Single source of truth | yes (one geometry feeds render + science) | Locked (charter B.5). One welded land+bathymetry mesh produces both the render tiles (vector mesh) and the rasterized depth/slope field the `s_space` covariate consumes. Prevents the picture and the numbers drifting, and supersedes the two current ETOPO1 copies (`salish_heightmap.json` + `san_juan_bathymetry.json`) with one provenance chain. |
| Conversion host | **OPERATOR DECISION** | Locked principle (charter B.6): heavy converters (GDAL/PostGIS, tilers, gltfpack) run natively on the matching CPU arch, never under emulation. Options in section 2. Must be confirmed before the first heavy conversion. |
| Source DEM (land) | **OPERATOR DECISION**, recommend USGS 3DEP 1/3 arc-sec (~10 m), or 1 m lidar where covered | Public, licensed for measurement, covers the San Juans. Section 3 lists the alternative. |
| Source bathymetry (seafloor) | **OPERATOR DECISION**, recommend NOAA NCEI Puget Sound / Salish Sea bathymetric DEM (e.g. the regional CUDEM / coastal relief tiles), GEBCO 2024 as coarse fallback | Public, measurement-licensed, far finer than ETOPO1's 1 arc-min. Section 3. |
| Target CRS | **OPERATOR DECISION**, recommend EPSG:32610 (UTM zone 10N, metres) | The bbox (48.40-48.70 N, -123.25 to -122.75 W) sits squarely in UTM 10N; a projected metric CRS gives clean planar meshing and a local engineering frame for `3d-tiles-renderer`. |
| Vertical reference | **OPERATOR DECISION**, recommend NAVD88 orthometric height in metres, both layers transformed via NOAA VDatum | The footgun (charter B.9): land DEM is on a land datum (NAVD88 / ellipsoid), bathymetry on a tidal datum (MLLW). Both must convert to ONE metric vertical reference before meshing or the coastline will not join. NAVD88 metres via VDatum is the standard reconciliation for this region; ellipsoidal (NAD83) is the alternative. |
| Downstream science consumer | depth/slope field feeding `s_space` (depth/habitat prior) | The existing `BathymetryAdapter` + `spatial_enrichment.py` over `SAN_JUAN_BOUNDS` is the live consumer. First derived layer = depth (and optionally slope/aspect) rasterized from the same welded mesh. Line-of-sight is a later option, not first-wave. |

Worked-example footguns restated (must hold in the reproject+datum recipe agent, Wave 1):

1. Vertical datum reconciliation. Transform the land DEM (NAVD88/ellipsoid) and the
   bathymetry (MLLW/tidal) to one metric vertical reference (recommended NAVD88 metres via
   VDatum) BEFORE meshing. This is the analog of the NYC feet-to-metres + z-up-to-y-up fix.
2. Coastline seam weld. Terrain and bathymetry must meet at the shoreline with no gap and no
   overlap (analog of the NYC double-drawn-buildings gate). Use one authoritative coastline
   (the existing `data/geo/san_juan_land.geojson` land mask is the in-repo candidate) to clip
   and weld the two surfaces into one continuous mesh.

---

## 2. Conversion host options (charter section 7, operator decision)

The first heavy conversion (DEM + bathymetry reproject, datum transform, mesh, weld, tile,
gltfpack) needs a host matching the converter binaries' CPU arch so PostGIS/GDAL/tilers do
not crash under emulation.

| Option | What it is | Pros | Cons | Note |
|--------|-----------|------|------|------|
| Local (this machine) | run natively on the operator's Mac (arm64) | zero provisioning, fast iteration on one pilot chunk | must use arm64-native GDAL/PDAL/gltfpack builds, not x86 under Rosetta; heavy full-extent bakes compete with the dev box | viable for the Wave 1 single-chunk pilot only |
| Shared host | an existing team box | no new cloud spend | arch must be confirmed; contention risk | needs reachability + arch check first |
| Dedicated matching-arch cloud box | a provisioned VM matching the converter arch | isolates heavy bakes, scales to full extent, no Rosetta | provisioning + cost; must confirm reachability before first conversion | recommended for the Wave 2/3 full-extent bake |

Recommendation to the operator: do the Wave 1 single-chunk pilot locally on arm64-native
tools (cheap, fast), and provision a dedicated matching-arch box before the Wave 2 full-extent
batch conversion. Operator confirms.

---

## 3. Source options for DEM and bathymetry (operator decision)

Land DEM (pick one):
- USGS 3DEP 1/3 arc-second (~10 m) seamless DEM. Recommended baseline: full San Juan coverage,
  measurement-licensed, easy national coverage.
- USGS 3DEP 1 m lidar DEM where tiles exist over the islands. Highest fidelity for the render;
  larger data and patchier coverage. Could be used over 3DEP 10 m only where available.

Seafloor bathymetry (pick one):
- NOAA NCEI regional bathymetric/coastal-relief DEM for Puget Sound / Salish Sea (e.g. the
  CUDEM / coastal relief tiles). Recommended: far finer than ETOPO1, measurement-licensed.
- GEBCO 2024 (~15 arc-sec). Coarse fallback / coverage gap filler only.
- ETOPO1 (current). Too coarse (~1 arc-min) to be the upgrade target; keep only as the
  provenance baseline the new mesh replaces.

Both layers must be licensed for measurement (charter B.2) and both must carry a stated
vertical datum so the Wave 1 datum agent can transform them to the one chosen reference.

---

## 4. Section 7 open questions, drafted answers

| Open question | Draft answer / recommendation | Who decides |
|---------------|------------------------------|-------------|
| First-wave scope: include the science spike, or defer it? | Recommend INCLUDE a lightweight science spike in Wave 1, because the single-source-of-truth principle (B.5) is the whole point and there is already a live consumer (`BathymetryAdapter` / `s_space`). The spike = rasterize a depth (and optionally slope) field from the one pilot mesh chunk and confirm `BathymetryAdapter` can read it. Keep it to one chunk so it does not gate the render path. | operator |
| Conversion host: local / shared / dedicated? | Recommend local arm64-native for the Wave 1 pilot chunk; dedicated matching-arch box before the Wave 2 full-extent bake. See section 2. | operator (must confirm before first heavy conversion) |
| Subagent model: inherit vs pin? | Recommend pinning a strong model for the build-heavy Wave 1 agents (reproject+datum recipe, tiler bake-off) given the geospatial correctness risk; inherit for the lighter sandbox/realism agents. Specific model slug is the operator's call. | operator |
| Worked-example specifics (DEM, bathymetry, CRS, vertical ref, consumer) | DEM = USGS 3DEP 10 m (1 m lidar where covered); bathymetry = NOAA NCEI Salish Sea DEM (GEBCO fallback); CRS = EPSG:32610 (UTM 10N, m); vertical = NAVD88 m via VDatum; consumer = depth/slope field for `s_space`. All recommendations; operator confirms each. | operator |

---

## 5. Proposed Wave 1 shape (NOT launched, for operator review only)

If the operator confirms section 1 and section 4, Wave 1 (6 parallel agents, no edits to
`SalishScene.tsx`, type-check validation only, one integration commit at wave end) would be:

1. Realism module: water surface + atmosphere/fog + sun + ocean depth color ramp, against a
   throwaway scene (owns a new module file, not the convergence file).
2. Reproject + datum recipe: reproject DEM + bathymetry to EPSG:32610, transform both to the
   one chosen vertical reference (VDatum), mesh both, weld the coastline seam against the
   land mask. THIS AGENT OWNS THE TWO FOOTGUNS.
3. Tiler bake-off: meshed-DEM-to-3D-Tiles vs quantized-mesh terrain on one coastal chunk;
   compare size / draw calls / fidelity; recommend one.
4. Optimize + assemble pilot: gltfpack/meshopt + 3D Tiles validator on one coastal chunk;
   report real sizes; push the artifact to object storage, not git.
5. Renderer sandbox: an isolated Next.js route that mounts the pilot tileset via
   `3d-tiles-renderer`; confirm terrain and seafloor both load. No `SalishScene.tsx` edits.
6. Science spike: rasterize a depth/slope field from the pilot mesh; confirm `BathymetryAdapter`
   ingests it; label output "modeled, not measured".

Manifest editor for the wave (the only agent that adds `3d-tiles-renderer` to
`web/package.json`): the renderer-sandbox agent. Gate to Wave 2: the pilot tileset validates
AND the sandbox renders it.

---

## 6. Risks

- Primary: vertical-datum + coastline-seam correctness. If the land DEM (NAVD88/ellipsoid) and
  bathymetry (MLLW) are not transformed to one metric reference before meshing, the shoreline
  will show a vertical step or a gap/overlap, and the science depth field inherits the error.
  Mitigation: the Wave 1 reproject+datum agent owns this end to end with VDatum, validated
  against the in-repo land mask coastline before any tiling.
- Secondary: arm64 vs x86 converter arch. Native arm64 builds of GDAL/PDAL/gltfpack must be
  confirmed before the first conversion, or the tilers crash under emulation (charter B.6).
- Tertiary: source-license check. Both DEM and bathymetry must be confirmed measurement-licensed
  before they feed the `s_space` science consumer (charter B.2).

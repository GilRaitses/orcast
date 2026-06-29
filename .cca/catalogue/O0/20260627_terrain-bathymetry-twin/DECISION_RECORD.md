# Decision record, orcast terrain+bathymetry coastal twin

Date: 2026-06-27 (America/New_York). Lane: O0 orchestrator, 3d-twin only.
Home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`. Status: CONFIRMED by operator
2026-06-27. Instantiated from `.cca/catalogue/O0/20260627_3d-twin/WAVESET_CHARTER_TEMPLATE.md`
section 1 (decision record) + section 7 (open questions).

Worked example: a San Juan / Salish Sea coastal twin where one integrated land+seafloor
elevation surface renders in the existing Three.js scene and the same geometry feeds the
depth/habitat science consumer (`s_space`).

Operator confirmations (this rotation):
1. First-wave scope: run all six Wave 1 agents (science spike included; re-run the spike later
   if helpful).
2. Conversion host: aimez.ai EC2 on AWS.
3. Subagent model: inherit the orchestrator's model.
4. Worked-example data: confirmed, grounded below (CUDEM adopted as the primary integrated
   source after grounding; see section 3).
5. Instantiate: this home (copied from the template).

No commit, no push, and no agent launch happen on this document. Wave 1 launch is the next
operator gate.

---

## 0. Code surface this twin extends (verified by reading the repo)

- Convergence file (render, single editor target): `web/app/components/scene/SalishScene.tsx`.
  Only file in `web/` that imports `three` / `@react-three/fiber`; builds the terrain
  `BufferGeometry` from a depth grid, mounts a water plane, hydrophone beacons, a focus marker,
  lights, and `OrbitControls`. Entry chain: `web/app/page.tsx` -> `AdaptiveExplore.tsx` ->
  `web/app/components/scene/SceneHost.tsx` (WebGL check + Google Maps fallback) -> `SalishScene`.
- Geographic projection / sampling: `web/lib/sceneIntent.ts` (`projectToScene`,
  `unprojectFromScene`, `sampleDepth`, `sceneDepth`, `HEIGHT_SCALE = 0.04`, `SCENE_WIDTH = 120`).
- Render geometry asset (current): `web/public/geo/salish_heightmap.json`, ~1 arc-minute
  (~1.85 km) grid. This is the placeholder geometry to retire (NYC heightfield analog).
- Science consumer side: `src/aws_backend/sources/bathymetry.py` (`BathymetryAdapter`,
  nearest-grid depth lookup, the `s_space` depth covariate in
  `docs/methodology/FORECAST_KERNELS.md`), reading `data/geo/san_juan_bathymetry.json` (ETOPO1,
  point-list form). Consumed by `src/aws_backend/spatial_enrichment.py` over `SAN_JUAN_BOUNDS`.
- Region of record: `SAN_JUAN_BOUNDS` in `src/aws_backend/geo_region.py` =
  `min_lat 48.40, max_lat 48.70, min_lng -123.25, max_lng -122.75`.
- Web dependency manifest: `web/package.json`. Present: `three ^0.169.0`,
  `@react-three/fiber ^8.18.0`, `@react-three/drei ^9.122.0`. **`3d-tiles-renderer` is NOT
  present** (added by the single designated manifest editor in the wave that mounts tiles).

Key observation: render and science already read the SAME ETOPO1 relief source, so the
single-source-of-truth principle is partly realized but only at ETOPO1's coarse posting and as
a raw grid. This twin upgrades that one shared source to a higher-resolution integrated
land+bathymetry surface served as 3D Tiles, without splitting into two pipelines.

---

## 1. Decision record (charter section 1) — CONFIRMED

| Decision | Choice | Rationale / source |
|----------|--------|--------------------|
| Geometry source | self-hosted owned/public data | Locked (charter B.2). The `s_space` consumer extracts depth; managed photoreal tiles forbid measurement/geodata extraction. |
| Tile format | OGC 3D Tiles 1.1 (glTF) | Locked (charter B.3). Renders via `3d-tiles-renderer`, no Cesium; existing `SalishScene` overlays stay native. |
| Render runtime | extend existing Three.js scene (react-three-fiber) | Locked (charter B.4). Extend `SalishScene.tsx`; preserve `OrbitControls`, beacons, focus marker, click-to-`SceneIntent` picking, `SceneHost` Maps fallback. |
| Single source of truth | yes (one geometry feeds render + science) | Locked (charter B.5). One integrated surface produces the render tiles (vector mesh) and the rasterized depth/slope field for `s_space`; supersedes the two ETOPO1 copies with one provenance chain. |
| Conversion host | **aimez.ai EC2 (AWS)** | Operator-confirmed. Heavy converters (GDAL/PDAL, PostGIS, tilers, gltfpack) run natively on the EC2 arch, never under emulation (charter B.6). Confirm reachability + arch before the first heavy conversion. |
| Primary geometry source | **NOAA NCEI CUDEM 1/9 arc-second topobathic-topographic tiles (`wash_bellingham` collection)** | Grounded + corrected 2026-06-27 by agent F: the San Juan bbox is NOT in `wash_pugetsound` (stops ~lat 48.2) nor `strait_of_juan_de_fuca` (ends ~lon -123.52); it is covered by the CUDEM 1/9 **`wash_bellingham`** collection (6 tiles: n48x50/n48x75 x w122x75/w123x00/w123x25). The 1/9 arc-sec (~3 m) CUDEM tiles are the only NCEI resolution that integrate bathymetry AND topography in one DEM, referenced vertically to NAVD88 (EPSG:5703) m, horizontally to NAD83 (EPSG:4269). NOAA merged land+sea across the shoreline via VDatum, so the integrated surface, the vertical-datum reconciliation, and the coastline seam are handled at the source. |
| Land refinement (optional) | USGS 3DEP 1/3 arc-sec (~10 m) or 1 m PSLC lidar, NAVD88, public domain | Grounded (public domain, NAVD88). Use only where finer land relief than CUDEM is wanted; re-introduces the seam weld at the 0 m line if blended. |
| Coarse / cross-border fallback | GEBCO 2024 (and Canadian CHS) — NOT needed for the current bbox | Grounded + measured 2026-06-27 by agent B: the 4 covering `wash_bellingham` tiles mosaic to 100% valid coverage over the full SAN_JUAN_BOUNDS bbox, INCLUDING the Haro Strait / Canadian-side west strip. GEBCO/CHS fill is only required if the extent widens west of -123.25 (Canadian Gulf Islands). |
| Target CRS | EPSG:32610 (WGS84 / UTM zone 10N, meters) | Grounded. The bbox sits squarely in UTM 10N (zone spans -126 to -120). Reproject the NAD83-geographic CUDEM to a projected metric frame for clean planar meshing and a local engineering frame for `3d-tiles-renderer`. NAD83->WGS84 horizontal difference (~1-2 m) noted, negligible at this scale. |
| Vertical reference | NAVD88 orthometric height, meters | Grounded. CUDEM is natively NAVD88 m, so no transform is needed for the primary source. If a non-NAVD88 source is blended (e.g. an MLLW multibeam survey), transform it to NAVD88 m with NOAA VDatum, whose Strait of Juan de Fuca / Puget Sound grids cover this region. |
| Downstream science consumer | depth/slope field feeding `s_space` (depth/habitat prior) | The existing `BathymetryAdapter` + `spatial_enrichment.py` over `SAN_JUAN_BOUNDS` is the live consumer. First derived layer = depth (optionally slope/aspect) rasterized from the same integrated surface. Line-of-sight is a later option. |

---

## 2. Worked-example footguns, restated against the grounded source

The two template footguns are substantially pre-handled by choosing CUDEM, but the Wave 1
reproject+mesh agent still owns them:

1. Vertical-datum reconciliation. Primary source (CUDEM) is already one metric vertical
   reference (NAVD88 m), so the land/sea datum join is done at the source. The agent must
   preserve NAVD88 m through reprojection to EPSG:32610 and meshing (no implicit datum shift).
   The footgun returns only if 3DEP land or an MLLW survey is blended; then VDatum to NAVD88 m
   BEFORE meshing.
2. Coastline seam weld. CUDEM is a continuous topobathy surface, so the shoreline is continuous
   at the source. The agent meshes the single surface and marks the 0 m NAVD88 contour as the
   modeled shoreline (no two-dataset weld needed for the primary path). If a higher-fidelity
   land source is blended, weld at the 0 m line against one authoritative coastline (the in-repo
   `data/geo/san_juan_land.geojson` land mask is the candidate), no gap, no overlap.

---

## 3. Grounding notes (sources verified 2026-06-27)

- CUDEM 1/9 arc-second topobathy, Puget Sound: NCEI `gov.noaa.ngdc.mgg.dem:199919`; tiles at
  `https://coast.noaa.gov/htdata/raster2/elevation/NCEI_ninth_Topobathy_2014_8483/wash_pugetsound/`
  (~4.2 GB full set; subset via Digital Coast Data Access Viewer). 1/9 tiles integrate bathy +
  topo; vertical NAVD88 (EPSG:5703) meters; horizontal NAD83 (EPSG:4269). Public, "available to
  the public for scientific research and analysis."
- USGS 3DEP 1/3 arc-second (~10 m): public domain (`usa.gov/publicdomain/label/1.0`), NAD83 /
  NAVD88. S3: `prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/`. 1 m lidar exists in
  parts of the San Juans via the Puget Sound Lidar Consortium.
- NOAA "Puget Sound 1/3 arc-second NAVD88 Coastal DEM" (`gov.noaa.ngdc.mgg.dem:5165`): an older
  integrated bathy-topo DEM, NAVD88 m, WGS84 horizontal, built with VDatum (THREDDS NetCDF).
  A drop-in alternative to CUDEM if CUDEM tile coverage over the exact bbox is thin.
- VDatum: full coverage for the San Juan Islands / Strait of Juan de Fuca / Puget Sound;
  transforms MLLW <-> NAVD88 (NOS CS-25, Hess et al.). Needed only for non-NAVD88 blends.
- Coverage caveat (grounded): the bbox western edge (-123.25, Haro Strait) abuts Canadian
  waters; US federal sources thin toward the border. The Wave 1 reproject agent must confirm
  CUDEM/3DEP tile coverage over the full bbox and flag any Canadian-side gap for GEBCO/CHS fill.

---

## 4. Conversion host: aimez.ai EC2 (confirmed)

The first heavy conversion (CUDEM fetch/clip, reproject to EPSG:32610, mesh, tile, gltfpack)
runs on the `aimez-services` EC2 (`i-04a649f91274e9fce`, c6i.xlarge), x86_64 Ubuntu 22.04,
4 vCPU, 7.6 GB RAM, ~20 GB free. Reachable `ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177`
and SSM (us-east-1). Has docker + python3; converters run as linux/amd64 docker images natively
(no emulation; charter B.6).

Serving + write infra (grounded 2026-06-27):
- Serving path IS provisioned: CloudFront distribution `EOMERK64CS5CE`
  (`d8kxxpcnj3ub5.cloudfront.net`) fronts the `aimez-data` S3 bucket; the bucket policy lets that
  distribution `s3:GetObject` on `aimez-data/3dtwin/pilot/*`. Bucket public access is fully
  blocked, so the pilot tileset is browser-fetchable at
  `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/...` via OAC, not via a public bucket. This
  is the URL agent E's sandbox should point at in Wave 2.
- Write path is NOT provisioned (BLOCKER): the instance role `aimez-host-role` inline policy
  `aimez-host-s3` only grants access to the `pax-nyc-images` bucket (pax NYC lineage); it grants
  NOTHING on `aimez-data`. Agent F hit `AccessDenied` on PutObject. Until the role is granted
  `s3:PutObject` + `s3:ListBucket` on `aimez-data/3dtwin/*`, agents cannot stage tilesets/rasters
  to S3, so agent D cannot publish the pilot and the Wave 1->Wave 2 gate cannot close. Proposed
  minimal fix: add an inline statement allowing `s3:PutObject`/`s3:GetObject` on
  `arn:aws:s3:::aimez-data/3dtwin/*` and `s3:ListBucket` on `arn:aws:s3:::aimez-data` (prefix
  `3dtwin/*`). Operator-gated IAM change.

---

## 5. Wave 1 shape (CONFIRMED scope, NOT yet launched)

Six parallel agents, no edits to `SalishScene.tsx`, type-check validation only, one integration
commit at wave end (commit gated on explicit operator ask). Full per-agent prompts are in
`WAVE1_DISPATCH.md`.

1. Realism module (new file): water surface + atmosphere/fog + sun + ocean depth color ramp,
   against a throwaway scene.
2. Reproject + mesh recipe (infra, runs on aimez.ai EC2): clip CUDEM to the bbox, reproject to
   EPSG:32610 preserving NAVD88 m, mesh the integrated surface, mark the 0 m shoreline. OWNS THE
   TWO FOOTGUNS.
3. Tiler bake-off (infra): meshed-surface-to-3D-Tiles vs quantized-mesh terrain on one coastal
   chunk; compare size / draw calls / fidelity; recommend one.
4. Optimize + assemble pilot (infra): gltfpack/meshopt + 3D Tiles validator on one chunk; report
   real sizes; artifact to S3, not git.
5. Renderer sandbox (new Next.js route): mount the pilot tileset via `3d-tiles-renderer` inside
   react-three-fiber; confirm terrain and seafloor both load. SOLE MANIFEST EDITOR (adds
   `3d-tiles-renderer` to `web/package.json`).
6. Science spike (infra): rasterize a depth/slope field from the pilot mesh; confirm
   `BathymetryAdapter` ingests it; label output "modeled, not measured".

Model: inherit (operator-confirmed). Gate to Wave 2: the pilot tileset validates AND the
sandbox renders it.

---

## 6. Risks

- Primary (now reduced): vertical-datum + coastline-seam correctness. Choosing CUDEM moves the
  datum/seam reconciliation into the source (one NAVD88 m topobathy surface). Residual risk is
  an implicit datum shift during reprojection/meshing, or a blended non-NAVD88 source bypassing
  VDatum. Mitigation: the Wave 1 reproject agent preserves NAVD88 m end to end and uses VDatum
  for any blend.
- Render integration: the scene is react-three-fiber, not raw Three.js. `3d-tiles-renderer` is
  imperative (own `update()`/camera/LoD). The Wave 1 renderer-sandbox agent must prove the
  r3f + `TilesRenderer` mount pattern (shadows, `OrbitControls`, picking) before Wave 2 touches
  the live scene.
- aimez.ai EC2 arch: confirm `uname -m` and use native converter builds before the first
  conversion, or the tilers crash under emulation (charter B.6).
- Cross-border coverage: US federal DEMs thin toward the Canadian boundary at the bbox west
  edge; confirm coverage and flag gaps for GEBCO/CHS fill.

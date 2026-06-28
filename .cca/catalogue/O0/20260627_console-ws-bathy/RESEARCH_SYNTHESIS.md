# WS-BATHY research synthesis

Home: `.cca/catalogue/O0/20260627_console-ws-bathy/`
Date: 2026-06-27. Wave: Research. Status: COMPLETE, read-only, doc-producing.
Served extent under study: lat 48.4 to 48.7, lng -123.25 to -122.75 (`TILESET_BOUNDS` in `web/app/components/scene/SalishScene.tsx`, identical to `SAN_JUAN_BOUNDS` and the substrate field bounds).

## 1. The live underwater stack, read from the repo

### 1.1 water2, the depth-driven ocean

`web/lib/scene/water2/` exports `makeWater2` and the types `Water2Options` and `Water2Handle` (`web/lib/scene/water2/index.ts`). The technique lives in `web/lib/scene/water2/depthWater.ts`.

How it reads the seabed depth:

1. A depth pre-pass renders the opaque scene (the terrain tiles, water mesh hidden) into a `WebGLRenderTarget` carrying a `DepthTexture`. The caller runs `handle.renderDepthPrepass(renderer, scene, camera)` once per frame before the main render.
2. The water fragment shader samples that depth texture at its own screen-space fragment, reconstructs the seabed world position through the inverse view-projection matrix, and computes the vertical water-column thickness as `column = uWaterLevel - seabed.y`. Where terrain sits at or above the surface the column is clamped to zero and the water clears to reveal land.
3. A Beer-Lambert style map turns column thickness into alpha and a shallow-to-deep color, `colorT = 1 - exp(-column / uDepthColorScale)` and `depthAlpha = 1 - exp(-column / uDepthAlphaScale)`, with a thin near-shore foam band, Fresnel sky reflection, and sun glitter.

The water plane stays at scene Y = 0, the visible waterline the streamed tiles poke through. The datum the ramp measures from is exactly the surface the operator sees.

Tunable public surface (`Water2Options`): `colorShallow`, `colorDeep`, `colorFoam`, `skyColor`, `sunDirection`, `amplitude`, `speed`, `depthColorScale` (default 0.3), `depthAlphaScale` (default 0.3), `foamDepth` (default 0.08), `maxOpacity` (default 0.96), `fresnelStrength` (default 0.5), plane `width`, `depth`, `segments`, `level`. The fragment shader carries a debug uniform `uDebug` that, when set, renders the water-column thickness as grayscale, the exact instrument needed for a real depth-read visual check at acceptance.

Important: the color and alpha are driven by a single scalar column thickness through a two-stop color lerp `mix(uColorShallow, uColorDeep, colorT)`. Absorption is not yet per-channel RGB. This is the main styling lever the Water and Depth Stylist proposes to the water2 owner.

### 1.2 substrate, the modeled CUDEM depth field

`web/lib/scene/substrate/` exports `loadSubstrate`, `sampleSubstrate`, `buildSubstrateOverlay`, `SUBSTRATE_URL`, `SUBSTRATE_LABEL`, and the field types (`web/lib/scene/substrate/index.ts`). The contract is in `web/lib/scene/substrate/WIRING-substrate.md`.

- `loadSubstrate(url?)` fetches and parses `/geo/sample_san_juan_bathymetry_cudem.json` into a typed `SubstrateField`, computing `minDepthM` and `maxDepthM` once. The asset is fetched, not bundled, so it can be swapped without a web rebuild.
- `sampleSubstrate(field, lat, lng)` returns nearest-neighbour depth in metres by equirectangular distance with longitude scaled by `cos(lat)`. It is a faithful mirror of the Python `BathymetryAdapter.depth_at` in `src/aws_backend/sources/bathymetry.py`. `depth_m` is negative below sea level and positive on land. It returns `NaN` for no data so a real 0 m reading is distinguishable.
- `buildSubstrateOverlay(field, opts?)` builds an optional toggleable `THREE.Points` cloud tinted on a `colorDeep` to `colorShore` to `colorHigh` ramp over the field depth extent. It is tagged for honesty, `userData.modeledNotMeasured = true`, `userData.label = "modeled, not measured"`, and the name carries the same.

Field metadata, read from `web/public/geo/sample_san_juan_bathymetry_cudem.json`:

- source `NOAA NCEI CUDEM 1/9 arc-sec topobathy, wash_bellingham collection`.
- bounds 48.4 to 48.7 N, -123.25 to -122.75 W. resolution 0.005 deg (about 370 m N-S), 100 by 60 = 6000 cells.
- depth extent in this grid -349.7 m (Haro Strait channel) to 679.9 m (Orcas Island upland), mean about -26 m. From `infra/3dtwin/science/SCIENCE-SPIKE.md`.
- provenance string starts `MODELED, NOT MEASURED. Depth field rasterized from NOAA NCEI CUDEM 1/9 arc-second topobathy (wash_bellingham collection), the integrated land+seafloor surface that also feeds the 3D render tiles`.

### 1.3 how SalishScene composes the two

`web/app/components/scene/SalishScene.tsx`:

- `Water2Rig` builds `makeWater2` with `width = SCENE_WIDTH * 1.6`, `depth = SCENE_DEPTH * 1.6`, `level = 0`, sun direction and sky color from the realism `makeSun`. Each frame it runs the depth pre-pass then `handle.update`. The agent-A flat realism water is disabled (`water: false`) because water2 replaces it.
- The substrate field is loaded once (`loadSubstrate().then(setField)`) and used ONLY to fill `depth_m` on a pick, `const d = field ? sampleSubstrate(field, lat, lng) : NaN`. The pick emits a `SceneIntent` with `depth_m` set from the modeled CUDEM substrate.

So the labels pick `depth_m` as MODELED CUDEM depth, not a measured sounding. The substrate overlay `buildSubstrateOverlay` is built but is NOT currently mounted in the live scene, it is an available data layer.

The seabed the water reads is the tile mesh itself, NOT the substrate field. The substrate field is the pick-depth lookup and an optional point overlay. This distinction drives the whole discovery and dispatch.

## 2. Is the CUDEM tileset already topobathy

Resolved: YES. The served tileset is topobathy and the seafloor is already baked into the render geometry.

Evidence from the repo:

- `infra/3dtwin/host/WIRING-host.md`, the full-extent tileset contract the live `SalishScene.tsx` consumes (`FULL_TILESET_URL`), states the elevation range is -376.431 to +733.885 m NAVD88, vertical NAVD88 m at true 1:1 scale, Y = NAVD88 elevation, sea level NAVD88 0 m maps to scene Y 0. Provenance, NOAA NCEI CUDEM 1/9 arc-second topobathy `wash_bellingham`, reprojected NAD83 to EPSG:32610 with NAVD88 m preserved. Modeled, not measured. A -376 m floor in the served mesh is the seafloor of the deep Haro Strait channel, so bathymetry is in the geometry.
- `infra/3dtwin/science/SCIENCE-SPIKE.md` confirms the same `wash_bellingham` source and that the science depth field and the render tiles read the identical NCEI tiles, one geometry, no second pipeline.

Evidence from the data source itself:

- NOAA NCEI CUDEM metadata states the 1/9 arc-second tiles are the ONLY resolution that integrates BOTH bathymetric and topographic data, the coarser 1/3 and 3 arc-second tiles map bathymetry only. The served tileset is the 1/9 arc-second product, so it is the integrated land plus seafloor surface. Source, NOAA NCEI CUDEM 1/9 arc-second metadata landing page, https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.dem%3A199919 .

Consequence for the waveset: the Bathy Terrain Builder does NOT need to author a separate seabed mesh for the water to read. The seabed exists. The builder work is a depth field and tinting that reads the existing seabed and substrate, plus reconciling any added measured reference WITHOUT introducing a competing geometry or a datum seam at the shoreline.

## 3. Bathy data source survey, provenance and licence

All depths discussed are NAVD88 metres positive up unless noted. The served extent is split by the international marine border that runs through Haro Strait and Boundary Pass, so a full truthful coverage needs a US source and a Canadian source.

### 3.1 NOAA NCEI CUDEM 1/9 arc-second topobathy, wash_bellingham (already baked, the seabed the water reads)

- What. The integrated land plus seafloor DEM that built both the render tiles and the substrate depth field. Native 1/9 arc-second, about 3 m. Served in the tiles at a leaf ground sample distance near 10 m, and rasterized in the substrate field at 0.005 deg.
- Provenance. CUDEM is a MODELED gridded surface built FROM measured sources, NOAA Office of Coast Survey hydrographic surveys, NOAA National Geodetic Survey, NOAA Office for Coastal Management, USGS, and USACE, with topographic and topo-bathy lidar, multibeam sonar, and hydrographic soundings. It carries FGDC spatial-metadata shapefiles that record the source agency, year, and method per area, so relative accuracy can be inferred. Sources, NCEI CUDEM metadata landing page and Amante et al. 2023, Remote Sensing 15(6) 1702, https://repository.library.noaa.gov/view/noaa/50089 .
- Land validation. The CUDEM land portion was validated against ICESat-2 ATLAS with a vertical mean bias 0.12 m and RMSE 0.76 m (Amante et al. 2023). This is a land statistic, not a seafloor accuracy.
- Licence. Public domain, not subject to US copyright. The CUDEM toolchain `ciresdem/cudem` is MIT.
- Coverage of the served extent. Full on the US side. The science spike already proved `wash_bellingham` 1/9 tiles tile the whole San Juan bbox, and noted that `wash_pugetsound` and the regional `puget_sound` DEM stop near 48.19 to 48.25 N south of the bbox, and `strait_of_juan_de_fuca` covers west of -123.52 only. `wash_bellingham` is the correct collection.
- Honesty label. Modeled, not measured. Keep `SUBSTRATE_LABEL = "modeled, not measured"`. CUDEM must not be relabelled as measured even though it is built from measured soundings, because it is an interpolated grid.

### 3.2 NOAA BlueTopo, the National Bathymetric Source (recommended MEASURED provenance reference, US side)

- What. NOAA Office of Coast Survey curated nationwide compilation of the best available seafloor bathymetry. Three-layer 32-bit float GeoTIFF, an elevation layer, an uncertainty layer, and a Raster Attribute Table.
- The honesty signal. The RAT carries a per-pixel `bathy_coverage` boolean. If true the value is sourced from a MEASURED depth, if false it is an interpolated value. This is the exact measured-versus-modeled flag the Honesty Labeler needs, per area, not per dataset. There is also a `coverage` flag for full seafloor coverage. Source, BlueTopo specifications, https://www.nauticalcharts.noaa.gov/data/bluetopo_specs.html .
- Datum. Elevation increasingly negative with depth, positive landward, vertical datum NAVD88, the same datum as the served CUDEM tiles. This means a BlueTopo reference can be compared to the modeled seabed with no vertical transform.
- Provenance. Built from NOAA and USACE hydrographic surveys and topo-bathy lidar, plus external source data. Gaps deeper than 200 m are filled with Global Multi-Resolution Topography from Lamont-Doherty. Updated weekly to monthly. Source, NOAA National Bathymetric Source, https://nauticalcharts.noaa.gov/learn/nbs.html and BlueTopo InPort record https://www.fisheries.noaa.gov/inport/item/75311 .
- Caveat. Not for navigation. Generalization is not limited by the shoreline, so erroneous interpolation can occur over land where no data exist, which is why it is a reference and mask source, not a rendered seabed.
- Licence. Public domain through NOAA Open Data Dissemination and nowCOAST.
- Coverage of the served extent. US navigable waters of the San Juan archipelago, Rosario Strait, and the US side of Haro Strait. The 2024 NOAA hydrographic survey season was actively resurveying Puget Sound, so coverage and recency are improving. Source, https://nauticalcharts.noaa.gov/updates/noaas-2024-hydrographic-survey-season-is-underway/ .

### 3.3 Canadian Hydrographic Service NONNA-10 and NONNA-100 (recommended MEASURED reference, BC side)

- What. CHS Non-Navigational bathymetry for Canadian marine space, the BC side of Haro Strait and Boundary Pass north of the marine border. Available at 10 m (NONNA-10) and 100 m (NONNA-100). Formats BAG, CSAR, GeoTIFF, ASCII, plus WMS, WCS, WMTS services. A backscatter intensity layer indicates seafloor hardness and roughness.
- Provenance. Measured CHS hydrographic data, multibeam echo and lidar, released after validation steps. Measured, not modeled.
- Datum. Chart datum, Lower Low Water Large Tide, which differs from NAVD88 by roughly 1.5 to 3 m in this region. A NONNA depth must be datum-shifted before any numeric comparison to the CUDEM seabed, and it is safest to use NONNA only as a labeled reference and coverage signal, not as rendered geometry.
- Licence. Open Government Licence Canada. Requires attribution and is non-navigational. Sources, CHS NONNA open data record https://open.canada.ca/data/en/dataset/d3881c4c-650d-4070-bf9b-1e00aabf0a1d and the NONNA portal https://www.charts.gc.ca/data-gestion/nonna/index-eng.html .
- Coverage gaps. The portal notes some surveyed data is not yet ingested, so Canadian coverage is partial and must be treated as present-where-available.

### 3.4 GEBCO_2024 (context only, too coarse for this extent)

- What. Global terrain model, 15 arc-second (about 450 m). Carries a Type Identifier grid that marks each cell as measured, interpolated, or predicted from gravity, a useful honesty precedent.
- Licence. Public domain, attribution requested, `GEBCO Compilation Group (2024) GEBCO 2024 Grid (doi:10.5285/1c44ce99-0a0d-5f4f-e063-7086abc0ea0f)`. Must not imply IHO or IOC endorsement.
- Verdict. At 450 m it is coarser than the 0.005 deg substrate and far coarser than the 10 m tiles. Use only as wide-context narrative, never as the seabed or a per-cell honesty source for this extent. Source, https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2024-grid .

### 3.5 Source recommendation

- Keep the baked NOAA NCEI CUDEM 1/9 arc-second topobathy (`wash_bellingham`) as the seabed the depth-driven water reads, and the substrate field as the pick-depth lookup. Label modeled, not measured. Do not swap in a second seabed geometry.
- Adopt NOAA BlueTopo (US) plus CHS NONNA (BC) as a MEASURED provenance reference, used to drive an honesty coverage signal that marks where the modeled seabed is backed by measured surveys (`bathy_coverage` true or NONNA present) versus interpolated, and optionally to validate the modeled depths. Carry the per-area measured-versus-modeled label, not a blanket dataset label.
- GEBCO_2024 stays context only.

## 4. Depth-rendering technique recommendation

### 4.1 Keep the physically grounded depth-driven water

The water2 approach, read the opaque scene depth, reconstruct the seabed world position, and attenuate by water-column thickness with a Beer-Lambert curve, is the correct and current best practice for shore-aware water in a WebGL or Three.js scene. Independent references describe the same construction, transmitted color `sceneColor * exp(-absorption * d)` plus an intrinsic water color, alpha driven by `1 - exp(-absorption * depth)`, and a shoreline foam term `exp(k * dh)` that decays as the water-terrain difference `dh` approaches zero. Sources, Three.js Water Pro color and transparency docs https://docs.threejswaterpro.com/api/color.html , the shader-dev water-ocean reference https://github.com/MiniMax-AI/skills/blob/main/skills/shader-dev/reference/water-ocean.md , and the Meep water-over-terrain shader notes https://meep.company-named.com/docs/world/water/ . The existing foam band in `depthWater.ts` already implements the `dh` near-zero shoreline term.

### 4.2 Upgrade the water absorption to per-channel, proposed to the water2 owner

The current shader uses one scalar column through a two-stop `mix(shallow, deep)`. Real water absorbs red fastest and blue slowest, so deep water shifts blue-green to navy by physics. The Water and Depth Stylist should propose to the water2 owner a per-channel absorption coefficient, a `vec3` extinction (for example R fast, G medium, B slow), replacing or augmenting the single `depthColorScale`. This is a tuning change to `water2/` internals, so it is owned by water2 and requested through them, not edited by this waveset.

### 4.3 Tint the submerged seabed with a perceptually uniform bathymetric ramp plus relief shading

For the seabed itself to read truthfully through the water, the recommended treatment is a perceptually uniform hypsometric depth ramp combined with the existing shaded relief, the standard for honest seafloor cartography.

- Use a perceptually uniform sequential ramp, light at the shallows darkening to deep blue and purple at depth, the cmocean `deep` family, not rainbow or jet. Perceptually uniform ramps represent depth without the false gradients and local-maxima bias of jet, and are colorblind-safe. Sources, Thyng et al. 2016 Oceanography, True Colors of Oceanography https://tos.org/oceanography/article/true-colors-of-oceanography-guidelines-for-effective-and-accurate-colormap , and cmocean https://matplotlib.org/cmocean/ .
- Blend the depth tint with hillshade. Patterson, Mountains Unseen, the Hawaii seafloor relief map, shows that light-to-dark blue depth tints combined with shaded relief read as translucent water filling the lowest areas and accentuate three-dimensionality, with class breaks tightened in the very shallow and very deep flats. Source, https://cartographicperspectives.org/index.php/journal/article/download/cp76-patterson/1295?inline=1 . The realism rig already supplies the sun and lighting that produce this relief.
- Map the ramp over the real modeled depth extent of this scene, the substrate field already exposes `minDepthM` and `maxDepthM` (-349.7 to a positive land max), and `buildSubstrateOverlay` already implements a deep-shore-high three-stop ramp that can be retuned to the cmocean `deep` palette. This is the cleanest existing hook for the seabed tint.

### 4.4 Reconcile sources and avoid the shoreline seam at Y = 0

- The render tiles, the substrate field, and any BlueTopo reference all share the NAVD88 datum, and scene Y = 0 equals NAVD88 0 m through the uniform fit scale. Because the seabed mesh and the substrate field come from one CUDEM geometry, there is no second-source geometry seam to reconcile in the live render. The only seam risk is introduced by rendering a SECOND seabed from a different source.
- Recommendation, do not render BlueTopo or NONNA as competing seabed geometry. Use them as a data and honesty overlay only, a coverage mask and optional validation, so no datum mismatch and no shoreline seam can appear. NONNA in particular is on chart datum, not NAVD88, so rendering it as geometry would create a visible vertical step at the marine border.
- At the waterline, keep the existing foam band, which is the `dh` near-zero shoreline term, and ensure the seabed tint fades into the land material exactly at the modeled 0 m contour so the shoreline does not double-draw. The seabed tint and the water must both measure from the same Y = 0 datum, which they already do.

## 5. Research gate check

The synthesis names concrete, citable techniques (depth-driven Beer-Lambert water with per-channel absorption, perceptually uniform bathymetric tint plus hillshade, foam `dh` shoreline term) and concrete sources with provenance and licence (CUDEM topobathy baked, BlueTopo `bathy_coverage` measured flag, CHS NONNA for the BC side, GEBCO context only). It resolves the key fact, the tileset is topobathy. Research gate PASSED.

# R2 — Bathymetry soundings: authoritative measured sources, soundings vs gridded DEM, datums, ingest

Research agent: R2 (terrain+bathymetry 3D twin spike). Read-only brief. No code edits, no commit.

Study extent (`SAN_JUAN_BOUNDS`): `min_lat 48.40, max_lat 48.70, min_lng -123.25, max_lng -122.75` —
San Juan Islands + Haro Strait + western Rosario Strait, straddling the US/Canada maritime
boundary that runs down the middle of Haro Strait. Primary modeled surface in the pilot is
NOAA NCEI CUDEM 1/9 arc-second topobathy (`wash_bellingham`), NAVD88 m, reprojected to
EPSG:32610. This brief covers REAL measured **sounding / multibeam** sources, how they differ
from that gridded DEM, the datum reconciliation, and concrete ingest.

The central distinction this brief defends: **CUDEM is a modeled, interpolated raster surface.
Soundings and multibeam are the discrete depth MEASUREMENTS that surfaces like CUDEM are built
from.** Showing measured soundings over the modeled surface is the honest way to expose where
the model is observation-backed and where it is interpolation.

---

## 1. Real measured bathymetry sources

### 1.1 NOAA NOS hydrographic surveys (the primary US measured archive)
NCEI stewards the National Ocean Service (NOS) hydrographic survey archive and the NOS
Hydrographic Data Base (NOSHDB): **over 76 million soundings from 6,600+ surveys**, smooth
sheets 1837–1965 plus digital NOAA-vessel surveys since 1965.
- Product page: https://www.ncei.noaa.gov/products/nos-hydrographic-survey
- NOSHDB/HSMDB: https://www.ngdc.noaa.gov/mgg/bathymetry/noshdb/

Two distinct things come out of this archive, and the difference matters for us:
1. **Modern gridded surveys → BAG files.** Bathymetric Attributed Grid (BAG, Open Navigation
   Surface Working Group) is the standard public-release format. A BAG is a **gridded**,
   georeferenced raster holding a depth/elevation band, an **uncertainty band**, and embedded
   XML metadata describing source and provenance. NCEI can also export BAGs to ASCII **XYZ**
   (empty cells dropped). So even "modern multibeam" is delivered as a small high-res grid plus
   uncertainty, not raw pings.
2. **Classic / smooth-sheet surveys → point soundings (XYZ, A93).** Older surveys are served as
   discrete point soundings (`SurveyID, Long, Lat, Depth`, depths in meters, vertical datum
   converted to MLLW where possible) via the NCEI Point Store / NEXT extract.

Surveys confirmed over / adjacent to our bbox (per NCEI survey reports):
- **H08085 — Haro Strait** (project OPR-CS-287-LJ-53, 1953–54, scale 1:10,000). Point soundings,
  vertical datum MLLW, horizontal NAD27, served as XYZ + A93. Directly inside the bbox.
  https://www.ngdc.noaa.gov/nos/H08001-H10000/H08085.html
- **H10766 — Rosario Strait** (Towhead Island to Fern Point, project OPR-N368-PHP-97). Point
  soundings, MLLW, NAD83. Eastern edge of bbox.
  https://www.ngdc.noaa.gov/nos/H10001-H12000/H10766.html
- **H11631 / H11632 — Strait of Georgia, Alden Bank to Matia Island** (project OPR-N161-RA-06,
  Sept–Oct 2006, NOAA Ship RAINIER, scale 1:10,000). **100% multibeam (MBES) + 200% side-scan**
  coverage, modern → BAG + uncertainty. Northern part of the study area (Matia/Sucia/Patos).
  Reports: https://data.ngdc.noaa.gov/platforms/ocean/nos/coast/H10001-H12000/H11632/DR/H11632.pdf
  and https://data.ngdc.noaa.gov/platforms/ocean/nos/coast/H10001-H12000/H11631/DR/H11631.pdf

Note the datum mix already visible here: 1950s surveys are MLLW/NAD27; 2000s surveys are
MLLW/NAD83. None are natively NAVD88. This is exactly the reconciliation problem in §3.

### 1.2 NCEI Bathymetric Data Viewer (the discovery/download front door)
Single interactive viewer over the full NCEI bathymetric archive: multibeam datasets,
single-beam surveys, NOS hydrographic surveys (with BAGs), crowdsourced bathymetry (CSB), and
DEMs. Per-layer filter panels; draw-rectangle or enter-coordinates AOI; direct download (GeoTIFF
is the viewer's only direct-download raster format, BAG/XYZ via the survey-level archive).
Modernized Feb 2026.
- Viewer: https://www.ncei.noaa.gov/maps/bathymetry/
- Announcement: https://www.ncei.noaa.gov/news/explore-sea-floor-ncei-modernized-portal

This is the right tool to enumerate exactly which MBES/single-beam/NOS surveys intersect our
rectangle before downloading.

### 1.3 NOAA ENC / S-57 (and the S-101 successor) — soundings + depth areas as vectors
NOAA Electronic Navigational Charts are vector charts in IHO **S-57** format (`.000` files).
Relevant for us because an ENC carries, as discrete vector features:
- **SOUNDG** — individual sounding points (the cartographic depth numbers on a chart),
- **DEPARE** — depth areas (polygons bounded by isobaths, with min/max depth),
- **DEPCNT** — depth contours (isobaths), plus **OBSTRN/WRECKS/UWTROC** hazards.
ENC depths are referenced to chart datum (**MLLW** in US waters). S-57 is being superseded by
the modern **S-101** product spec (richer, gridded-bathymetry-aware), but S-57 is what is
downloadable and tool-supported today.
- Chart Downloader (S-57 `.000`): https://www.charts.noaa.gov/ENCs/ENCs.shtml
- ENC Direct to GIS (clip/convert to shapefile/gdb, non-navigational): http://www.nauticalcharts.noaa.gov/learn/encdirect/
- ENC InPort record: https://www.fisheries.noaa.gov/inport/item/39976
ENCs are the cleanest way to get **chart-style labeled soundings** for the US side of the bbox
without processing raw survey data.

### 1.4 Canadian side — CHS NONNA (required for the Haro Strait Canadian strip)
The international boundary runs down Haro Strait; the bbox west edge (-123.25) includes Canadian
waters. US federal products (CUDEM/3DEP/NOS) thin or stop at the border, so the Canadian side
needs the **Canadian Hydrographic Service Non-Navigational (NONNA)** product:
- Free, public, non-navigational. Two gridded resolutions: **NONNA-10 (10 m)** and
  **NONNA-100 (100 m)**, plus NONNA Intensity (backscatter).
- Formats: 32-bit **GeoTIFF, ASCII++ (XYZ), CSAR, BAG**; also WMS/WCS/WMTS services.
- **Horizontal datum WGS84 (EPSG:4326); vertical datum Chart Datum (CD)** — a locally derived
  low-water tidal datum, NOT NAVD88 and NOT identical to US MLLW.
- Portal (login to download): https://data.chs-shc.ca/login
- Open Government record: https://open.canada.ca/data/en/dataset/d3881c4c-650d-4070-bf9b-1e00aabf0a1d
- WMS GetCapabilities: https://nonna-geoserver.data.chs-shc.ca/geoserver/wms?request=GetCapabilities

### 1.5 Salish Sea-specific measured compilation — Tombolo / SeaDoc / MLML (best fit for our bbox)
The most relevant high-res **measured** compilation for the exact study area is the San Juan
Islands archipelago multibeam/backscatter/habitat mapping by the Center for Habitat Studies
(Moss Landing Marine Laboratories) with Tombolo Mapping Lab, the SeaDoc Society, Natural
Resources Canada, and CHS. It is purpose-built MBES bathymetry of the San Juan Islands and Haro
Strait and was the primary source behind the NOAA Salish Sea oil-spill assessment maps.
- SeaDoc San Juan maps: https://www.seadocsociety.org/blog/detailed-bathymetry-backscatter-and-habitat-maps-of-the-san-juan-islands-archipelago
- NOAA oil-spill map (documents the MBES sourcing + 25 m contours): https://www.fisheries.noaa.gov/s3/2022-04/oil-spill-assessment-map-central-salish-sea.pdf
- Canadian GSC multibeam catalog (Haro Strait 2000/2002/2003 surveys, group layer "Salish Sea"):
  https://geoappext.nrcan.gc.ca/arcgis/rest/services/GSCA/multibeam_west_e/MapServer/184

### 1.6 Broad-coverage compilations and their provenance
- **GMRT (Global Multi-Resolution Topography)** — continually updated, quality-controlled
  multibeam compilation; v4.4.1 (Jan 2026) holds curated multibeam from 1,621 cruises. Served
  via GridServer web service; also on OpenTopography. Good for context, NOT a substitute for the
  local high-res surveys above. https://www.gmrt.org/ ,
  https://portal.opentopography.org/raster?opentopoID=OTGMRT.112016.4326.1
- **GEBCO_2024** — global 15 arc-second grid (SRTM15+ base augmented by Seabed 2030 regional
  grids). Crucially ships a **TID (Type Identifier) grid** marking each cell's source: e.g.
  10=singlebeam, 11=multibeam, 13=isolated sounding, **14=ENC sounding**, 15=lidar, 40s=predicted
  (satellite-gravity), 70=pre-generated mixed grid. The TID grid is the model for honesty
  labeling we want (see §5). https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2024-grid ,
  https://www.gebco.net/gebco-tid-grid
- **USGS / NOAA Digital Coast topobathy lidar** — measured LAND + nearshore. The **2019 WA DNR
  San Juan County lidar** covers the islands' land surface, NAVD88 (GEOID18), as LAS 1.4 / LAZ on
  the NOAA coastal lidar S3 bucket. https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/laz/geoid18/9495/index.html

---

## 2. Point soundings vs a gridded DEM (CUDEM)

| | Point soundings / MBES pings | Gridded DEM (CUDEM, BAG, NONNA) |
|---|---|---|
| Nature | Irregular, discrete depth **measurements** at specific x,y | Regular raster of **interpolated** depth/elevation per cell |
| Spatial layout | Dense along survey tracklines; gaps between lines / unsurveyed areas | Continuous everywhere in the footprint, including unmeasured cells |
| What it represents | What was actually observed (subject to tide/datum reduction) | A best-estimate **surface**, including interpolation over gaps |
| Uncertainty | Per-sounding (TVU/THU); BAG carries an explicit uncertainty band | Smoothed; per-cell uncertainty usually lost unless a BAG uncertainty band is carried through |
| Cartographic use | Charts print **selected least-depth** soundings (shoal-biased for safety), not all points | Hillshade / hypsometric tint / contour rendering of a smooth surface |
| Pros | Truthful, auditable, shows real coverage and gaps | Easy to mesh, tile, render; seamless; no holes |
| Cons | Holey, irregular, hard to mesh directly; huge point counts | Hides where data is real vs invented; interpolation artifacts; datum blends baked in |

Two points specific to charts: (1) charted soundings are deliberately **shoal-biased** — the
chart shows the shallowest representative depth in an area, not the mean, because the use case is
not running aground; a meshed surface averages instead. (2) ENC `DEPARE`/`DEPCNT` give the
depth-area/contour structure, which is the bridge between scattered soundings and a continuous
tinted surface (this is R3's cartography territory; flagged here for the seam).

Implication: a gridded DEM like CUDEM is a *model fit to* soundings. Overlaying the real
soundings exposes coverage (where tracklines ran) and disagreement (where the grid smoothed a
shoal). That is precisely the "modeled, not measured" honesty story the spike wants.

---

## 3. Vertical datums and reconciliation

The core problem: our datasets live on **different vertical references with opposite sign
conventions**, and they cannot be merged by a single constant offset.

- **CUDEM topobathy → NAVD88, orthometric, meters, elevation-up.** Seafloor is negative,
  land positive. This is the pilot's working datum (preserved through reprojection to EPSG:32610).
- **Soundings / ENC / NOS surveys → MLLW (US chart datum), depth-down.** A "12.3 m" sounding is
  12.3 m *below* MLLW. Sign and reference both differ from NAVD88.
- **CHS NONNA → Chart Datum (CD)**, a locally derived Canadian low-water datum, depth-down,
  ≈ but not equal to US MLLW.
- **MSL / LMSL** is the intermediate tidal surface; **MHW** defines the cartographic shoreline.

In the Salish Sea, NAVD88 and MLLW differ by **roughly a couple of meters and the offset varies
spatially** (it is a function of the local tide range and the geoid), so you cannot subtract a
single number. The authoritative tool is **NOAA VDatum**:
- VDatum home: https://vdatum.noaa.gov/ — VDatumWeb: https://vdatum.noaa.gov/vdatumweb/
- West-coast roadmap (per the VDatum user guide / KGPS paper): ellipsoid → NAD83 → **NAVD88**
  (via NGS hybrid geoid) → **LMSL** (via topography-of-the-sea-surface) → tidal datum (**MLLW**).
  So MLLW↔NAVD88 = the LMSL hop plus the NAVD88↔LMSL hop, both gridded and spatially varying.
  https://www.vdatum.noaa.gov/docs/userguide.html ,
  https://vdatum.noaa.gov/download/publications/2003_hess_USHydro_GPS.pdf

Practical reconciliation recipe to bring measured soundings into the pilot's NAVD88-m / EPSG:32610 frame:
1. Confirm each source's native vertical datum from its metadata (MLLW/CD) and horizontal datum
   (NAD27/NAD83/WGS84). NOS XYZ headers and BAG XML state this.
2. Convert **depth-down MLLW → NAVD88 height** with VDatum over the bbox (input MLLW, target
   NAVD88, point or raster). Flip sign so depth becomes negative elevation (`z_navd88 = -depth +
   (MLLW-to-NAVD88 offset)`, with the offset supplied per-point by VDatum).
3. For CHS NONNA (Chart Datum), VDatum's US grids do not cover Canadian CD; either keep the
   Canadian strip on CD and label it as a separate datum, or apply the local CD↔MLLW relationship
   from a nearby CHS/CO-OPS tidal station — and document the approximation. Do not silently merge.
4. Reproject horizontally (NAD27/NAD83/WGS84 → EPSG:32610). NAD83↔WGS84 ≈ 1–2 m horizontal,
   negligible here; NAD27→NAD83 is larger (tens of m) and must be done for the 1950s surveys.

Honesty constraint: every datum conversion is itself a model. Soundings reduced through VDatum
are "measured depth, model-reduced to NAVD88", which is still meaningfully more measured than the
interpolated CUDEM cell, but the reduction should be recorded in provenance.

---

## 4. Practical ingest

Formats and the tools that read them:

- **BAG** (NOS modern surveys, CHS NONNA): GDAL has a native **BAG driver** — read the depth band
  and the **uncertainty band** as separate raster bands. `gdalinfo survey.bag`; `gdal_translate`
  to GeoTIFF; keep the uncertainty band for honesty shading.
- **S-57 ENC** (`.000`): **GDAL/OGR S-57 driver**. To get individual soundings as points with a
  usable depth attribute, set the driver options:
  ```bash
  export OGR_S57_OPTIONS="SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON"
  ogr2ogr -f GeoJSON soundings.geojson US5WA*.000 SOUNDG
  ogr2ogr -f GeoJSON depare.geojson    US5WA*.000 DEPARE   # depth-area polygons
  ```
  In S-57 one sounding feature holds many points; `SPLIT_MULTIPOINT` explodes them to single
  `s57_point3d` features and `ADD_SOUNDG_DEPTH` writes the depth as an attribute.
  https://gdal.org/en/latest/drivers/vector/s57.html
- **XYZ / ASCII** (NOS Point Store, NONNA ASCII++): plain `SurveyID, Lon, Lat, Depth`. Read with
  GDAL XYZ driver or directly; reproject with `gdalwarp`/`pyproj`.
- **LAS / LAZ** (topobathy/topo lidar, e.g. 2019 WA DNR San Juan): **PDAL**. A pipeline reads the
  LAZ, filters noise (`filters.outlier`), selects a classification (ground=2; topobathy lidar uses
  bathymetric classes 40/41/45 for water-surface/submerged-topo), and either keeps points or grids
  to a raster via `writers.gdal` (output_type `min`/`idw`). https://pdal.org/en/stable/pipeline.html

Rendering choices for our stack (react-three-fiber / three / 3d-tiles-renderer):
- **As point markers (recommended for "measured" layer):** keep soundings as a sparse point set
  (`THREE.Points` / instanced sprites) placed at their EPSG:32610 x,y and NAVD88-reduced z,
  labeled with depth text. Cheap, irregular, and visually distinct from the surface — it *reads*
  as measurement, not model.
- **As a thin gridded overlay:** grid soundings/MBES with `pdal writers.gdal` (IDW or min) or
  `gdal_grid` to a small high-res raster, then a separate semi-transparent tile/mesh draped above
  the CUDEM surface — but this re-introduces interpolation, so prefer points unless contour/tint
  rendering is the goal (defer to R3).
- **Keep measured separate from modeled:** never blend soundings into the CUDEM mesh. Carry them
  as their own scene layer with their own material/provenance, mirroring GEBCO's TID model
  (per-feature/per-cell source tag) so the UI can label and toggle "measured soundings (NOS H#,
  MLLW→NAVD88 via VDatum)" vs "modeled surface (CUDEM 1/9, NAVD88)".

---

## 5. Implications for orcast

**Should we add a measured-soundings layer over the modeled CUDEM surface? Yes — as a distinct,
labeled overlay, not a blend.** It is the single cleanest way to satisfy the spike's "modeled,
not measured" honesty constraint: the CUDEM surface stays the continuous renderable base, and a
sparse point-sounding layer sits above it showing exactly where real measurements exist and where
the surface is interpolation. Render soundings as labeled point markers (depth text), styled
visibly differently from the surface, with a per-source provenance tag and a toggle. Do **not**
mesh soundings into the CUDEM geometry.

**Which exact datasets cover our bbox (48.40–48.70 N, -123.25 to -122.75 W):**
1. **NOS hydrographic surveys (US, point soundings + modern BAG):**
   - `H08085` — Haro Strait, point soundings, MLLW/NAD27 (inside bbox).
   - `H10766` — Rosario Strait (Towhead–Fern Point), point soundings, MLLW/NAD83 (east edge).
   - `H11631` + `H11632` — Strait of Georgia / Alden Bank–Matia Island, 2006 RAINIER, **100% MBES
     → BAG + uncertainty** (north of the islands). Enumerate any others via the NCEI viewer.
2. **NOAA ENC (US, S-57):** the San Juan / Haro Strait harbor- and approach-band ENC cells —
   `SOUNDG` (labeled soundings) + `DEPARE`/`DEPCNT`, MLLW. Easiest chart-style soundings.
3. **CHS NONNA-10 / NONNA-100 (Canada):** required for the Haro Strait Canadian strip west of the
   maritime boundary near -123.1…-123.25; GeoTIFF/XYZ/BAG, WGS84, **Chart Datum** (separate datum).
4. **Tombolo / SeaDoc / MLML San Juan Islands MBES compilation** (+ Canadian GSC Haro Strait
   2000/2002/2003 multibeam): the best dedicated high-res measured surface for the exact area.
5. **2019 WA DNR San Juan County topo lidar** (NAVD88/GEOID18, LAZ): measured LAND relief, already
   in our vertical datum — useful as the measured counterpart on the topo side.
6. **GMRT / GEBCO_2024 (+TID grid):** coarse context / Canadian fallback only; the TID grid is the
   provenance-labeling pattern to copy.

**Honesty labeling (concrete):**
- Tag every rendered element with `source` + `vertical_datum` + `reduction`, e.g.
  `measured · NOS H08085 · MLLW→NAVD88 (VDatum)` vs `modeled · CUDEM 1/9 · NAVD88` vs
  `measured · CHS NONNA-10 · Chart Datum (CD, unreconciled)`.
- Adopt the **GEBCO TID convention** (10 singlebeam / 11 multibeam / 13 isolated sounding /
  14 ENC sounding / 15 lidar / 40s predicted / 70 mixed grid) as the vocabulary for the per-source
  tag so "measured vs interpolated" is explicit and auditable.
- Surface BAG **uncertainty** in the UI where available; flag CHS Canadian-side data as a distinct
  datum (CD ≠ NAVD88) rather than implying a clean merge.
- Continue labeling the CUDEM surface "modeled, not measured"; the soundings layer is what makes
  that label verifiable instead of decorative.

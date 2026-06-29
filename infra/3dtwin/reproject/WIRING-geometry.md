# WIRING-geometry — output geometry contract (agent B → agents C, F)

The single integrated land+seafloor surface produced by agent B. Consume this for the render
tiles (agent C) and the science depth/slope field (agent F). One geometry, no drift.

## Mesh (tiler agent C)

| Field | Value |
|-------|-------|
| S3 URI | `s3://aimez-data/3dtwin/reproject/pilot_mesh.ply` |
| Sidecar | `s3://aimez-data/3dtwin/reproject/pilot_mesh.meta.json` |
| Format | PLY, `binary_little_endian 1.0`; `vertex` (float x,y,z) + `face` (uchar3 + int32×3) |
| Horizontal CRS | **EPSG:32610** (WGS84 / UTM zone 10N) |
| Units | **metres** |
| Vertical datum | **NAVD88 m** (orthometric; Z<0 is below the NAVD88 geoid = seafloor) |
| Vertex frame | **local**: `x = easting_m − origin_easting`, `y = northing_m − origin_northing`, `z = NAVD88 m` (absolute, not offset) |
| `origin_easting` | `485245.194` (EPSG:32610) |
| `origin_northing` | `5377443.419` (EPSG:32610) |
| Vertices / Triangles | 1,229,170 / 2,453,900 |
| Resolution | 10 m grid posting (decimated from ~3.4 m native) |
| Z range | −264.367 m … +273.882 m NAVD88 |
| UTM bbox | E 485245.194–496315.194, N 5377443.419–5388563.419 |
| Triangle winding | CCW seen from +Z (up); per-vertex normals not included (compute at bake) |
| NoData | none in the mesh (NoData cells are simply absent vertices/faces) |

**Georeference back to absolute UTM / lon-lat:** `easting = x + origin_easting`,
`northing = y + origin_northing`, then EPSG:32610 → EPSG:4326. The local origin keeps vertex
magnitudes small (≤ ~11 km) for float32 stability in the renderer; apply the origin as the
tile/scene root transform so 3D Tiles place correctly. **Z is true NAVD88 metres** — do not
add a vertical offset, or the depth science and the render will drift apart.

**Tiler notes for agent C:** the mesh is a single watertight-per-cell grid surface (land +
seafloor continuous, no coastline seam). For OGC 3D Tiles 1.1 (glTF), Y-up vs Z-up is the
tiler's choice — record whichever you pick in `WIRING-tiler.md` so the Wave 2 integrator
applies the matching root transform. To produce a larger or finer chunk, re-run agent B's
pipeline with a wider `PILOT_*` window and/or smaller `MESH_TR` (e.g. native ~3 m), then
`--stride` in `mesh_dem.py` for extra decimation. If you need a stand-in before bake, the
`pilot_utm.tif` raster is the same surface in raster form.

## Source raster (science agent F)

| Field | Value |
|-------|-------|
| S3 URI | `s3://aimez-data/3dtwin/reproject/pilot_utm.tif` |
| Format | GeoTIFF, single band Float32 |
| CRS | EPSG:32610, metres |
| Vertical | NAVD88 m (band value; ocean depth = −value where value<0) |
| Size / res | 1108 × 1113 @ 10 m |
| NoData | −9999 |
| Native-res source | `s3://aimez-data/3dtwin/reproject/pilot_src.tif` (COMPOUND EPSG:5498, 1/9 arc-sec) |

This is the **same** surface as the mesh (one provenance chain). Rasterize depth/slope from
`pilot_utm.tif` (or `pilot_src.tif` for full native resolution). The `BathymetryAdapter`
depth = max(0, −NAVD88_m). Label outputs **"modeled, not measured"**.

## Modeled shoreline

`s3://aimez-data/3dtwin/reproject/pilot_shoreline_0m.gpkg` (and `.geojson`) — the 0 m NAVD88
isoline in EPSG:32610. Use as the modeled land/sea boundary; it is intrinsic to the single
topobathy surface (no two-dataset weld on the primary path; see `RECIPE.md` §6 for the weld
procedure if 3DEP land is later blended).

## Coverage / extent

CUDEM `wash_bellingham` covers 100% of `SAN_JUAN_BOUNDS` (−123.25..−122.75, 48.40..48.70),
including the Haro Strait western edge. GEBCO/CHS fill is only needed if the extent widens
**west of −123.25**. The pilot covers west San Juan Island + Haro Strait (lng −123.20..−123.05,
lat 48.55..48.65).

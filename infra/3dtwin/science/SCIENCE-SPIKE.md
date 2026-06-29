# Science feasibility spike (Agent F, Wave 1)

orcast terrain+bathymetry coastal twin. Goal: prove the SAME integrated topobathy
geometry used for the render can feed the science consumer (the `s_space`
depth/habitat prior) with no second pipeline. Rasterize a depth (plus slope and
aspect) field from the pilot surface, and confirm the existing backend
`BathymetryAdapter` ingests it unchanged.

Everything here is **MODELED, NOT MEASURED**.

## Source used (and the substitution)

Agent B's reprojected integrated surface was NOT available at run time
(`~/3dtwin/reproject/` and `infra/3dtwin/reproject/` did not exist; only
`~/3dtwin/bakeoff_twin/` from Agent C was present). Per the dispatch fallback, I
clipped CUDEM directly and state the substitution here.

Primary source: **NOAA NCEI CUDEM 1/9 arc-second topobathic-topographic DEM**,
the `wash_bellingham` collection (NOT `wash_pugetsound`). This is the same
integrated land+seafloor surface slated to feed the render tiles, so it is one
geometry, not a second pipeline.

Coverage finding (grounded, important): the `wash_pugetsound` CUDEM 1/9 set and
the `puget_sound_13_navd88_2014` regional DEM both stop near lat 48.19 to 48.25,
SOUTH of the study bbox. The `strait_of_juan_de_fuca_13_navd88_2015` DEM covers
lat 48.04 to 48.72 but only lon -125.12 to -123.52, WEST of the bbox. The San
Juan bbox (48.40 to 48.70 N, -123.25 to -122.75) is covered by the
`wash_bellingham` 1/9 tiles, which is the collection used here. The six tiles
that tile the bbox:

```
ncei19_n48x50_w122x75_2024v1.tif   ncei19_n48x75_w122x75_2017v1.tif
ncei19_n48x50_w123x00_2024v1.tif   ncei19_n48x75_w123x00_2017v1.tif
ncei19_n48x50_w123x25_2024v1.tif   ncei19_n48x75_w123x25_2024v1.tif
```

Base URL: `https://coast.noaa.gov/htdata/raster2/elevation/NCEI_ninth_Topobathy_2014_8483/wash_bellingham/`

Native CRS proof (from `gdalinfo` on a tile): horizontal NAD83, vertical NAVD88
height (compound CRS `NAD83 + NAVD88 height`, EPSG:5498), elevation in metres,
`positive up`. Native pixel size 0.0000308642 deg (1/9 arc-second, ~3 m).

## How it was produced

Run on the `aimez-services` EC2 (`i-04a649f91274e9fce`, x86_64 Ubuntu 22.04) with
GDAL as the official **linux/amd64** docker image run natively (NO emulation):
`ghcr.io/osgeo/gdal:ubuntu-small-latest` (GDAL 3.14.0dev). Tiles are read over
`/vsicurl` (no full download). Script: `rasterize_depth.sh`.

1. Read the 6 `/vsicurl` CUDEM tiles directly into one `gdalwarp` mosaic. (A
   `gdalbuildvrt` step was dropped because the 2017 vs 2024 tile vintages carry
   cosmetically different NAD83 compound-CRS strings, which makes `gdalbuildvrt`
   reject two tiles as "heterogeneous projection" and leave a nodata hole over
   the NE bbox. `gdalwarp` mosaics heterogeneous inputs directly, so all six
   tiles contribute.)
2. `gdalwarp` to clip to the bbox and resample to a 0.005 deg grid
   (`-te -123.25 48.40 -122.75 48.70 -tr 0.005 0.005 -tap -r average`), target
   CRS EPSG:4326. NAVD88 m is preserved with no vertical transform (warp only
   touches the horizontal CRS). Output grid is 100 x 60 = 6000 cells.
   0.005 deg (~370 m N-S) is an upgrade from the ETOPO1 source's ~0.0167 deg
   (1 arc-minute) while staying a sane size for a point-list covariate.
3. `gdaldem slope` (`-s 111120` to scale degrees of lat/lng to metres) and
   `gdaldem aspect` produce companion fields on the same grid.
4. `gdal_translate -of XYZ` dumps the depth field to `lon lat value` rows, then
   `build_sample_json.py` builds the adapter JSON.

Derived raster stats (from `gdalinfo -stats`, MODELED):

| field  | min     | max     | mean    | units              |
|--------|---------|---------|---------|--------------------|
| depth  | -349.67 | 679.91  | -26.13  | m NAVD88, pos up   |
| slope  | 0.015   | 21.40   | 2.95    | degrees            |
| aspect | 0.283   | 359.995 | 166.27  | degrees            |

Max 679.9 m falls on Orcas Island (Mount Constitution, ~734 m true; lower here
because of 500 m-scale averaging). Min -349.7 m is the deep Haro Strait channel.

## The exact BathymetryAdapter-compatible format

`sample_san_juan_bathymetry_cudem.json` mirrors `data/geo/san_juan_bathymetry.json`
exactly. `BathymetryAdapter.load()` reads `data["points"]` and each
`{lat, lng, depth_m}`; `summary()` reads `source` / `bounds`. Extra keys
(`provenance`, `modeled_not_measured`) are ignored by the adapter.

```json
{
  "source": "https://coast.noaa.gov/htdata/raster2/elevation/NCEI_ninth_Topobathy_2014_8483/wash_bellingham/ (CUDEM 1/9 arc-sec topobathy)",
  "dataset": "NOAA NCEI CUDEM 1/9 arc-second topobathic-topographic DEM, wash_bellingham; integrated bathymetry+topography; vertical NAVD88 m (EPSG:5703), horizontal NAD83 (EPSG:4269) -> WGS84 (EPSG:4326)",
  "bounds": {"min_lat": 48.4, "max_lat": 48.7, "min_lng": -123.25, "max_lng": -122.75},
  "resolution_deg": 0.005,
  "provenance": "MODELED, NOT MEASURED. ...",
  "modeled_not_measured": true,
  "points": [{"lat": 48.6975, "lng": -123.2475, "depth_m": -349.7}, ...6000 total...]
}
```

### Sign convention

`depth_m` is NEGATIVE below sea level (water), POSITIVE for land, matching the
committed asset. CUDEM elevation is already `positive up` NAVD88 m, so
`depth_m == CUDEM elevation`, with NO sign flip. NAVD88 is treated as the
sea-level reference; it differs from local MSL/MLLW by roughly 1 m here, which is
left unmodeled (acceptable for a depth prior, and labeled modeled).

## Provenance line (verbatim, carried in the JSON `provenance` field)

> MODELED, NOT MEASURED. Depth field rasterized from NOAA NCEI CUDEM 1/9
> arc-second topobathy (wash_bellingham collection), the integrated land+seafloor
> surface that also feeds the 3D render tiles, one geometry, no second pipeline.
> Native vertical datum NAVD88 metres (positive up); NAVD88 treated as the
> sea-level reference for the negative-below-sea-level sign convention (NAVD88
> differs from local MSL/MLLW by ~1 m here, unmodeled). Horizontal NAD83
> (EPSG:4269) warped to WGS84 (EPSG:4326), ~1-2 m shift, negligible at this grid
> spacing. Aggregated to 0.005 deg cells with GDAL -r average; supersedes the
> ETOPO1 1-arc-minute provenance of data/geo/san_juan_bathymetry.json.

## Ingest proof (REAL output, run locally against the repo's BathymetryAdapter)

Command: `python3 infra/3dtwin/science/ingest_proof.py` (pure-python, no AWS).
It imports the real `src/aws_backend/sources/bathymetry.BathymetryAdapter` with
`asset_path=` the sample. No backend code was changed.

```
load()         : 6000 points
  first        : {'lat': 48.6975, 'lng': -123.2475, 'depth_m': -349.7}
  last         : {'lat': 48.4025, 'lng': -122.7525, 'depth_m': -66.4}

depth_at(lat, lng)  [m, NEGATIVE below sea level, POSITIVE land]:
  ( 48.550, -123.200) ->   -260.9  m   # Haro Strait channel (deep water)
  ( 48.450, -122.950) ->    -44.5  m   # San Juan Channel (water)
  ( 48.530, -123.050) ->     41.7  m   # near San Juan Island shore (mixed)
  ( 48.680, -122.850) ->    560.6  m   # Orcas Is. / Mt Constitution upland (land)
  ( 48.500, -123.000) ->    -18.9  m   # bbox interior
  ( 48.400, -122.750) ->    -66.4  m   # bbox SE corner

edge / robustness:
  depth_at(0,0)            -> -66.4   (nearest edge pt, expected)
  depth_at(nan, -123.0)    -> None    (None expected)

summary():
  source        : https://coast.noaa.gov/htdata/raster2/elevation/NCEI_ninth_Topobathy_2014_8483/wash_bellingham/ (CUDEM 1/9 arc-sec topobathy)
  point_count   : 6000
  min_depth_m   : -349.7
  max_depth_m   : 679.9
  bounds        : {'min_lat': 48.4, 'max_lat': 48.7, 'min_lng': -123.25, 'max_lng': -122.75}
```

Result: the existing consumer ingests the modeled CUDEM field with zero code
change. Water reads negative, land reads positive, deep channels are deepest,
non-finite input returns `None`, summary is sane.

## Files

- `rasterize_depth.sh` : GDAL-in-docker CUDEM clip + warp + slope/aspect + XYZ.
- `build_sample_json.py` : XYZ -> adapter JSON (sign convention + provenance).
- `ingest_proof.py` : runs the real `BathymetryAdapter` against the sample.
- `sample_san_juan_bathymetry_cudem.json` : the NEW sample (6000 points). Does
  NOT overwrite the committed `data/geo/san_juan_bathymetry.json`.

## Artifact locations

Derived rasters (small, <25 KB GeoTIFF each; ~300 KB XYZ) live on the EC2 host:
`ubuntu@44.197.243.177:/home/ubuntu/3dtwin/science/out/`
(`depth_sanjuan_cudem.tif`, `slope_sanjuan_cudem.tif`, `aspect_sanjuan_cudem.tif`,
`depth_sanjuan_cudem.xyz`).

S3 staging to `s3://aimez-data/3dtwin/science/` was BLOCKED: the EC2 instance role
`aimez-host-role` is not authorized for `s3:PutObject`/`s3:ListBucket` on
`aimez-data` (AccessDenied). The rasters are small enough to keep on the host;
S3 staging needs an IAM policy fix (see Risks).

## Risks / next steps

1. S3 write permission: `aimez-host-role` cannot write `s3://aimez-data`. Either
   grant `s3:PutObject` on `aimez-data/3dtwin/*` or pick a writable bucket. Low
   urgency here (artifacts are tiny and on the host), but Agents B/C/D staging
   large tilesets will hit the same wall.
2. Datum: NAVD88 used as the sea-level reference; ~1 m offset from MLLW/MSL is
   unmodeled. If the science prior needs a tidal datum, apply NOAA VDatum
   (NAVD88 -> MLLW) before the sign step.
3. Resolution: 0.005 deg via `-r average` mixes land and sea near the shoreline
   into one cell value, which softens the coastline in the prior. Finer grids
   (0.0025 deg) or `-r near`/`-r bilinear` are options if `s_space` wants a
   crisper land/water edge.
4. Source dependency on Agent B: this used a direct CUDEM clip. When Agent B's
   reprojected EPSG:32610 mesh lands, the depth field should be rasterized from
   THAT exact surface (see `WIRING-science.md`) to guarantee render/science use
   the identical geometry rather than two independent clips of the same source.

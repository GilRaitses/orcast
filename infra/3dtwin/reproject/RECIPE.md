# RECIPE — CUDEM topobathy reproject + mesh (orcast 3dtwin, Wave 1, agent B)

Reproducible recipe to turn NOAA NCEI CUDEM 1/9 arc-second integrated topobathy into a
clean triangulated land+seafloor surface in a projected metric CRS for the orcast Salish
Sea twin. Produces the render mesh (tiler agent C) and the source raster the science
consumer (agent F) rasterizes. **One geometry, no drift.** Owns the two footguns
(vertical datum, coastline seam).

All heavy work runs on the `aimez-services` EC2 (x86_64 / Ubuntu 22.04) using the official
**linux/amd64** GDAL docker image natively — NO emulation. Outputs stage to S3.

---

## 0. Host + tooling (verified 2026-06-27)

| Item | Value |
|------|-------|
| Host | `ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177` (`i-04a649f91274e9fce`, c6i.xlarge) |
| Arch | `uname -m` = **x86_64** (native; no Rosetta/QEMU) |
| Docker | 29.1.3 (run via passwordless `sudo docker`; the `ubuntu` user is not in the `docker` group) |
| GDAL image | **`ghcr.io/osgeo/gdal:ubuntu-small-3.8.5`** (pinned; ships python3 + osgeo.gdal + numpy 1.21.5) |
| Remote workdir | `~/3dtwin/reproject/` (created fresh; does NOT touch `~/bakeoff` / `~/borough`) |
| S3 | `s3://aimez-data/3dtwin/reproject/` (account 198456344617, us-east-1) |

The box has **no** `aws` CLI/creds and no host `gdal`. Artifacts are pulled to a creds-bearing
box (local) and uploaded from there; everything else runs in the container.

```bash
# docker helper (from env.sh): mount workdir at /data, native x86_64 GDAL
gdal() { sudo docker run --rm -i -v "$HOME/3dtwin/reproject:/data" -w /data \
         ghcr.io/osgeo/gdal:ubuntu-small-3.8.5 "$@"; }
```

## 1. Run it

```bash
# on the EC2 host
mkdir -p ~/3dtwin/reproject            # scp the scripts here (env.sh, 01_*, 02_*, 03_*, mesh_dem.py)
cd ~/3dtwin/reproject
bash run_pipeline.sh                    # coverage -> clip+reproject+proof -> mesh+shoreline
```

Scripts (this directory):
- `env.sh` — all parameters (bbox, pilot window, tiles, CRS, S3, the `gdal()` helper).
- `01_coverage.sh` — VRT of the 4 covering tiles; full-bbox + Canadian-strip coverage stats.
- `02_clip_reproject.sh` — fetch pilot tile, clip, reproject to EPSG:32610, **prove NAVD88**.
- `mesh_dem.py` — grid → triangle mesh (binary PLY) + sidecar JSON (runs inside the container).
- `03_mesh_shoreline.sh` — mesh + 0 m NAVD88 shoreline contour.
- `run_pipeline.sh` — driver.

---

## 2. Source data + the corner convention (coverage footgun)

NOAA NCEI CUDEM 1/9 arc-second topobathy, public S3 mirror (anonymous HTTPS), collection
`NCEI_ninth_Topobathy_2014_8483`. **Source CRS: COMPOUND `EPSG:5498` = NAD83 (`EPSG:4269`,
horizontal) + NAVD88 height (vertical), metres. NoData −9999. Posting 1/9 arc-sec (~3.4 m).**

Tiles are named by their **NW corner** and span 0.25°: `ncei19_nAAxBB_wCCxDD_YYYYv1.tif`
covers lat `[AA.BB−0.25, AA.BB]`, lng `[−CC.DD, −CC.DD+0.25]`.

**Correction vs the decision record:** the San Juan bbox (lat 48.40–48.70) is **NOT** in
`wash_pugetsound` — that collection's northernmost NW-corner tile is `n48x25` (coverage
≤ lat 48.25). The bbox is covered by the **`wash_bellingham`** collection. The four tiles
that fully tile `SAN_JUAN_BOUNDS`:

| Tile | lat span | lng span | vertical-CRS WKT |
|------|----------|----------|------------------|
| `ncei19_n48x50_w123x25_2024v1.tif` | 48.25–48.50 | −123.25..−123.00 | COMPOUND (EPSG:5498) |
| `ncei19_n48x50_w123x00_2024v1.tif` | 48.25–48.50 | −123.00..−122.75 | COMPOUND (EPSG:5498) |
| `ncei19_n48x75_w123x25_2024v1.tif` | 48.50–48.75 | −123.25..−123.00 | COMPOUND (EPSG:5498) |
| `ncei19_n48x75_w123x00_2017v1.tif` | 48.50–48.75 | −123.00..−122.75 | plain NAD83 (EPSG:4269) |

The 2017 tile is WKT-tagged plain NAD83 (no vertical-CRS component) but its elevation values
are NAVD88 m per the CUDEM spec. `gdalbuildvrt` skips it as "heterogeneous projection" unless
`-allow_projection_difference` is passed (same NAD83 datum + same NAVD88 m values; only the
WKT vertical tag differs). The pilot was meshed from a 2024 COMPOUND-tagged tile so the
datum proof reads a source that explicitly declares NAVD88 height.

Base URL: `https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/NCEI_ninth_Topobathy_2014_8483/wash_bellingham`

---

## 3. Exact commands (what the scripts run)

### 3a. Coverage (full bbox + Canadian-side strip)
```bash
gdal gdalbuildvrt -overwrite -allow_projection_difference bbox_mosaic.vrt \
  /vsicurl/$BASE/ncei19_n48x50_w123x25_2024v1.tif \
  /vsicurl/$BASE/ncei19_n48x50_w123x00_2024v1.tif \
  /vsicurl/$BASE/ncei19_n48x75_w123x25_2024v1.tif \
  /vsicurl/$BASE/ncei19_n48x75_w123x00_2017v1.tif
# full bbox  (W N E S = -123.25 48.70 -122.75 48.40)
gdal gdal_translate -projwin -123.25 48.70 -122.75 48.40 -outsize 1000 0 bbox_mosaic.vrt cov_full.tif
gdal gdalinfo -stats cov_full.tif    # STATISTICS_VALID_PERCENT
```

### 3b. Clip pilot window (source CRS)
```bash
curl -fSL -o $PILOT_TILE $BASE/$PILOT_TILE   # ncei19_n48x75_w123x25_2024v1.tif (191 MB)
# pilot window W N E S = -123.20 48.65 -123.05 48.55
gdal gdal_translate -projwin -123.20 48.65 -123.05 48.55 -a_nodata -9999 $PILOT_TILE pilot_src.tif
```

### 3c. Reproject NAD83 geo → EPSG:32610, NO vertical shift
```bash
gdal gdalwarp -overwrite -t_srs EPSG:32610 -tr 10 10 -r bilinear \
  -srcnodata -9999 -dstnodata -9999 pilot_src.tif pilot_utm.tif
```
A single-band DEM warp changes only the **horizontal** CRS; band Z values pass through
untouched — gdalwarp does not invoke any vertical-datum pipeline (no `+vto`, no geoid grid),
so NAVD88 m is preserved. See §4 proof.

### 3d. Mesh + shoreline
```bash
gdal python3 /data/mesh_dem.py pilot_utm.tif pilot_mesh.ply --stride 1
gdal gdal_contour -fl 0 pilot_utm.tif pilot_shoreline_0m.gpkg     # 0 m NAVD88 = modeled shoreline
```

---

## 4. CRS / datum / units PROOF (measured on the pilot)

| Property | Source `pilot_src.tif` | Reprojected `pilot_utm.tif` |
|----------|------------------------|------------------------------|
| Horizontal CRS | NAD83 geographic (EPSG:4269) | **WGS84 / UTM zone 10N (EPSG:32610)**, metres |
| Vertical | NAVD88 height (COMPOUND EPSG:5498) | **NAVD88 m (unchanged)** |
| Size | 4860 × 3240 @ 1/9 arc-sec | 1108 × 1113 @ 10 m |
| min / mean / max (m) | −264.43 / **−19.639** / 274.26 | −264.37 / **−19.614** / 273.88 |

**Vertical-datum proof:** the means differ by ~0.025 m. An implicit NAVD88→ellipsoid shift in
this region (geoid separation ≈ −22 to −23 m) would have offset every value by that constant;
it did not. Per-point samples (`navd88_proof.txt`):

```
lon        lat      z_src(NAVD88)  z_utm(NAVD88)  delta_m
-123.15    48.58    1.1417         1.2927         -0.151
-123.10    48.60    -12.4971       -12.5633        0.066
-123.18    48.62    3.7927         3.6129          0.180
-123.08    48.56    111.6020       110.6005        1.002
```
Deltas are 10 m-bilinear resampling noise (largest on the steep 112 m hillside), **not** a
constant offset → no vertical datum shift. NAVD88 m preserved end to end.

---

## 5. Coverage findings (measured)

Over `SAN_JUAN_BOUNDS` (−123.25..−122.75, 48.40..48.70), the 4-tile mosaic is:

| Region | STATISTICS_VALID_PERCENT |
|--------|--------------------------|
| Full bbox | **100%** |
| West / Canadian-side strip (−123.25..−123.10, Haro Strait) | **100%** |
| US-side strip (−123.10..−122.75) | **100%** |

CUDEM `wash_bellingham` **fully covers the study bbox**, including the Haro Strait /
Canadian-adjacent western edge down to the bbox west boundary (−123.25). **No GEBCO/CHS fill
is required for `SAN_JUAN_BOUNDS`.** The Canadian-fill caveat only applies if the extent is
later widened **west of −123.25** (Strait of Georgia / Canadian Gulf Islands), where US
federal coverage ends.

Mosaic: 16212 × 16212 @ 1/9 arc-sec, COMPOUND EPSG:5498, min −376 m, max 730 m.

---

## 6. The coastline seam + the weld procedure (footgun 2)

CUDEM is a **single continuous topobathy surface** — land and seafloor share one grid on one
datum, so there is **no two-dataset seam on the primary path**. The modeled shoreline is the
**0 m NAVD88 isoline** (`pilot_shoreline_0m.gpkg`, EPSG:32610, 17 segments for the pilot).

If a higher-fidelity land source (USGS 3DEP 1/3 arc-sec, or 1 m PSLC lidar) is later blended:

1. **Datum-normalise first.** 3DEP is already NAD83/NAVD88 m — reproject horizontally to
   EPSG:32610, no vertical change. Any **MLLW** survey (e.g. a multibeam bathymetry) must be
   transformed **MLLW → NAVD88 m with NOAA VDatum** (Strait of Juan de Fuca / Puget Sound
   grids cover this region) **before** anything else. Never blend across datums.
2. **Define the weld line** = the 0 m NAVD88 contour of the authoritative topobathy
   (`pilot_shoreline_0m.gpkg`) cross-checked against the in-repo coastline
   `data/geo/san_juan_land.geojson` (49 island polygons over the bbox).
3. **Mask by side of the line.** Land source clipped to **above** 0 m (inside the land mask);
   CUDEM bathymetry kept **below** 0 m (outside). `gdalwarp -cutline` per side.
4. **Weld with no gap / no overlap.** Mosaic the two masked rasters onto one grid
   (`gdalbuildvrt` then `gdal_translate`, or `gdalwarp` onto a common `-te/-tr`). Snap both to
   the identical target grid so cells align exactly; feather a 1–2 cell cosine blend across
   the 0 m line so the surface is C0-continuous at the shoreline.
5. **Verify.** Re-extract the 0 m contour from the welded raster; confirm one continuous
   shoreline with no slivers and no double coastline (hillshade + contour overlay).

Label any blended product **"modeled, not measured"**.

---

## 7. Outputs (staged to `s3://aimez-data/3dtwin/reproject/`)

| Key | What |
|-----|------|
| `pilot_mesh.ply` | binary PLY mesh, EPSG:32610 local frame, Z=NAVD88 m (1,229,170 v / 2,453,900 t) |
| `pilot_mesh.meta.json` | CRS / datum / origin / counts / bbox / provenance |
| `pilot_utm.tif` | reprojected raster, EPSG:32610, 10 m, NAVD88 m (science agent F rasterizes this) |
| `pilot_src.tif` | native-res source clip, COMPOUND EPSG:5498 (provenance) |
| `pilot_shoreline_0m.gpkg` / `.geojson` | 0 m NAVD88 modeled shoreline, EPSG:32610 |
| `navd88_proof.txt` | the datum-preservation proof |
| `pilot_color.png` / `pilot_hillshade.png` | visual verification (continuous land+seafloor, no seam) |

#!/usr/bin/env bash
# Agent F (Wave 1, terrain+bathymetry coastal twin) — science feasibility spike.
#
# Rasterize a depth (and slope/aspect) field for the s_space covariate from the
# SAME integrated topobathy surface that feeds the render: NOAA NCEI CUDEM 1/9
# arc-second topobathy (wash_bellingham collection), the tiles that actually
# cover the San Juan bbox. Agent B's reproject output did not exist at run time,
# so this clips CUDEM directly (stated substitution).
#
# Runs GDAL as the official linux/amd64 docker image natively on the x86_64
# aimez EC2 host (NO emulation). Reads tiles over /vsicurl (no full download).
#
# Output convention matches BathymetryAdapter: elevation in metres, NAVD88,
# "positive up" — i.e. NEGATIVE below sea level (water), POSITIVE land. CUDEM is
# already positive-up NAVD88 m, so depth_m == CUDEM elevation, no sign flip.
#
# MODELED, NOT MEASURED.
set -euo pipefail

GDAL_IMAGE="ghcr.io/osgeo/gdal:ubuntu-small-latest"
WORK="${WORK:-$HOME/3dtwin/science}"
OUT="$WORK/out"
LOGS="$WORK/logs"
mkdir -p "$OUT" "$LOGS"

# Study bbox (SAN_JUAN_BOUNDS): xmin ymin xmax ymax
XMIN=-123.25; YMIN=48.40; XMAX=-122.75; YMAX=48.70
# s_space target grid resolution (deg). Upgrade from ETOPO1's ~0.0167 (1 arc-min).
RES="${RES:-0.005}"   # ~0.005 deg ≈ 370 m N-S; 100x60 = 6000 cells over the bbox

BASE="https://coast.noaa.gov/htdata/raster2/elevation/NCEI_ninth_Topobathy_2014_8483/wash_bellingham"
TILES=(
  ncei19_n48x50_w122x75_2024v1.tif
  ncei19_n48x50_w123x00_2024v1.tif
  ncei19_n48x50_w123x25_2024v1.tif
  ncei19_n48x75_w122x75_2017v1.tif
  ncei19_n48x75_w123x00_2017v1.tif
  ncei19_n48x75_w123x25_2024v1.tif
)

VRTSRC=""
for t in "${TILES[@]}"; do VRTSRC="$VRTSRC /vsicurl/$BASE/$t"; done

drun() { sudo docker run --rm --platform linux/amd64 \
  -e GDAL_HTTP_MAX_RETRY=5 -e GDAL_HTTP_RETRY_DELAY=2 \
  -e CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif \
  -v "$WORK:/work" -w /work "$GDAL_IMAGE" "$@"; }

echo "[1/6] Source CRS / datum proof (one native tile)"
drun gdalinfo "/vsicurl/$BASE/${TILES[0]}" 2>&1 | tee "$LOGS/02_srcinfo.log" | grep -E "Coordinate System|ID\[|VERT|NAVD|Pixel Size|Band 1|Origin" | head -40 || true

# NOTE: gdalbuildvrt rejects these tiles as "heterogeneous projection" because the
# 2017 vs 2024 vintages carry cosmetically different NAD83 compound-CRS strings.
# gdalwarp mosaics heterogeneous inputs directly (reprojecting each), so we feed
# all 6 /vsicurl tiles straight into one warp — no VRT, no dropped tiles, no hole.
echo "[2/6] (skipped VRT; warping 6 tiles directly to avoid projection-equality drop)"

echo "[3/6] Clip+resample to bbox at ${RES} deg, EPSG:4326, -r average (depth field)"
drun gdalwarp -overwrite \
  -t_srs EPSG:4326 \
  -te $XMIN $YMIN $XMAX $YMAX \
  -tr $RES $RES -tap \
  -r average \
  -srcnodata -9999 -dstnodata -9999 \
  -of GTiff -co COMPRESS=DEFLATE \
  $VRTSRC /work/out/depth_sanjuan_cudem.tif 2>&1 | tee "$LOGS/03_warp.log"

echo "[4/6] Slope + aspect companion fields (modeled, same grid)"
drun gdaldem slope  -s 111120 /work/out/depth_sanjuan_cudem.tif /work/out/slope_sanjuan_cudem.tif  2>&1 | tee "$LOGS/04_slope.log"
drun gdaldem aspect          /work/out/depth_sanjuan_cudem.tif /work/out/aspect_sanjuan_cudem.tif 2>&1 | tee "$LOGS/05_aspect.log"

echo "[5/6] Stats + XYZ dump of the depth field"
drun gdalinfo -stats /work/out/depth_sanjuan_cudem.tif 2>&1 | tee "$LOGS/06_depthinfo.log" | grep -E "Size is|Pixel Size|Minimum|Maximum|Mean|NoData|Upper Left|Lower Right" | head
drun gdal_translate -of XYZ /work/out/depth_sanjuan_cudem.tif /work/out/depth_sanjuan_cudem.xyz 2>&1 | tee "$LOGS/07_xyz.log"

echo "[6/6] done. Outputs in $OUT"
ls -la "$OUT"

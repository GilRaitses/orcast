#!/usr/bin/env bash
# run_pipeline.sh — build, optimize, assemble, and validate the orcast 3dtwin pilot tileset.
#
# Runs ENTIRELY on the aimez-services EC2 (x86_64 Ubuntu 22.04) using official
# linux/amd64 docker images natively (NO emulation):
#   - ghcr.io/osgeo/gdal:ubuntu-small-latest   (fetch/clip/reproject DEM + python meshing)
#   - node:20-bookworm                          (gltfpack + 3d-tiles-tools + 3d-tiles-validator)
#
# Inputs (env-overridable):
#   SRC = integrated topobathy DEM source. Default: GMRT GridServer for SAN_JUAN_BOUNDS.
#         (Substitute: agent B's CUDEM/NAVD88 mesh was not ready and CUDEM wash_pugetsound
#          only reaches 48.25N, below the 48.40-48.70N study bbox. GMRT is the charter's
#          named cross-border fallback family (GEBCO-derived blend). Vertical datum ~MSL,
#          NOT NAVD88. Modeled, not measured.)
#
# Output: ~/3dtwin/pilot/out/{tileset.json, pilot.glb, validation_report.json}
#
# Usage (on the EC2 box):  bash run_pipeline.sh
set -euo pipefail

ROOT="${ROOT:-$HOME/3dtwin/pilot}"
WORK="$ROOT/work"
OUT="$ROOT/out"
GDAL="ghcr.io/osgeo/gdal:ubuntu-small-latest"
NODE="node:20-bookworm"
DK="sudo docker run --rm --platform linux/amd64"

# Study extent (SAN_JUAN_BOUNDS) and target grid.
MINLON=-123.25; MAXLON=-122.75; MINLAT=48.40; MAXLAT=48.70
TR="${TR:-80}"          # output pixel size in meters (UTM 10N)
TSRS="EPSG:32610"       # UTM zone 10N, meters

mkdir -p "$WORK" "$OUT"
cd "$WORK"

echo "== 1. fetch integrated topobathy DEM (GMRT, EPSG:4326) =="
if [ ! -f dem_geo.tif ]; then
  curl -sL --max-time 240 -o dem_geo.tif \
    "https://www.gmrt.org/services/GridServer?minlongitude=${MINLON}&maxlongitude=${MAXLON}&minlatitude=${MINLAT}&maxlatitude=${MAXLAT}&format=geotiff&resolution=high&layer=topo"
fi
ls -l dem_geo.tif

echo "== 2. reproject to ${TSRS} @ ${TR} m (no implicit vertical shift) =="
$DK -v "$WORK":/data "$GDAL" gdalwarp -overwrite -t_srs "$TSRS" \
  -tr "$TR" "$TR" -r bilinear -of GTiff /data/dem_geo.tif /data/dem_utm.tif

echo "== 3. mesh DEM -> Y-up glTF (local meters frame) =="
$DK -v "$WORK":/data "$GDAL" python3 /data/dem_to_glb.py /data/dem_utm.tif /data/pilot_raw.glb

echo "== 4. gltfpack: meshopt compression + quantization =="
$DK -v "$ROOT":/pilot -w /pilot/work "$NODE" \
  ./node_modules/.bin/gltfpack -i pilot_raw.glb -o /pilot/out/pilot.glb -cc

echo "== 5. assemble OGC 3D Tiles 1.1 tileset.json =="
$DK -v "$ROOT":/pilot "$GDAL" python3 /pilot/work/make_tileset.py \
  /pilot/work/pilot_raw.glb.bounds.json pilot.glb /pilot/out/tileset.json

echo "== 6. validate with CesiumGS 3d-tiles-validator =="
$DK -v "$ROOT":/pilot -w /pilot/out "$NODE" \
  npx --prefix /pilot/work 3d-tiles-validator -t tileset.json -r validation_report.json
echo "--- validation_report.json ---"
cat "$OUT/validation_report.json"

echo "== sizes =="
ls -l "$WORK/pilot_raw.glb" "$OUT/pilot.glb" "$OUT/tileset.json"

#!/usr/bin/env bash
# Step 4-5: mesh the reprojected integrated surface, and extract the 0 m NAVD88
# contour as the modeled shoreline (in EPSG:32610). Run on EC2: `bash 03_mesh_shoreline.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
cd "${WORKDIR}"

echo "=== Mesh pilot_utm.tif -> pilot_mesh.ply (local UTM frame, NAVD88 m Z) ==="
gdal python3 /data/mesh_dem.py pilot_utm.tif pilot_mesh.ply --stride 1
echo
ls -lh pilot_mesh.ply pilot_mesh.meta.json

echo
echo "=== Modeled shoreline: 0 m NAVD88 contour from the reprojected raster ==="
# CUDEM is a single continuous topobathy surface, so the 0 m NAVD88 isoline IS the
# modeled shoreline (no two-dataset weld required on the primary path).
gdal rm -f pilot_shoreline_0m.gpkg 2>/dev/null || true
gdal gdal_contour -q -fl 0 -amax elev_max -amin elev_min \
  pilot_utm.tif pilot_shoreline_0m.gpkg
gdal ogrinfo -so -al pilot_shoreline_0m.gpkg 2>/dev/null | grep -iE "Feature Count|Geometry|EPSG|32610|Extent" | head -10
# Also emit GeoJSON (EPSG:32610) for easy inspection by downstream agents.
gdal rm -f pilot_shoreline_0m.geojson 2>/dev/null || true
gdal ogr2ogr -f GeoJSON pilot_shoreline_0m.geojson pilot_shoreline_0m.gpkg 2>/dev/null || true
ls -lh pilot_shoreline_0m.gpkg 2>/dev/null || true

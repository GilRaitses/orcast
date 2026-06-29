#!/usr/bin/env bash
# Step 1: confirm CUDEM tile coverage over the full study bbox and flag any
# Canadian-side (Haro Strait) nodata gap. Reads tiles remotely via /vsicurl.
# Run on the EC2 host: `bash 01_coverage.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

echo "=== Building remote VRT of the 4 wash_bellingham tiles covering the bbox ==="
# -allow_projection_difference: the 2017 tile is WKT-tagged plain NAD83 (EPSG:4269)
# while the 2024 tiles are COMPOUND NAD83 + NAVD88 height (EPSG:5498). Same NAD83 datum
# and same NAVD88 m elevation values; only the vertical-CRS WKT tag differs, so it is
# safe to mosaic them together.
VRT_LIST=()
for t in "${CUDEM_TILES[@]}"; do
  VRT_LIST+=("/vsicurl/${CUDEM_BASE}/${t}")
done
gdal gdalbuildvrt -overwrite -allow_projection_difference bbox_mosaic.vrt "${VRT_LIST[@]}"

echo
echo "=== Mosaic CRS / extent ==="
gdal gdalinfo bbox_mosaic.vrt | grep -iE "Size is|Pixel Size|Corner|Upper|Lower|Center|EPSG|COMPOUND|VERT|NoData" | head -40

echo
echo "=== Full-bbox valid-pixel coverage (approx stats) ==="
gdal gdal_translate -q -projwin "${BBOX_W}" "${BBOX_N}" "${BBOX_E}" "${BBOX_S}" \
  -outsize 1000 0 bbox_mosaic.vrt cov_full.tif
gdal gdalinfo -stats cov_full.tif | grep -iE "STATISTICS_VALID_PERCENT|STATISTICS_MIN|STATISTICS_MAX|STATISTICS_MEAN|NoData"

echo
echo "=== Canadian-side strip (lng ${BBOX_W} .. -123.10), Haro Strait ==="
gdal gdal_translate -q -projwin "${BBOX_W}" "${BBOX_N}" -123.10 "${BBOX_S}" \
  -outsize 400 0 bbox_mosaic.vrt cov_west.tif
gdal gdalinfo -stats cov_west.tif | grep -iE "STATISTICS_VALID_PERCENT|STATISTICS_MIN|STATISTICS_MAX"

echo
echo "=== US-side strip (lng -123.10 .. ${BBOX_E}) for comparison ==="
gdal gdal_translate -q -projwin -123.10 "${BBOX_N}" "${BBOX_E}" "${BBOX_S}" \
  -outsize 600 0 bbox_mosaic.vrt cov_east.tif
gdal gdalinfo -stats cov_east.tif | grep -iE "STATISTICS_VALID_PERCENT|STATISTICS_MIN|STATISTICS_MAX"

echo
echo "Coverage check complete. VALID_PERCENT < 100 on the west strip indicates the"
echo "Canadian-side gap to backfill with GEBCO 2024 / CHS in a later wave."

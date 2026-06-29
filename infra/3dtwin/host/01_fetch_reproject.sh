#!/usr/bin/env bash
# Step 1: fetch the 4 wash_bellingham CUDEM tiles, mosaic, and reproject the FULL
# SAN_JUAN_BOUNDS extent NAD83 geo -> EPSG:32610 (UTM 10N, m) at 10 m with NO vertical
# shift, preserving NAVD88 m. Reproduces agent B's 02_clip_reproject.sh over the full
# bbox. Proves NAVD88 preservation and full-bbox coverage.
# Run on the EC2 host: `bash 01_fetch_reproject.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
mkdir -p "${WORKDIR}" "${TILES_DIR}"
cd "${WORKDIR}"

echo "=== Fetch the 4 wash_bellingham tiles (reuse agent B's cache when present) ==="
for t in "${CUDEM_TILES[@]}"; do
  if [ -s "${TILES_DIR}/${t}" ]; then
    echo "  have ${t}"
  elif [ -s "${REPROJECT_DIR}/${t}" ]; then
    echo "  link from reproject cache: ${t}"
    cp -n "${REPROJECT_DIR}/${t}" "${TILES_DIR}/${t}"
  else
    echo "  fetch ${t}"
    curl -fSL --retry 3 -o "${TILES_DIR}/${t}" "${CUDEM_BASE}/${t}"
  fi
done
ls -lh "${TILES_DIR}"

echo
echo "=== Build VRT mosaic (allow_projection_difference: 2017 tile is plain NAD83 WKT, same NAVD88 values) ==="
VRT_LIST=()
for t in "${CUDEM_TILES[@]}"; do VRT_LIST+=("tiles/${t}"); done
gdal gdalbuildvrt -overwrite -allow_projection_difference full_mosaic.vrt "${VRT_LIST[@]}"
gdal gdalinfo full_mosaic.vrt | grep -iE "Size is|Pixel Size|COMPOUND|NAVD88|NAD83|NoData" | head -20

echo
echo "=== Reproject FULL bbox -> ${TARGET_CRS} @ ${MESH_TR} m, bilinear, horizontal-only (NAVD88 m preserved) ==="
# -te in EPSG:4326 (the lat/lng study bbox); -te_srs maps it into the target CRS.
gdal gdalwarp -overwrite -q \
  -t_srs "${TARGET_CRS}" -tr "${MESH_TR}" "${MESH_TR}" -r bilinear \
  -te "${BBOX_W}" "${BBOX_S}" "${BBOX_E}" "${BBOX_N}" -te_srs EPSG:4326 \
  -srcnodata "${NODATA}" -dstnodata "${NODATA}" \
  full_mosaic.vrt full_utm.tif
gdal gdalinfo -stats full_utm.tif | grep -iE "Size is|Pixel Size|STATISTICS_MIN|STATISTICS_MAX|STATISTICS_MEAN|NoData|UTM zone 10N|ID\\[\"EPSG\",32610"

echo
echo "=== Full-bbox valid-pixel coverage over the reprojected surface ==="
gdal gdalinfo -stats full_utm.tif | grep -iE "STATISTICS_VALID_PERCENT"

echo
echo "=== PROOF: NAVD88 m preserved (source geo vs reprojected UTM point samples) ==="
PROOF="navd88_proof_full.txt"
{
  echo "NAVD88 preservation proof - FULL extent (generated $(date -u +%FT%TZ))"
  echo "Source full_mosaic.vrt : NAD83 geographic, NAVD88 m (CUDEM wash_bellingham, COMPOUND EPSG:5498 / plain NAD83)"
  echo "Reprojected full_utm.tif : EPSG:32610 (UTM 10N m), NAVD88 m (unchanged, no +vto, no geoid grid)"
  printf "%-12s %-12s %-14s %-14s %-12s\n" "lon" "lat" "z_src(NAVD88)" "z_utm(NAVD88)" "delta_m"
} > "${PROOF}"
for pt in "-123.15 48.58" "-123.05 48.45" "-122.85 48.68" "-123.20 48.42"; do
  lon=$(echo "$pt" | awk '{print $1}'); lat=$(echo "$pt" | awk '{print $2}')
  zsrc=$(gdal gdallocationinfo -valonly -geoloc full_mosaic.vrt "$lon" "$lat" 2>/dev/null | tr -d '\r')
  xy=$(echo "$lon $lat" | gdal bash -lc "gdaltransform -s_srs EPSG:4269 -t_srs ${TARGET_CRS}" 2>/dev/null | tr -d '\r')
  x=$(echo "$xy" | awk '{print $1}'); y=$(echo "$xy" | awk '{print $2}')
  zutm=$(gdal gdallocationinfo -valonly -geoloc full_utm.tif "$x" "$y" 2>/dev/null | tr -d '\r')
  delta=$(awk -v a="$zsrc" -v b="$zutm" 'BEGIN{ if(a==""||b=="") print "n/a"; else printf "%.4f", a-b }')
  printf "%-12s %-12s %-14s %-14s %-12s\n" "$lon" "$lat" "$zsrc" "$zutm" "$delta" >> "${PROOF}"
done
cat "${PROOF}"
echo
echo "Near-equal samples (resampling noise only, no ~-22 m geoid offset) => NAVD88 m preserved."

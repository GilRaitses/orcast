#!/usr/bin/env bash
# Step 2-3: fetch the pilot CUDEM tile, clip the coastal pilot window in the source
# CRS, reproject NAD83 geographic -> EPSG:32610 (UTM 10N, m) with NO vertical shift,
# and PROVE NAVD88 m is preserved (stats + point samples before/after).
# Run on the EC2 host: `bash 02_clip_reproject.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

echo "=== Fetch pilot tile (${PILOT_TILE}) ==="
if [ ! -s "${PILOT_TILE}" ]; then
  curl -fSL --retry 3 -o "${PILOT_TILE}" "${CUDEM_BASE}/${PILOT_TILE}"
fi
ls -lh "${PILOT_TILE}"

echo
echo "=== Source tile CRS / datum (must be COMPOUND NAD83 + NAVD88 height) ==="
gdal gdalinfo "${PILOT_TILE}" | grep -iE "COMPOUND|NAVD88|NAD83|Pixel Size|NoData|EPSG\",5498" | head -20

echo
echo "=== Clip pilot window in source CRS (W N E S = ${PILOT_W} ${PILOT_N} ${PILOT_E} ${PILOT_S}) ==="
gdal gdal_translate -q -projwin "${PILOT_W}" "${PILOT_N}" "${PILOT_E}" "${PILOT_S}" \
  -a_nodata "${NODATA}" "${PILOT_TILE}" pilot_src.tif
gdal gdalinfo -stats pilot_src.tif | grep -iE "Size is|Pixel Size|STATISTICS_MIN|STATISTICS_MAX|STATISTICS_MEAN|NoData"

echo
echo "=== Reproject -> ${TARGET_CRS} @ ${MESH_TR} m, bilinear, horizontal-only (no +vto) ==="
# A single-band DEM warp changes only the HORIZONTAL CRS; band Z values are passed
# through untouched (no vertical datum pipeline is invoked). NAVD88 m is preserved.
gdal gdalwarp -overwrite -q \
  -t_srs "${TARGET_CRS}" -tr "${MESH_TR}" "${MESH_TR}" -r bilinear \
  -srcnodata "${NODATA}" -dstnodata "${NODATA}" \
  pilot_src.tif pilot_utm.tif
gdal gdalinfo -stats pilot_utm.tif | grep -iE "Size is|Pixel Size|STATISTICS_MIN|STATISTICS_MAX|STATISTICS_MEAN|NoData|ID\\[\"EPSG\",32610|UTM zone 10N"

echo
echo "=== PROOF: NAVD88 m preserved (point samples, source geo vs reprojected UTM) ==="
PROOF="navd88_proof.txt"
{
  echo "NAVD88 preservation proof  (generated $(date -u +%FT%TZ))"
  echo "Source pilot_src.tif : horizontal NAD83 geographic, vertical NAVD88 m (COMPOUND EPSG:5498)"
  echo "Reprojected pilot_utm.tif : horizontal EPSG:32610 (UTM 10N m), vertical NAVD88 m (unchanged)"
  echo "If an implicit vertical datum shift had occurred (e.g. NAVD88->ellipsoid), the geoid"
  echo "separation in this region (~ -22 to -23 m) would offset every sample. Equal values prove none."
  echo
  printf "%-12s %-12s %-14s %-14s %-12s\n" "lon" "lat" "z_src(NAVD88)" "z_utm(NAVD88)" "delta_m"
} > "${PROOF}"

for pt in "-123.15 48.58" "-123.10 48.60" "-123.18 48.62" "-123.08 48.56"; do
  lon=$(echo "$pt" | awk '{print $1}')
  lat=$(echo "$pt" | awk '{print $2}')
  zsrc=$(gdal gdallocationinfo -valonly -geoloc pilot_src.tif "$lon" "$lat" 2>/dev/null | tr -d '\r')
  xy=$(echo "$lon $lat" | gdal bash -lc "gdaltransform -s_srs EPSG:4269 -t_srs ${TARGET_CRS}" 2>/dev/null | tr -d '\r')
  x=$(echo "$xy" | awk '{print $1}')
  y=$(echo "$xy" | awk '{print $2}')
  zutm=$(gdal gdallocationinfo -valonly -geoloc pilot_utm.tif "$x" "$y" 2>/dev/null | tr -d '\r')
  delta=$(awk -v a="$zsrc" -v b="$zutm" 'BEGIN{ if(a==""||b=="") print "n/a"; else printf "%.4f", a-b }')
  printf "%-12s %-12s %-14s %-14s %-12s\n" "$lon" "$lat" "$zsrc" "$zutm" "$delta" >> "${PROOF}"
done
cat "${PROOF}"
echo
echo "Compare STATISTICS_MEAN of pilot_src vs pilot_utm above: near-equal => no datum shift."

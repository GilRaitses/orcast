#!/usr/bin/env bash
# Stage the pilot chunk used by the bake-off onto the EC2 conversion host.
#
# PRIMARY PATH (what the recorded results use): agent B's reprojected chunk.
#   B's WIRING-geometry output is staged at s3://aimez-data/3dtwin/reproject/.
#   We use B's pilot_utm.tif: EPSG:32610 (UTM 10N, m), NAVD88 m, 10 m posting,
#   1108x1113, San Juan Islands (CUDEM 1/9 wash_bellingham). The EC2 instance
#   role (aimez-host-role) lacks s3:GetObject on aimez-data, so the file is
#   pulled with credentialed AWS access on the operator workstation and pushed
#   to the box over scp.
#
# STAND-IN PATH (only if B's output is absent): clip a real CUDEM 1/9 topobathy
#   tile directly with /vsicurl + gdal_translate, then reproject to EPSG:32610.
#   This was the agent-C stand-in used before B's output appeared; it targets a
#   Whidbey/Saratoga Passage tile because the exact San Juan bbox is not in the
#   wash_pugetsound collection.
#
# Env: EC2 (host), KEY (ssh key), GDAL (gdal image tag).
set -euo pipefail
EC2="${EC2:-ubuntu@44.197.243.177}"
KEY="${KEY:-$HOME/.ssh/pax-ec2-key.pem}"
RWD="${RWD:-/home/ubuntu/3dtwin/bakeoff_twin}"
GDAL="${GDAL:-ghcr.io/osgeo/gdal:ubuntu-small-3.8.5}"
SSH="ssh -i $KEY -o StrictHostKeyChecking=no $EC2"

mode="${1:-b}"   # 'b' = use agent B's chunk (default); 'standin' = clip CUDEM

$SSH "mkdir -p $RWD/in $RWD/logs"

if [ "$mode" = "b" ]; then
  echo "[prep] pulling agent B pilot_utm.tif via local creds -> scp to EC2"
  tmp="$(mktemp -d)"
  aws s3 cp s3://aimez-data/3dtwin/reproject/pilot_utm.tif "$tmp/B_pilot_utm.tif" --quiet
  scp -i "$KEY" -o StrictHostKeyChecking=no "$tmp/B_pilot_utm.tif" "$EC2:$RWD/in/B_pilot_utm.tif"
  echo "[prep] B chunk staged as $RWD/in/B_pilot_utm.tif"
  $SSH "sudo docker run --rm -v $RWD:/data $GDAL gdalinfo -mm /data/in/B_pilot_utm.tif | grep -iE 'Size is|Pixel Size|Computed Min|EPSG\",32610'"
else
  echo "[prep] STAND-IN: clipping CUDEM 1/9 topobathy via /vsicurl"
  TIF='/vsicurl/https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/NCEI_ninth_Topobathy_2014_8483/wash_pugetsound/ncei19_n48x25_w122x75_2024v1.tif'
  # window B: deep water + real land relief, straddles 0 m shoreline
  $SSH "sudo docker run --rm -v $RWD:/data -e CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif $GDAL \
        gdal_translate -q -projwin -122.62 48.10 -122.59 48.07 /data_in.tmp '$TIF' /data/in/pilot_geo.tif || \
        sudo docker run --rm -v $RWD:/data -e CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif $GDAL \
        gdal_translate -q -projwin -122.62 48.10 -122.59 48.07 '$TIF' /data/in/pilot_geo.tif"
  $SSH "sudo docker run --rm -v $RWD:/data $GDAL gdalwarp -q -t_srs EPSG:32610 -r bilinear -dstnodata -9999 -overwrite /data/in/pilot_geo.tif /data/in/B_pilot_utm.tif"
  echo "[prep] STAND-IN chunk staged as $RWD/in/B_pilot_utm.tif (clearly NOT agent B's output)"
fi

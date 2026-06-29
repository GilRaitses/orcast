#!/usr/bin/env bash
# Candidate 2: quantized-mesh terrain tiles via cesium-terrain-builder (CTB).
#
# CTB tiles the global-geodetic (EPSG:4326) TMS pyramid, so the projected UTM
# pilot is warped to EPSG:4326 first (note: this re-introduces an ellipsoidal /
# global tiling frame, the opposite of the local UTM engineering frame the twin
# wants -- that trade-off is the whole point of the bake-off).
#
# Produces .terrain (quantized-mesh-1.0) tiles with oct-encoded normals plus a
# layer.json, then measures tile counts per zoom and total bytes.
set -euo pipefail
EC2="${EC2:-ubuntu@44.197.243.177}"
KEY="${KEY:-$HOME/.ssh/pax-ec2-key.pem}"
RWD="${RWD:-/home/ubuntu/3dtwin/bakeoff_twin}"
GDAL="${GDAL:-ghcr.io/osgeo/gdal:ubuntu-small-3.8.5}"
CTB="${CTB:-tumgis/ctb-quantized-mesh}"
IN="${IN:-/data/in/B_pilot_utm.tif}"
OUT="${OUT:-/data/qmesh_B}"
SSH="ssh -i $KEY -o StrictHostKeyChecking=no $EC2"

$SSH "set -e
  sudo docker run --rm -v $RWD:/data $GDAL gdalwarp -q -t_srs EPSG:4326 -r bilinear \
       -dstnodata -9999 -overwrite $IN /data/in/B_pilot_4326.tif
  rm -rf $OUT && mkdir -p $OUT
  # quantized-mesh tiles (-f Mesh), Cesium-friendly roots (-C), oct normals (-N)
  sudo docker run --rm -v $RWD:/data $CTB ctb-tile -f Mesh -C -N -o ${OUT#/data/../} /data/in/B_pilot_4326.tif
  # metadata
  sudo docker run --rm -v $RWD:/data $CTB ctb-tile -f Mesh -l -o ${OUT#/data/../} /data/in/B_pilot_4326.tif
  HOST_OUT=$RWD/\$(basename $OUT)
  echo '--- quantized-mesh measured ---'
  echo -n 'total .terrain tiles: '; find \$HOST_OUT -name '*.terrain' | wc -l
  echo -n 'tiles per zoom: '; for z in \$(ls \$HOST_OUT | grep -E '^[0-9]+\$' | sort -n); do echo -n \"z\$z=\$(find \$HOST_OUT/\$z -name '*.terrain'|wc -l) \"; done; echo
  echo -n 'total bytes: '; du -sb \$HOST_OUT | cut -f1
  maxz=\$(ls \$HOST_OUT | grep -E '^[0-9]+\$' | sort -n | tail -1)
  echo -n \"max-zoom z\$maxz bytes: \"; du -sb \$HOST_OUT/\$maxz | cut -f1
"

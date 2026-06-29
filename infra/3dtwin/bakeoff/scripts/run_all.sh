#!/usr/bin/env bash
# End-to-end bake-off on the aimez-services EC2 (x86_64, native amd64 docker).
# Reproduces every measured number in ../BAKEOFF.md.
#
# Prereqs (one-time on the box): build the python image
#   ssh ... 'cd ~/3dtwin/bakeoff_twin && sudo docker build -f Dockerfile.py -t bakeoff-py .'
# and pull: ghcr.io/osgeo/gdal:ubuntu-small-3.8.5, node:20-slim, tumgis/ctb-quantized-mesh.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
EC2="${EC2:-ubuntu@44.197.243.177}"
KEY="${KEY:-$HOME/.ssh/pax-ec2-key.pem}"
RWD="${RWD:-/home/ubuntu/3dtwin/bakeoff_twin}"

# push scripts the box runs
scp -i "$KEY" -o StrictHostKeyChecking=no \
    "$here/10_mesh_to_3dtiles.py" "$here/40_fidelity.py" "$here/Dockerfile.py" \
    "$EC2:$RWD/"

bash "$here/00_prep_pilot.sh" "${1:-b}"      # 'b' (agent B chunk) | 'standin'
bash "$here/15_mesh_compress.sh"             # Candidate 1
bash "$here/20_qmesh_ctb.sh"                 # Candidate 2

# fidelity (RMSE + hillshade/color PNGs) on the same chunk
ssh -i "$KEY" -o StrictHostKeyChecking=no "$EC2" "
  sudo docker run --rm -v $RWD:/data -e IN_TIF=/data/in/B_pilot_utm.tif \
       -e OUT_RECON=/data/logs/lod_recon_B.tif -e TARGET_VERTS=61642 bakeoff-py \
       python /data/40_fidelity.py
  printf '273 247 252 180\n10 90 150 70\n0 60 120 60\n-0.01 20 90 150\n-264 5 20 70\nnv 0 0 0\n' > $RWD/logs/ramp_B.txt
  sudo docker run --rm -v $RWD:/data ghcr.io/osgeo/gdal:ubuntu-small-3.8.5 bash -lc '
    gdaldem hillshade -q -of GTiff /data/in/B_pilot_utm.tif /data/logs/hs_source_B.tif &&
    gdaldem hillshade -q -of GTiff /data/logs/lod_recon_B.tif /data/logs/hs_lod_B.tif &&
    gdaldem color-relief -q /data/in/B_pilot_utm.tif /data/logs/ramp_B.txt /data/logs/color_B.tif &&
    for f in hs_source_B hs_lod_B color_B; do gdal_translate -q -of PNG -ot Byte /data/logs/\$f.tif /data/logs/\$f.png; done'
"
bash "$here/30_stage_s3.sh"
echo "DONE"

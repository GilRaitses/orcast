#!/usr/bin/env bash
# Candidate 1 finishing step: build the mesh glTF tile (10_mesh_to_3dtiles.py),
# then produce the two comparison sizes with gltf-transform (node container):
#   - pilot.dracoonly.glb : Draco compression, NO decimation (full fidelity)
#   - pilot.draco.glb      : optimize (meshopt error-aware simplify + Draco)
# Measures raw / draco-only / optimized byte sizes and the optimized tri count.
set -euo pipefail
EC2="${EC2:-ubuntu@44.197.243.177}"
KEY="${KEY:-$HOME/.ssh/pax-ec2-key.pem}"
RWD="${RWD:-/home/ubuntu/3dtwin/bakeoff_twin}"
IN="${IN:-/data/in/B_pilot_utm.tif}"
OUT="${OUT:-/data/mesh3dtiles_B}"
NODE="${NODE:-node:20-slim}"
SSH="ssh -i $KEY -o StrictHostKeyChecking=no $EC2"
HOST_OUT="$RWD/$(basename "$OUT")"

$SSH "set -e
  rm -rf $OUT
  sudo docker run --rm -v $RWD:/data -e IN_TIF=$IN -e OUT_DIR=$OUT -e STRIDE=1 bakeoff-py \
       python /data/10_mesh_to_3dtiles.py
  sudo docker run --rm -v $RWD:/data $NODE bash -c '
    cd $OUT && \
    npx --yes @gltf-transform/cli@4 draco pilot.glb pilot.dracoonly.glb >/dev/null 2>&1 && \
    npx --yes @gltf-transform/cli@4 optimize pilot.glb pilot.draco.glb --compress draco --texture-compress false 2>&1 | grep -iE \"glb\" | tail -1 && \
    echo -n \"optimized triangles: \" && npx --yes @gltf-transform/cli@4 inspect pilot.draco.glb 2>&1 | grep TRIANGLES'
  echo '--- mesh sizes (bytes) ---'
  stat -c '%n %s' $HOST_OUT/pilot.glb $HOST_OUT/pilot.dracoonly.glb $HOST_OUT/pilot.draco.glb $HOST_OUT/tileset.json
"

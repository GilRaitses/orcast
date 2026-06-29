#!/usr/bin/env bash
# Step 3: gltfpack meshopt-compress every glb tile in place (EXT_meshopt_compression +
# KHR_mesh_quantization), the same optimisation the served pilot used.
# Run on the EC2 host: `bash 03_compress.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
cd "${WORKDIR}"

RAW_BYTES=$(du -sb tileset/tiles | awk '{print $1}')
echo "=== Raw glb bytes (pre-gltfpack): ${RAW_BYTES} ==="

echo "=== gltfpack -cc each tile (node container) ==="
sudo docker run --rm -v "${WORKDIR}:/data" -w /data "${NODE_IMAGE}" bash -lc '
  set -e
  npm i -g gltfpack >/tmp/npm.log 2>&1 || { cat /tmp/npm.log; exit 1; }
  n=0
  for f in tileset/tiles/*.glb; do
    out="${f%.glb}.tmp.glb"
    gltfpack -i "$f" -o "$out" -cc >/dev/null 2>&1
    mv "$out" "$f"
    n=$((n+1))
  done
  echo "compressed $n tiles"
'

OPT_BYTES=$(du -sb tileset/tiles | awk '{print $1}')
echo "=== Optimized glb bytes (post-gltfpack): ${OPT_BYTES} ==="
awk -v r="${RAW_BYTES}" -v o="${OPT_BYTES}" 'BEGIN{ if(o>0) printf "compression ratio: %.2fx\n", r/o }'
du -sh tileset

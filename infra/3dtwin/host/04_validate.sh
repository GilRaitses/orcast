#!/usr/bin/env bash
# Step 4: validate the whole tileset tree with the CesiumGS 3d-tiles-validator.
# Require 0 errors. The validator follows children + content, so it validates every glb.
# Run on the EC2 host: `bash 04_validate.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
cd "${WORKDIR}"

echo "=== 3d-tiles-validator (CesiumGS) over tileset/tileset.json ==="
sudo docker run --rm -v "${WORKDIR}:/data" -w /data "${NODE_IMAGE}" bash -lc '
  set -e
  npm i -g 3d-tiles-validator >/tmp/val_install.log 2>&1 || { cat /tmp/val_install.log; exit 1; }
  cd tileset
  3d-tiles-validator --tilesetFile tileset.json
' | tee validation_full.json

echo
echo "=== Error / warning summary ==="
grep -iE '"numErrors"|"numWarnings"|"numInfos"' validation_full.json | head || true

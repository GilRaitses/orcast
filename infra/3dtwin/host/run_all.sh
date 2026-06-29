#!/usr/bin/env bash
# Driver: full-extent batch conversion, end to end, on the aimez-services EC2.
#   1 fetch + reproject (CUDEM wash_bellingham -> EPSG:32610 / NAVD88 m, full bbox)
#   2 bake OGC 3D Tiles 1.1 LoD quadtree (glb + tileset.json)
#   3 gltfpack meshopt-compress every glb
#   4 validate with CesiumGS 3d-tiles-validator (require 0 errors)
#   5 upload to s3://aimez-data/3dtwin/full/ + confirm CloudFront/CORS
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -euo pipefail
bash "${SCRIPT_DIR}/01_fetch_reproject.sh"
bash "${SCRIPT_DIR}/02_bake.sh"
bash "${SCRIPT_DIR}/03_compress.sh"
bash "${SCRIPT_DIR}/04_validate.sh"
bash "${SCRIPT_DIR}/05_upload.sh"
echo "=== run_all complete ==="

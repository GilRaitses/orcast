#!/usr/bin/env bash
# Driver: run the full pilot pipeline on the EC2 host (x86_64, native docker GDAL).
# Usage (on the host, from ~/3dtwin/reproject):  bash run_pipeline.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"

echo "############################################################"
echo "# orcast 3dtwin reproject+mesh pilot  (agent B, Wave 1)"
echo "# host arch : $(uname -m)   workdir: ${WORKDIR}"
echo "# gdal image: ${GDAL_IMAGE}"
echo "############################################################"

bash "${SCRIPT_DIR}/01_coverage.sh"
bash "${SCRIPT_DIR}/02_clip_reproject.sh"
bash "${SCRIPT_DIR}/03_mesh_shoreline.sh"

echo
echo "=== Pilot outputs in ${WORKDIR} ==="
ls -lh "${WORKDIR}"/pilot_*.tif "${WORKDIR}"/pilot_mesh.* "${WORKDIR}"/pilot_shoreline_0m.* 2>/dev/null || true
echo "Done. Upload the large artifacts (pilot_utm.tif, pilot_mesh.ply) to S3 from a host with creds."

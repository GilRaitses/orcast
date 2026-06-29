#!/usr/bin/env bash
# Step 5: upload the validated tileset tree to s3://aimez-data/3dtwin/full/ via the
# instance role, with correct content types, then confirm CloudFront + CORS.
# Run on the EC2 host: `bash 05_upload.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
cd "${WORKDIR}"

aws_cli() { sudo docker run --rm --network host -v "${WORKDIR}:/data" -w /data "${AWS_IMAGE}" "$@"; }

echo "=== Upload glb tiles (model/gltf-binary) ==="
aws_cli s3 sync tileset/tiles "${S3_PREFIX}/tiles" \
  --content-type "model/gltf-binary" --exclude "*" --include "*.glb" --no-progress

echo "=== Upload tileset.json + sidecars (application/json) ==="
aws_cli s3 cp tileset/tileset.json "${S3_PREFIX}/tileset.json" --content-type "application/json"
[ -s full.bounds.json ] && aws_cli s3 cp full.bounds.json "${S3_PREFIX}/full.bounds.json" --content-type "application/json"
[ -s validation_full.json ] && aws_cli s3 cp validation_full.json "${S3_PREFIX}/validation_report.txt" --content-type "text/plain"
[ -s navd88_proof_full.txt ] && aws_cli s3 cp navd88_proof_full.txt "${S3_PREFIX}/navd88_proof_full.txt" --content-type "text/plain"

echo
echo "=== S3 listing ==="
aws_cli s3 ls "${S3_PREFIX}/" --recursive --human-readable --summarize | tail -20

echo
echo "=== CloudFront + CORS check (expect HTTP/2 200 + access-control-allow-origin) ==="
curl -sI -H "Origin: https://example.com" "${CF_BASE}/tileset.json" | grep -iE "HTTP/|content-type|access-control-allow-origin|x-cache|etag"

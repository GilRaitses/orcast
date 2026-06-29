#!/usr/bin/env bash
# Stage bake-off outputs to s3://aimez-data/3dtwin/bakeoff/.
#
# IMPORTANT: the EC2 instance role (aimez-host-role) is DENIED s3:PutObject and
# s3:ListBucket on the aimez-data bucket (verified 2026-06-27). Uploading from
# the box fails with AccessDenied. So outputs are pulled to the operator
# workstation over scp and uploaded there with credentialed AWS access.
# Wave 2 batch baking on EC2 will need the instance-role policy extended, or a
# credentialed staging path.
set -euo pipefail
EC2="${EC2:-ubuntu@44.197.243.177}"
KEY="${KEY:-$HOME/.ssh/pax-ec2-key.pem}"
RWD="${RWD:-/home/ubuntu/3dtwin/bakeoff_twin}"
BUCKET="${BUCKET:-s3://aimez-data/3dtwin/bakeoff}"
FIG="${FIG:-$(cd "$(dirname "$0")/.." && pwd)/figures}"

tmp="$(mktemp -d)"
scp -q -i "$KEY" -o StrictHostKeyChecking=no -r \
    "$EC2:$RWD/mesh3dtiles_B" "$EC2:$RWD/qmesh_B" "$tmp/"

aws s3 cp "$tmp/mesh3dtiles_B" "$BUCKET/mesh3dtiles/" --recursive --only-show-errors
aws s3 cp "$tmp/qmesh_B"       "$BUCKET/qmesh/"       --recursive --only-show-errors
aws s3 cp "$FIG"               "$BUCKET/figures/"     --recursive --exclude '*' --include '*.png' --only-show-errors

echo "staged to $BUCKET"
aws s3 ls "$BUCKET/mesh3dtiles/" --human-readable
echo -n 'qmesh .terrain in S3: '; aws s3 ls "$BUCKET/qmesh/" --recursive | grep -c '.terrain'

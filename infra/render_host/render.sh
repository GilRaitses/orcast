#!/usr/bin/env bash
# Reliable headless render of an orcast route on the aimez render host.
#
# WHY THIS EXISTS: local dev servers are unreliable for verifying the 3D twin.
# This drives the aimez-services EC2 over SSM (rock-solid control channel) and
# ships code in / frames out through S3 (the orcast reports bucket the host's
# instance role can write). It has NO dependency on SSH port 22, which has been
# observed to flake while SSM stayed up.
#
# usage:
#   infra/render_host/render.sh <route> [waitMs]      # sync code, render, pull frame
#   infra/render_host/render.sh --no-sync <route>     # render only (code already on host)
#
# output: a local PNG under .cca/catalogue/O0/20260628_render-host/proof/ and the
# render JSON (canvas present?, console/page error count) printed to stdout.
set -euo pipefail

INSTANCE="i-04a649f91274e9fce"          # aimez-services
BUCKET="198456344617-us-west-2-orcast-aws-backend-reports"
REGION="us-west-2"
PREFIX="render-host"
PORT="3010"
KEY="$HOME/.ssh/pax-ec2-key.pem"        # only used by the optional fast rsync path
HOST="ubuntu@44.197.243.177"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROOF="${REPO_ROOT}/.cca/catalogue/O0/20260628_render-host/proof"

SYNC=1
if [ "${1:-}" = "--no-sync" ]; then SYNC=0; shift; fi
ROUTE="${1:?route required, e.g. /orca or /water}"
WAITMS="${2:-9000}"
mkdir -p "$PROOF"

# --- run a shell snippet on the host via SSM and wait for it ---
ssm() {
  local cid
  cid=$(aws ssm send-command --instance-ids "$INSTANCE" --document-name AWS-RunShellScript \
    --timeout-seconds 600 --parameters "commands=[$1]" --query 'Command.CommandId' --output text)
  local st="Pending"
  while [ "$st" = "Pending" ] || [ "$st" = "InProgress" ] || [ "$st" = "Delayed" ]; do
    sleep 5
    st=$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$INSTANCE" \
      --query 'Status' --output text 2>/dev/null || echo InProgress)
  done
  aws ssm get-command-invocation --command-id "$cid" --instance-id "$INSTANCE" \
    --query 'StandardOutputContent' --output text
  [ "$st" = "Success" ] || { echo "SSM step failed: $st" >&2; \
    aws ssm get-command-invocation --command-id "$cid" --instance-id "$INSTANCE" \
      --query 'StandardErrorContent' --output text >&2; return 1; }
}

dock_aws() { echo "docker run --rm -v /home/ubuntu/orcast:/w amazon/aws-cli $* --region $REGION"; }

if [ "$SYNC" = "1" ]; then
  echo ">> packing web/ (no node_modules/.next) -> S3"
  TAR="/tmp/orcast-web.tgz"
  tar -C "$REPO_ROOT" -czf "$TAR" \
    --exclude='web/node_modules' --exclude='web/.next' \
    --exclude='*.mp4' --exclude='*.mov' web
  aws s3 cp "$TAR" "s3://$BUCKET/$PREFIX/code/orcast-web.tgz" --region "$REGION" --only-show-errors
  # also ship the render script
  aws s3 cp "${REPO_ROOT}/infra/render_host/render_route.mjs" \
    "s3://$BUCKET/$PREFIX/code/render_route.mjs" --region "$REGION" --only-show-errors
  echo ">> host: pull + extract code (node_modules preserved), refresh render script"
  ssm "\"mkdir -p /home/ubuntu/orcast/shots\",\"$(dock_aws s3 cp s3://$BUCKET/$PREFIX/code/orcast-web.tgz /w/orcast-web.tgz --only-show-errors)\",\"tar -C /home/ubuntu/orcast -xzf /home/ubuntu/orcast/orcast-web.tgz\",\"$(dock_aws s3 cp s3://$BUCKET/$PREFIX/code/render_route.mjs /w/render_route.mjs --only-show-errors)\",\"chown -R ubuntu:ubuntu /home/ubuntu/orcast/web /home/ubuntu/orcast/render_route.mjs\""
fi

echo ">> host: ensure deps + dev server on :$PORT, then render $ROUTE"
ssm "\"su - ubuntu -c 'cd ~/orcast/web && [ -d node_modules/.bin ] || npm ci'\",\"su - ubuntu -c 'cd ~/orcast/web && (curl -sf -o /dev/null http://127.0.0.1:$PORT/ || (nohup npx next dev -p $PORT -H 127.0.0.1 >~/orcast/next-dev.log 2>&1 & sleep 12))'\",\"su - ubuntu -c 'for i in \$(seq 1 30); do curl -sf -o /dev/null http://127.0.0.1:$PORT/ && break; sleep 2; done'\",\"su - ubuntu -c 'node ~/orcast/render_route.mjs $ROUTE ~/orcast/shots/shot.png $WAITMS'\",\"$(dock_aws s3 cp /w/shots/shot.png s3://$BUCKET/$PREFIX/shots/shot.png --only-show-errors)\""

OUTNAME="$(echo "$ROUTE" | sed 's#^/##; s#/#_#g')_$(date +%H%M%S).png"
echo ">> pull frame -> $PROOF/$OUTNAME"
aws s3 cp "s3://$BUCKET/$PREFIX/shots/shot.png" "$PROOF/$OUTNAME" --region "$REGION" --only-show-errors
echo "FRAME: $PROOF/$OUTNAME"

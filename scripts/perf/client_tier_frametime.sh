#!/usr/bin/env bash
# Client-tier frame-time capture driver (BSWR-PRF, PRF-B). Mirrors
# infra/render_host/render.sh: ships the harness to the GPU render host over SSM,
# runs it SERIAL on the isolated host (the locked vsync-uncap + CDP CPU-throttle +
# client-viewport + hardened rAF sampler + BSW-on/off A/B), and pulls the metrics
# JSON back to the lane's gate_captures/.
#
# This is a VERIFICATION harness only. It changes NO scene behavior.
#
# GATED: the full --ab run is PRF-ACCEPT (a paid host run = human gate). Run that
# ONLY on explicit O0 go. The --smoke run (vsync-uncap proof) is cheap and is the
# precondition for trusting any number.
#
# usage:
#   scripts/perf/client_tier_frametime.sh --smoke      # prove the vsync uncap on the host
#   scripts/perf/client_tier_frametime.sh --ab         # full BSW-on/off A/B (PRF-ACCEPT; O0-gated)
#
# Honesty: the emulated number is a CPU-throttled LOWER BOUND on a server-class
# (T4) GPU. A miss (>33.3ms) is dispositive; a pass does NOT certify the real
# client GPU. See dispatch/PRF/findings/PRF-METHODOLOGY.md.
set -euo pipefail

MODE="${1:?usage: --smoke | --ab}"

# GPU render host (Tesla T4) is the only honest GL path for a tier number.
INSTANCE="${ORCAST_INSTANCE:-i-0e66ac03c729ebe02}"   # aimez-gpu-capture (Tesla T4)
BUCKET="198456344617-us-west-2-orcast-aws-backend-reports"
REGION="us-west-2"
PREFIX="render-host"
PORT="3010"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE_DIR="${REPO_ROOT}/.cca/catalogue/O0/20260629_bsw-followup-remediation/dispatch/PRF/gate_captures"

# Locked PRF-Q method knobs (override via env for PRF-Q-fixed values).
GL="${ORCAST_GL:-gpu}"
VSYNC="${ORCAST_VSYNC:-uncapped}"
CPU_THROTTLE="${ORCAST_CPU_THROTTLE:-4}"   # emulated laptop CPU tier; PRF-Q records the exact rate
VW="${ORCAST_VW:-1280}"; VH="${ORCAST_VH:-800}"; DSF="${ORCAST_DSF:-1}"
WARMUP_MS="${ORCAST_WARMUP_MS:-2000}"
SAMPLE_MS="${ORCAST_SAMPLE_MS:-10000}"
RUNS="${ORCAST_RUNS:-3}"
PWPATH="/home/ubuntu/orcast/web/node_modules/playwright/index.js"

mkdir -p "$GATE_DIR"

ssm() {
  local cid
  cid=$(aws ssm send-command --instance-ids "$INSTANCE" --document-name AWS-RunShellScript \
    --timeout-seconds 1800 --parameters "commands=[$1]" --query 'Command.CommandId' --output text)
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

echo ">> ship harness -> S3"
aws s3 cp "${REPO_ROOT}/infra/render_host/frametime_client_tier.mjs" \
  "s3://$BUCKET/$PREFIX/code/frametime_client_tier.mjs" --region "$REGION" --only-show-errors
echo ">> host: pull harness"
ssm "\"$(dock_aws s3 cp s3://$BUCKET/$PREFIX/code/frametime_client_tier.mjs /w/frametime_client_tier.mjs --only-show-errors)\",\"chown ubuntu:ubuntu /home/ubuntu/orcast/frametime_client_tier.mjs\""

COMMON_ENV="ORCAST_PW=$PWPATH ORCAST_GL=$GL ORCAST_VSYNC=$VSYNC ORCAST_VW=$VW ORCAST_VH=$VH ORCAST_DSF=$DSF ORCAST_WARMUP_MS=$WARMUP_MS ORCAST_SAMPLE_MS=$SAMPLE_MS ORCAST_RUNS=$RUNS"

if [ "$MODE" = "--smoke" ]; then
  echo ">> host: vsync-uncap smoke (no dev server needed; trivial page)"
  OUT=$(ssm "\"su - ubuntu -c '$COMMON_ENV node ~/orcast/frametime_client_tier.mjs --smoke'\"")
  echo "$OUT"
  echo "$OUT" > "$GATE_DIR/smoke_$(date +%Y%m%d_%H%M%S).json"
elif [ "$MODE" = "--ab" ]; then
  echo ">> host: ensure dev server on :$PORT, then run the BSW-on/off A/B SERIAL (CPU throttle ${CPU_THROTTLE}x)"
  ssm "\"su - ubuntu -c 'cd ~/orcast/web && [ -d node_modules/.bin ] || npm ci'\",\"su - ubuntu -c 'cd ~/orcast/web && (curl -sf -o /dev/null http://127.0.0.1:$PORT/ || (nohup npx next dev -p $PORT -H 127.0.0.1 >~/orcast/next-dev.log 2>&1 & sleep 12))'\",\"su - ubuntu -c 'for i in \$(seq 1 40); do curl -sf -o /dev/null http://127.0.0.1:$PORT/ && break; sleep 2; done'\""
  OUT=$(ssm "\"su - ubuntu -c '$COMMON_ENV ORCAST_CPU_THROTTLE=$CPU_THROTTLE ORCAST_DEV_BASE=http://127.0.0.1:$PORT node ~/orcast/frametime_client_tier.mjs --ab'\"")
  echo "$OUT"
  echo "$OUT" > "$GATE_DIR/frametime_ab_emulated_$(date +%Y%m%d_%H%M%S).json"
  echo ">> also capture the uncapped T4 reference (throttle=1) for the two-number report"
  OUT2=$(ssm "\"su - ubuntu -c '$COMMON_ENV ORCAST_CPU_THROTTLE=1 ORCAST_DEV_BASE=http://127.0.0.1:$PORT node ~/orcast/frametime_client_tier.mjs --ab'\"")
  echo "$OUT2"
  echo "$OUT2" > "$GATE_DIR/frametime_ab_t4_uncapped_$(date +%Y%m%d_%H%M%S).json"
else
  echo "usage: --smoke | --ab" >&2; exit 2
fi
echo ">> gate captures in $GATE_DIR"

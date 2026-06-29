#!/usr/bin/env bash
# F network check — RDS must not accept public TCP 5432
set -euo pipefail

HOST="${EXPLORATION_RDS_HOST:-}"
if [ -z "$HOST" ]; then
  HOST=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME:-orcast-aws-backend}" \
    --region "${AWS_REGION:-us-west-2}" \
    --query "Stacks[0].Outputs[?OutputKey=='ExplorationDatabaseEndpoint'].OutputValue" \
    --output text 2>/dev/null || true)
fi

if [ -z "$HOST" ] || [ "$HOST" = "None" ]; then
  echo "F network check skipped (no exploration RDS output)"
  exit 0
fi

echo "Checking public reachability of $HOST:5432 ..."
if nc -zv -w 3 "$HOST" 5432 2>&1; then
  echo "F network check: FAIL — Postgres port is publicly reachable"
  exit 1
fi

echo "F network check: PASS (connection refused or timed out)"

#!/usr/bin/env bash
# AT-4 — backend smoke against App Runner
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

BACKEND_URL="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"

echo "== AT smoke: ${BACKEND_URL} =="
python3 tools/testing/test_aws_backend_smoke.py --base-url "$BACKEND_URL"

echo "AT smoke gate: PASS"

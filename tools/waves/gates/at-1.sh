#!/usr/bin/env bash
# AT-1 — backend lane pytest after API truth wave 1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

python3 -m pytest \
  tests/aws_backend/test_read_endpoints.py \
  tests/aws_backend/test_auth.py \
  tests/aws_backend/test_forecast.py \
  -q --tb=short

echo "AT-1 gate: PASS"

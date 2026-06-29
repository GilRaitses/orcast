#!/usr/bin/env bash
# F local gate — explore limits + regression
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== F local: exploration tests =="
python -m pytest \
  tests/aws_backend/test_exploration_store.py \
  tests/aws_backend/test_explore_router.py \
  tests/aws_backend/test_explore_limits.py \
  -q

echo "== F local: web typecheck =="
(cd web && npm run typecheck)

echo "F local: PASS"

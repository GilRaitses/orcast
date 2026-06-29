#!/usr/bin/env bash
# G local gate — AI Gateway route, viewport helpers, explore tests
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== G local: explore + auth tests =="
PYTHONPATH=src python3 -m pytest \
  tests/aws_backend/test_explore_router.py \
  tests/aws_backend/test_auth_hardening.py \
  -q --tb=no

echo "== G local: web typecheck =="
cd web && npm run typecheck

echo "G local: PASS"

#!/usr/bin/env bash
# E2 local gate — exploration pytest + web typecheck
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== E2 local: exploration backend tests =="
python -m pytest tests/aws_backend/test_exploration_store.py tests/aws_backend/test_explore_router.py -q

echo "== E2 local: web typecheck =="
(cd web && npm run typecheck)

echo "E2 local: PASS"

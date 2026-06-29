#!/usr/bin/env bash
# M local gate — casting registry, interactions, policy tests
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== M local: casting pytest =="
PYTHONPATH=src python3 -m pytest \
  tests/aws_backend/test_managed_agents_registry.py \
  tests/aws_backend/test_interactions_router.py \
  tests/aws_backend/test_casting_policy.py \
  tests/aws_backend/test_explore_router.py \
  -q --tb=no

echo "== M local: no google imports in casting =="
if rg -i 'google|gemini|vertex' src/aws_backend/casting/ 2>/dev/null; then
  echo "FAIL: Google/Gemini references in casting package"
  exit 1
fi

echo "== M local: doc grep =="
bash "$ROOT/tools/waves/gates/m-doc-grep.sh"

echo "M local: PASS"

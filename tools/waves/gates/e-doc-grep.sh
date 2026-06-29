#!/usr/bin/env bash
# E-doc-grep — exploration docs consistency
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

fail=0

grep -q "exploration_sessions" docs/devpost/exploration/CONTRACT.md || { echo "MISSING: CONTRACT schema"; fail=1; }
grep -q "ORCAST_DATABASE_URL" docs/devpost/exploration/CONTRACT.md || { echo "MISSING: CONTRACT env"; fail=1; }
grep -q "Exploration guide" web/app/explore/page.tsx || { echo "MISSING: explore page title"; fail=1; }
grep -q "/explore" web/app/components/Nav.tsx || { echo "MISSING: nav explore link"; fail=1; }
grep -q "aurora" docs/devpost/figures/architecture.mmd || { echo "MISSING: architecture aurora"; fail=1; }

if [ "$fail" -ne 0 ]; then
  echo "E-doc-grep: FAIL"
  exit 1
fi
echo "E-doc-grep: PASS"

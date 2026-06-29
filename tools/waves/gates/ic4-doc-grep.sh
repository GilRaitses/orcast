#!/usr/bin/env bash
# IC4 doc consistency — API.md + gates UI + IC4 dossier
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

fail=0
check() {
  if ! eval "$1"; then
    echo "FAIL: $2"
    fail=1
  fi
}

check "test -f docs/devpost/casting/IC4_PREFLIGHT.md" "IC4_PREFLIGHT.md missing"
check "test -f docs/devpost/casting/IC4_NEXT_OBJECTIVES.md" "IC4_NEXT_OBJECTIVES.md missing"
check "test -f web/lib/gateDisplay.ts" "gateDisplay.ts missing"
check "rg -q '/api/gates' docs/API.md" "gates in API.md"
check "rg -q '/api/decision-records' docs/API.md" "decision-records in API.md"
check "rg -q '/api/interactions' docs/API.md" "interactions in API.md"
check "rg -q 'display_status' docs/API.md" "display_status documented in API.md"
check "rg -q 'Historical data' orcast-angular/src/app/components/landing/landing.component.ts" "historical badge on landing"
check "rg -q 'badge caution' web/app/gates/page.tsx" "caution badge on gates page"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "IC4 doc grep: PASS"

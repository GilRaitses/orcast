#!/usr/bin/env bash
# IC6 doc consistency — surface planner charter, UI intent schema, plan route
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

check "test -f docs/devpost/casting/J0_SURFACE_PLANNER_CHARTER.md" "J0 charter missing"
check "test -f docs/devpost/casting/UI_INTENT_SCHEMA.md" "UI_INTENT_SCHEMA missing"
check "test -f src/aws_backend/casting/panel_registry.json" "panel_registry.json missing"
check "test -f src/aws_backend/casting/planner.py" "planner.py missing"
check "test -f src/aws_backend/casting/seeds/surface-planner-v1.json" "surface-planner-v1 seed missing"
check "rg -q 'POST /api/interactions/plan' docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md docs/API.md" "plan route in docs"
check "rg -q 'plan_output' docs/devpost/casting/INTERACTIONS_GROUNDING_PATTERN.md" "plan_output in grounding pattern"
check "rg -q 'surface-planner-v1' docs/devpost/casting/SKILL_CATALOG.md" "planner in SKILL_CATALOG"
check "rg -q 'id: IC6' docs/devpost/waves.registry.yaml" "IC6 in waves.registry.yaml"
check "test -f web/lib/uiIntent.ts" "uiIntent.ts missing"
check "test -f web/app/components/ActiveSurfaceHost.tsx" "ActiveSurfaceHost missing"
check "test -f web/app/api/interactions/plan/route.ts" "Vercel plan proxy missing"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "IC6 doc grep: PASS"

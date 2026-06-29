#!/usr/bin/env bash
# IC doc consistency — synthesis, pattern, catalog, registry family IC
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

check "test -f docs/devpost/casting/IC0_STEP_LOG_SYNTHESIS.md" "IC0_STEP_LOG_SYNTHESIS.md missing"
check "test -f docs/devpost/casting/INTERACTIONS_GROUNDING_PATTERN.md" "INTERACTIONS_GROUNDING_PATTERN.md missing"
check "test -f docs/devpost/casting/SKILL_CATALOG.md" "SKILL_CATALOG.md missing"
check "test -f src/aws_backend/casting/skills_manifest.json" "skills_manifest.json missing"
check "rg -q 'Interactions casting family \\(IC\\)' docs/devpost/WAVES_REGISTRY.md" "IC family in WAVES_REGISTRY"
check "rg -q 'id: IC0' docs/devpost/waves.registry.yaml" "IC0 in waves.registry.yaml"
check "rg -q 'next_wave_set: IC' docs/devpost/waves.registry.yaml" "next_wave_set IC in registry"
check "rg -q 'INTERACTIONS_GROUNDING_PATTERN' docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md" "pattern cross-link in CONTRACT"
check "rg -q 'POST /api/interactions/prepare' docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md" "prepare endpoint in CONTRACT"
check "rg -q 'ExploreGuidePanel' docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md" "IC3 UI cross-link in CONTRACT"
check "test -f web/app/api/interactions/route.ts" "interactions Gateway route"
check "! rg -i 'googleapis|vertex ai|gemini api|import google' docs/devpost/casting/SKILL_CATALOG.md docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md 2>/dev/null" "Google SDK/API refs in catalog or contract"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "IC doc grep: PASS"

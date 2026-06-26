#!/usr/bin/env bash
# S wave doc consistency — submission copy + registry
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

check "test -f docs/devpost/submission/S0_SUBMISSION_SYNC_CHARTER.md" "S0 charter missing"
check "rg -q 'nine DynamoDB|9 tables|nine \`orcast' docs/devpost/SUBMISSION.md docs/devpost/DEVPOST_DRAFT.md" "nine tables in submission copy"
check "rg -q 'managed-agents' docs/devpost/SUBMISSION.md docs/devpost/DYNAMODB_PROOF.md" "managed-agents in proof"
check "rg -q 'planner=1|surface planner|Central Casting' docs/devpost/SUBMISSION.md docs/devpost/DEMO_STORYBOARD.md" "planner in demo"
check "rg -q 'id: S0' docs/devpost/waves.registry.yaml" "S0 in registry"
check "rg -q 'Central Casting' docs/devpost/figures/architecture.mmd" "Casting in architecture.mmd"
check "test -f docs/devpost/figures/architecture.png" "architecture.png missing"
check "test -f docs/devpost/figures/orcast-erd-workflows-page1.png" "ERD page1 PNG missing"
check "rg -q 'managed-agents' docs/devpost/figures/orcast-erd-workflows.drawio" "managed-agents in drawio"
check "rg -q 'next_wave_set: H1' docs/devpost/waves.registry.yaml" "next_wave_set H1"

# Wave Set SD — Standing Decisions Register + corrected deploy canon (SD-011)
check "test -f .cca/STANDING_DECISIONS_REGISTER.md" "Standing Decisions Register missing"
check "rg -q 'STANDING_DECISIONS_REGISTER' .cca/CLAIM_BOUNDARIES.md docs/devpost/WAVES_REGISTRY.md" "SDR decision-of-record pointer missing"
check "test ! -f vercel.json" "deploy canon: repo-root vercel.json must not exist (SD-011)"
check "test -f web/vercel.json && rg -q '\"framework\": \"nextjs\"' web/vercel.json" "deploy canon: web/vercel.json with framework nextjs (SD-011)"
check "! rg -q 'cd web && npm install' web/vercel.json 2>/dev/null" "deploy canon: web/vercel.json must not pin cd-web install (SD-011)"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "S doc grep: PASS"

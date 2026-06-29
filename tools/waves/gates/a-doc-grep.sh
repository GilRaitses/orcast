#!/usr/bin/env bash
# A wave doc consistency — agent demo automation charter + cross-links
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

check "test -f docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md" "A0 charter missing"
check "rg -q 'DEMO_NO_CRED_STORYBOARD' docs/devpost/DEMO_STORYBOARD.md" "DEMO_NO_CRED cross-link in DEMO_STORYBOARD"
check "rg -q 'DEMO_NO_CRED_STORYBOARD' docs/devpost/submission/H1_MANUAL_SUBMIT.md" "DEMO_NO_CRED cross-link in H1_MANUAL_SUBMIT"
check "rg -q 'a-gate' docs/devpost/submission/H1_MANUAL_SUBMIT.md docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md" "a-gate in operator docs"
check "rg -q 'demo-walkthrough.webm' docs/devpost/submission/H1_MANUAL_SUBMIT.md docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md" "video artifact in operator docs"
check "rg -q 'agentAuth' tools/testing/AGENT_USER.md docs/devpost/workflow-truth-table.md" "agentAuth in AGENT_USER / truth table"
check "rg -q 'id: A0' docs/devpost/waves.registry.yaml" "A0 in registry"
check "rg -q 'id: A5' docs/devpost/waves.registry.yaml" "A5 in registry"
check "rg -q 'gate: a-gate' docs/devpost/waves.registry.yaml" "a-gate in registry"
check "rg -q 'next_wave_set: H1' docs/devpost/waves.registry.yaml" "next_wave_set H1 (A complete)"
check "rg -q 'a-gate' tools/waves/run-gate.sh" "a-gate in run-gate.sh"
check "rg -q 'a-maps' tools/waves/run-gate.sh" "a-maps in run-gate.sh"
check "test -f tools/testing/setup_demo_maps.sh" "setup_demo_maps.sh missing"
check "test -f tools/waves/gates/a-maps-smoke.sh" "a-maps-smoke.sh missing"
check "test -f tools/waves/gates/a-video-gate.sh" "a-video-gate.sh missing"
check "test -f web/lib/agentAuth.ts" "agentAuth.ts missing"
check "test -f web/playwright.config.ts" "playwright.config.ts missing"
check "test -f web/public/demo-slides/dynamodb-proof.png" "demo slide dynamodb-proof missing"
check "test -f web/public/demo-slides/architecture.png" "demo slide architecture missing"
check "test -f docs/devpost/DEMO_NO_CRED_STORYBOARD.md" "DEMO_NO_CRED_STORYBOARD missing"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "A doc grep: PASS"

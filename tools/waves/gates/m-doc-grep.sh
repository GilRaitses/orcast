#!/usr/bin/env bash
# M doc consistency — CONTRACT + registry family M
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

check "test -f docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md" "MANAGED_AGENTS_CONTRACT.md missing"
check "rg -q 'explore-guide-v1' docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md" "seed agent id in CONTRACT"
check "rg -q 'POST /api/interactions' docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md" "interactions path in CONTRACT"
check "rg -q 'Managed agents family \\(M\\)' docs/devpost/WAVES_REGISTRY.md" "M family in WAVES_REGISTRY"
check "rg -q 'id: M0' docs/devpost/waves.registry.yaml" "M0 in waves.registry.yaml"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "M doc grep: PASS"

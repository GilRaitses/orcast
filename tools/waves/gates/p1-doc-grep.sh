#!/usr/bin/env bash
# P1-gate (part 1) — stale copy and ghost endpoint patterns in active tree
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

FAIL=0

check_absent() {
  local label="$1"
  shift
  local hits
  hits="$(rg -l "$@" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    echo "FAIL $label — matches in:"
    echo "$hits"
    FAIL=1
  else
    echo "OK   $label"
  fi
}

echo "== P1 doc/copy grep (active user-facing tree) =="

# User-facing web + angular only (not meta docs in HANDOFF)
check_absent "zero-trust tagline" \
  -i 'zero-trust forecast|zero-trust orchestrator' \
  web/ orcast-angular/src/

check_absent "honest orca tagline" \
  -i 'honest orca forecasting' \
  web/

check_absent "multi-agent platform tagline" \
  -i 'multi-agent whale research platform' \
  web/ orcast-angular/src/app/

# Ghost endpoints promoted as live (exclude API.md which documents 410 Gone)
check_absent "ghost endpoint promoted as live" \
  '/api/predictions|/api/behavioral-analysis|/api/dtag-data' \
  docs/ \
  --glob '!docs/API.md' \
  --glob '!docs/field-campaign/**' \
  --glob '!archive/**'

# Routed Angular user-facing strings (quarantine excluded)
ANG_HITS="$(rg -l 'ORCAST Agent Ready|Multi-Agent Whale' orcast-angular/src/app/components \
  2>/dev/null || true)"
if [ -n "$ANG_HITS" ]; then
  echo "FAIL stale Angular routed copy:"
  echo "$ANG_HITS"
  FAIL=1
else
  echo "OK   Angular routed components"
fi

if [ "$FAIL" -ne 0 ]; then
  echo "P1 doc grep: FAIL"
  exit 1
fi
echo "P1 doc grep: PASS"

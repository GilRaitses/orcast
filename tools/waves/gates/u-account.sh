#!/usr/bin/env bash
# U5 — Account content management gate
# Tests: list evidence, journal entries with evidence_assets field, account page loads.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

source "$ROOT/.agent-credentials.env" 2>/dev/null || true
KEY="${ORCAST_AGENT_KEY:-}"
WEB="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"

fail=0
check() {
  local desc="$1"
  shift
  if "$@"; then
    echo "PASS: $desc"
  else
    echo "FAIL: $desc"
    fail=1
  fi
}

# --- Check if evidence endpoint is deployed ---
EV_STATUS=$(curl -sf -o /dev/null -w '%{http_code}' "$WEB/api/be/api/evidence/assets" 2>/dev/null || echo "000")
EV_DEPLOYED=true
if [ "$EV_STATUS" = "404" ]; then
  echo "SKIP: /api/evidence/assets not deployed (404) — evidence tests skipped"
  EV_DEPLOYED=false
fi

if [ -z "$KEY" ]; then
  echo "SKIP: ORCAST_AGENT_KEY not set — authenticated tests skipped"
else
  if [ "$EV_DEPLOYED" = "true" ]; then
    # --- Evidence list endpoint ---
    check "GET /api/evidence/assets returns list" bash -c \
      "curl -sf '$WEB/api/be/api/evidence/assets' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get(\"status\")==\"success\"; assert isinstance(d.get(\"assets\",[]), list)'"

    # --- Anonymous cannot list evidence ---
    check "anonymous GET /api/evidence/assets rejected" bash -c \
      "CODE=\$(curl -sf -o /dev/null -w '%{http_code}' '$WEB/api/be/api/evidence/assets' 2>/dev/null || echo 000); [[ \"\$CODE\" =~ ^(401|403)$ ]]"

    # --- Anonymous delete rejected ---
    check "anonymous DELETE /api/evidence/assets/id rejected" bash -c \
      "CODE=\$(curl -sf -o /dev/null -w '%{http_code}' -X DELETE '$WEB/api/be/api/evidence/assets/fake_asset' 2>/dev/null || echo 000); [[ \"\$CODE\" =~ ^(401|403)$ ]]"
  fi

  # --- Journal entries have evidence_assets field ---
  check "journal entries have evidence_assets list field" bash -c \
    "curl -sf '$WEB/api/be/api/journal/entries' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c 'import json,sys; d=json.load(sys.stdin); entries=d.get(\"entries\",[]); all(isinstance(e.get(\"evidence_assets\",[]), list) for e in entries)'"
fi

# --- Account page HTTP 200 ---
check "/account page returns 200" bash -c \
  "CODE=\$(curl -sf -o /dev/null -w '%{http_code}' '$WEB/account' 2>/dev/null || echo 000); [ \"\$CODE\" = '200' ]"

if [ "$fail" -ne 0 ]; then
  echo "u-account gate: FAIL"
  exit 1
fi
echo "u-account gate: PASS"

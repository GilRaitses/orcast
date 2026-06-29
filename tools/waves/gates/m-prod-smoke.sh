#!/usr/bin/env bash
# M prod smoke — interactions by agent_id + registry keyed auth
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

BACKEND="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"
API_KEY="${ORCAST_API_KEY:-}"

echo "== M prod: interactions status =="
STATUS=$(curl -sf "$BACKEND/api/interactions/status")
echo "$STATUS" | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('status')=='success'; assert 'casting_enabled' in b"

echo "== M prod: registry list requires key =="
CODE=$(curl -s -o /dev/null -w '%{http_code}' "$BACKEND/api/managed-agents")
if [ "$CODE" != "401" ] && [ "$CODE" != "503" ]; then
  echo "FAIL: expected 401/503 for unkeyed registry, got $CODE"
  exit 1
fi

if [ -n "$API_KEY" ]; then
  echo "== M prod: seeded explore-guide-v1 (when App Runner key matches) =="
  AGENT_CODE=$(curl -s -o /tmp/m-agent.json -w '%{http_code}' -H "X-ORCAST-Key: $API_KEY" "$BACKEND/api/managed-agents/explore-guide-v1")
  if [ "$AGENT_CODE" = "200" ]; then
    python3 -c "import json; b=json.load(open('/tmp/m-agent.json')); assert b['agent']['id']=='explore-guide-v1'"
  else
    echo "SKIP: registry GET returned $AGENT_CODE (sync ORCAST_API_KEY on App Runner)"
  fi
fi

echo "== M prod: explore session + interaction =="
SESSION=$(curl -sf -X POST "$BACKEND/api/explore/sessions" -H "Content-Type: application/json" ${API_KEY:+-H "X-ORCAST-Key: $API_KEY"} -d '{}')
SID=$(echo "$SESSION" | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

INTERACTION=$(curl -sf -X POST "$BACKEND/api/interactions" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SID\",\"message\":\"What gates block promotion?\",\"agent_id\":\"explore-guide-v1\"}")

echo "$INTERACTION" | python3 -c "
import json, sys
b = json.load(sys.stdin)
assert b.get('status') == 'success', b
assert b.get('managed_agent_id') == 'explore-guide-v1', b
assert b.get('hydration_mode') == 'by_id', b
assert b.get('resolved_spec_hash'), b
assert 'fetch_gates' in b.get('skills_invoked', b.get('tools_used', [])), b
"

echo "== M prod: regression e-prod-smoke subset =="
bash "$ROOT/tools/waves/gates/e-prod-smoke.sh"

echo "M prod smoke: PASS"

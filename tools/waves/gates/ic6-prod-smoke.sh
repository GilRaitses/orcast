#!/usr/bin/env bash
# IC6 prod smoke — keyed plan route + public interactions regression
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

BASE="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"
WEB="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
KEY="${ORCAST_API_KEY:-}"

echo "== IC6 prod: public interactions status =="
curl -sf "$BASE/api/interactions/status" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='success'"

echo "== IC6 prod: panel registry file in repo =="
test -f src/aws_backend/casting/panel_registry.json

if [ -n "$KEY" ]; then
  echo "== IC6 prod: keyed plan route (requires session) =="
  SESSION=$(curl -sf -X POST "$BASE/api/explore/sessions" \
    -H "Content-Type: application/json" \
    -H "X-ORCAST-Key: $KEY" \
    -d '{"title":"ic6-gate"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")
  PLAN=$(curl -sf -X POST "$BASE/api/interactions/plan" \
    -H "Content-Type: application/json" \
    -H "X-ORCAST-Key: $KEY" \
    -d "{\"session_id\":\"$SESSION\",\"message\":\"Show decision audit log\"}")
  echo "$PLAN" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ui_intent']['version']=='1.0.0'; assert 'fetch_decision_records' in d['ui_intent']['skill_plan']; assert any(s.get('type')=='plan_output' for s in d['prepare']['steps'])"
else
  echo "SKIP: ORCAST_API_KEY not set — keyed plan curl skipped"
fi

echo "== IC6 prod: ic-gate regression =="
bash "$ROOT/tools/waves/gates/ic-prod-smoke.sh"

echo "IC6 prod smoke: PASS"

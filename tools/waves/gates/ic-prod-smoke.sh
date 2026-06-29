#!/usr/bin/env bash
# IC prod smoke — interaction steps + annotations + IC4/IC5 gates display_status
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

BACKEND="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"
WEB_BASE="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
KEY="${ORCAST_API_KEY:-}"

echo "== IC prod: M baseline =="
bash "$ROOT/tools/waves/gates/m-prod-smoke.sh"

echo "== IC prod: gates CV display_status (IC4/IC5) =="
GATES=$(curl -sf "$BACKEND/api/gates")
echo "$GATES" | python3 -c "
import json, sys
b = json.load(sys.stdin)
cv = b.get('gates', {}).get('cross_validation', {})
assert cv.get('gate_pass') is True, cv
skill = cv.get('mean_deviance_skill')
assert skill is not None and skill < 0, cv
assert cv.get('display_status') == 'caution', cv
assert cv.get('display_pass') is False, cv
caveats = b.get('caveats') or []
assert any('negative' in str(c).lower() for c in caveats), caveats
print('display_status=caution mean_deviance_skill=%.4f' % skill)
"

echo "== IC prod: steps + annotations on interaction =="
SESSION=$(curl -sf -X POST "$BACKEND/api/explore/sessions" \
  -H "Content-Type: application/json" \
  ${ORCAST_API_KEY:+-H "X-ORCAST-Key: $ORCAST_API_KEY"} \
  -d '{}')
SID=$(echo "$SESSION" | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

INTERACTION=$(curl -sf -X POST "$BACKEND/api/interactions" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SID\",\"message\":\"What gates block promotion?\",\"agent_id\":\"explore-guide-v1\"}")

echo "$INTERACTION" | python3 -c "
import json, sys
b = json.load(sys.stdin)
assert b.get('status') == 'success', b
steps = b.get('steps')
assert isinstance(steps, list) and steps, b
assert steps[0].get('type') == 'resolve_agent', steps[0]
assert any(s.get('type') == 'model_output' for s in steps), steps
annotations = b.get('annotations')
assert isinstance(annotations, list), b
"

echo "== IC prod: H0 gates UI bundle (IC4 caution badge) =="
# Client-rendered page; verify deployed JS contains IC4 gateDisplay strings.
GATES_JS=$(curl -sf "$WEB_BASE/gates" | python3 -c "
import re, sys
html = sys.stdin.read()
m = re.search(r'/_next/static/chunks/app/gates/page-[a-f0-9]+\.js', html)
if not m:
    m = re.search(r'/_next/static/chunks/[^\"\\']+gates[^\"\\']*\\.js', html)
print(m.group(0) if m else '')
")
if [ -z "$GATES_JS" ]; then
  echo "WARN: could not locate gates page chunk on $WEB_BASE/gates"
else
  CHUNK=$(curl -sf "$WEB_BASE$GATES_JS")
  echo "$CHUNK" | python3 -c "
import sys
js = sys.stdin.read()
for needle in ('Fold majority passed', 'badge caution', 'Gate:'):
    assert needle in js, f'missing {needle!r} in gates chunk'
print('gates UI chunk: IC4 caution strings present')
"
fi

echo "IC prod smoke: PASS"

#!/usr/bin/env bash
# H0 — hackathon automated pre-submit gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

WEB_BASE="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
BACKEND_URL="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"

echo "== H0: agent_smoke (dry-run) =="
python3 tools/testing/agent_smoke.py --dry-run

echo "== H0: sighting-assist status =="
STATUS_JSON="$(curl -fsS "${WEB_BASE}/api/be/api/sighting-assist/status")"
echo "$STATUS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
backend = d.get('narration_backend', '')
print('narration_backend:', backend)
if backend not in ('bedrock', 'template'):
    raise SystemExit('unexpected narration_backend: ' + str(backend))
"

echo "== H0: backend health =="
curl -fsS -o /dev/null -w "health HTTP %{http_code}\n" "${BACKEND_URL}/health"

echo "== H0: public gates (no auth) =="
curl -fsS "${BACKEND_URL}/api/gates" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'task_token' not in json.dumps(d), 'task_token leaked in public gates'
print('gates status:', d.get('status', 'ok'))
"

if [ -n "${ORCAST_PARTNER_DEV_KEY:-}" ]; then
  echo "== H0: partner gates (dev key) =="
  CODE="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "X-ORCAST-Partner-Key: ${ORCAST_PARTNER_DEV_KEY}" \
    "${WEB_BASE}/api/v1/api/gates")"
  if [ "$CODE" != "200" ]; then
    echo "partner gates returned $CODE (expected 200 when ORCAST_PARTNER_DEV_KEY is set)"
    exit 1
  fi
  echo "partner gates HTTP 200"
else
  echo "== H0: partner gates skipped (ORCAST_PARTNER_DEV_KEY not set) =="
fi

echo "H0 gate: PASS"

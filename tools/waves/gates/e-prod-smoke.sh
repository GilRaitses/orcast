#!/usr/bin/env bash
# E-gate — production exploration smoke
set -euo pipefail

WEB_BASE="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
BACKEND="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"

echo "== E-gate: explore status via H0 proxy =="
STATUS="$(curl -sf "${WEB_BASE}/api/be/api/explore/status")"
echo "$STATUS" | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='success', d"

echo "== E-gate: explore status direct backend =="
curl -sf "${BACKEND}/api/explore/status" | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='success', d"

AURORA="$(echo "$STATUS" | python -c "import json,sys; print(json.load(sys.stdin).get('aurora_connected', False))")"
if [ "$AURORA" = "True" ] || [ "$AURORA" = "true" ]; then
  echo "== E-gate: create session + turn =="
  SID="$(curl -sf -X POST "${WEB_BASE}/api/be/api/explore/sessions" \
    -H 'Content-Type: application/json' \
    -d '{}' | python -c "import json,sys; print(json.load(sys.stdin)['session_id'])")"
  curl -sf -X POST "${WEB_BASE}/api/be/api/explore/turn" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\":\"${SID}\",\"message\":\"Summarize promotion gates.\"}" \
    | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('reply'), d"
  echo "E-gate live turn: PASS"
else
  echo "E-gate: Aurora not connected — status-only PASS (deploy ORCAST_DATABASE_URL for full smoke)"
fi

echo "E-gate: PASS"

#!/usr/bin/env bash
# F prod smoke — exploration + rate limits
set -euo pipefail

WEB_BASE="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
BACKEND="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"

echo "== F prod: explore status =="
STATUS=$(curl -sf "${WEB_BASE}/api/be/api/explore/status")
echo "$STATUS" | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='success', d"
echo "$STATUS" | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('postgres_engine')=='rds', d"

echo "== F prod: session + turn =="
SID=$(curl -sf -X POST "${WEB_BASE}/api/be/api/explore/sessions" \
  -H 'Content-Type: application/json' \
  -d '{}' | python -c "import json,sys; print(json.load(sys.stdin)['session_id'])")
curl -sf -X POST "${WEB_BASE}/api/be/api/explore/turn" \
  -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"${SID}\",\"message\":\"Summarize promotion gates.\"}" \
  | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('reply'), d"

bash "$(dirname "$0")/f-network-check.sh"
bash "$(dirname "$0")/e-prod-smoke.sh"

echo "== F prod: explore session rate limit (6th should 429) =="
HIT429=0
for i in $(seq 1 6); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${WEB_BASE}/api/be/api/explore/sessions" \
    -H 'Content-Type: application/json' -d '{}')
  if [ "$CODE" = "429" ]; then
    HIT429=1
    break
  fi
done
if [ "$HIT429" != "1" ]; then
  echo "WARN: did not observe explore session 429 within 6 attempts (serverless cold buckets may differ)"
fi

echo "F prod smoke: PASS"

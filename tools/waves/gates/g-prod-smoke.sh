#!/usr/bin/env bash
# G prod smoke — AI Gateway config route + deep links + regression
set -euo pipefail

WEB_BASE="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"

echo "== G prod: AI Gateway config =="
CFG=$(curl -sf "${WEB_BASE}/api/explore")
echo "$CFG" | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='success', d"
echo "$CFG" | python -c "import json,sys; d=json.load(sys.stdin); print('ai_gateway_enabled', d.get('ai_gateway_enabled')); print('models', d.get('models'))"

echo "== G prod: explore status + postgres =="
curl -sf "${WEB_BASE}/api/be/api/explore/status" | python -c "import json,sys; d=json.load(sys.stdin); assert d.get('aurora_connected') is True, d"

echo "== G prod: viewport deep link (home) =="
CODE=$(curl -s -o /dev/null -w "%{http_code}" "${WEB_BASE}/?lat=48.55&lng=-123.05&provenance=1")
if [ "$CODE" != "200" ]; then
  echo "G prod: home viewport link HTTP $CODE"
  exit 1
fi

CODE=$(curl -s -o /dev/null -w "%{http_code}" "${WEB_BASE}/explore?lat=48.55&lng=-123.05")
if [ "$CODE" != "200" ]; then
  echo "G prod: explore viewport link HTTP $CODE"
  exit 1
fi

bash "$(dirname "$0")/f-prod-smoke.sh"

echo "G prod smoke: PASS"

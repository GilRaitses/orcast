#!/usr/bin/env bash
# Q1b — API/backend layer schema check
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

source "$ROOT/.agent-credentials.env" 2>/dev/null || true
KEY="${ORCAST_AGENT_KEY:-}"
WEB="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"

fail=0
check() {
  if ! eval "$1"; then
    echo "FAIL: $2"
    fail=1
  else
    echo "PASS: $2"
  fi
}

echo "== Q1b: API schema checks against $WEB =="

# Gates endpoint returns data
check "curl -sf '$WEB/api/be/api/gates' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert len(d) > 0, 'empty gates'\"" \
  "/api/be/api/gates returns data"

# Gates has caveats and effective_confidence
check "curl -sf '$WEB/api/be/api/gates' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert 'effective_confidence' in d,'no effective_confidence'; assert 'caveats' in d,'no caveats'\"" \
  "/api/be/api/gates has effective_confidence and caveats"

# Hotspots returns records with probability
check "curl -sf '$WEB/api/be/api/hotspots?lat=48.5465&lng=-123.03' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c \"import json,sys; d=json.load(sys.stdin); hs=d.get('hotspots',[]); assert len(hs)>0,'no hotspots'; assert 'probability' in hs[0],'no probability field'\"" \
  "/api/be/api/hotspots returns probability field"

# Sightings returns records
check "curl -sf '$WEB/api/be/api/sightings' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c \"import json,sys; d=json.load(sys.stdin); items=d.get('sightings',d if isinstance(d,list) else []); assert len(items)>0,'no sightings'\"" \
  "/api/be/api/sightings returns records"

# Provenance returns effective_confidence
check "curl -sf '$WEB/api/be/api/provenance?lat=48.5465&lng=-123.03' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert 'effective_confidence' in d or 'confidence' in d,'missing confidence fields'\"" \
  "/api/be/api/provenance returns confidence fields"

# Live URL responds
check "curl -sf -o /dev/null -w '%{http_code}' '$WEB' | grep -q 200" \
  "$WEB returns 200"

# interactions/status
BACKEND="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"
check "curl -sf '$BACKEND/api/interactions/status' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d.get('status')=='success'\"" \
  "/api/interactions/status returns success"

if [ "$fail" -ne 0 ]; then
  echo "Q1b: FAIL"
  exit 1
fi
echo "Q1b: PASS"

#!/usr/bin/env bash
# P1-gate (part 2) — production curl smoke
set -euo pipefail

WEB_BASE="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
BACKEND_URL="${ORCAST_BACKEND_URL:-https://pjrftm3bkv.us-west-2.awsapprunner.com}"
CF_URL="${ORCAST_CLOUDFRONT_URL:-https://d2gslju5drx74c.cloudfront.net}"

echo "== P1 prod curl: backend health =="
curl -fsS -o /dev/null -w "health %{http_code}\n" "${BACKEND_URL}/health"

echo "== P1 prod curl: CORS from CloudFront origin =="
curl -fsS -o /dev/null -w "gates+cors %{http_code}\n" \
  -H "Origin: ${CF_URL}" \
  "${BACKEND_URL}/api/gates"

echo "== P1 prod curl: Vercel H0 home =="
curl -fsS -o /dev/null -w "h0 home %{http_code}\n" "${WEB_BASE}/"

echo "== P1 prod curl: CloudFront landing =="
curl -fsS -o /dev/null -w "cf home %{http_code}\n" "${CF_URL}/"

echo "== P1 prod curl: fake partner key -> 401 =="
CODE="$(curl -s -o /dev/null -w '%{http_code}' \
  -H 'X-ORCAST-Partner-Key: orcast_builder_fake' \
  "${WEB_BASE}/api/v1/api/gates")"
if [ "$CODE" != "401" ]; then
  echo "expected 401 for fake partner key, got $CODE"
  exit 1
fi
echo "fake partner key HTTP 401"

if [ -n "${ORCAST_PARTNER_DEV_KEY:-}" ]; then
  CODE="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "X-ORCAST-Partner-Key: ${ORCAST_PARTNER_DEV_KEY}" \
    "${WEB_BASE}/api/v1/api/gates")"
  if [ "$CODE" != "200" ]; then
    echo "expected 200 for dev partner key, got $CODE"
    exit 1
  fi
  echo "dev partner key HTTP 200"
else
  echo "dev partner key check skipped (ORCAST_PARTNER_DEV_KEY not set)"
fi

echo "P1 prod curl: PASS"

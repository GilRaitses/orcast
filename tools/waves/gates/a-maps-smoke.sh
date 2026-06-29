#!/usr/bin/env bash
# A5 maps smoke — Google Maps renders on home, explore, ask (no error overlay)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CREDS="${ROOT}/.agent-credentials.env"
if [ -f "$CREDS" ]; then
  # shellcheck disable=SC1090
  source "$CREDS"
fi

cd "$ROOT/web"
if [ ! -d node_modules/@playwright ]; then
  npm install
fi
npx playwright install chromium

export PW_BASE_URL="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
npx playwright test a-maps-smoke --project=chromium-desktop

echo "A maps smoke: PASS"

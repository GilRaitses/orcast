#!/usr/bin/env bash
# H1 demo walkthrough — agent-automation path (requires .agent-credentials.env)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

CREDS="${ROOT}/.agent-credentials.env"
if [ ! -f "$CREDS" ]; then
  echo "FAIL: missing $CREDS — run bash tools/testing/setup_agent_user.sh"
  exit 1
fi

# shellcheck disable=SC1090
source "$CREDS"

cd web
if [ ! -d node_modules/@playwright ]; then
  npm install
fi
npx playwright install chromium

export PW_BASE_URL="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
export DEMO_SCREENSHOTS=1

npm run demo:screenshots

OUT="${ROOT}/docs/devpost/figures/_demo-run"
for f in beat-01-home beat-02-provenance beat-03-gates beat-04-planner beat-05-ask beat-06-journal beat-06-moderation beat-07-dynamodb beat-08-architecture; do
  if [ ! -f "${OUT}/${f}.png" ]; then
    echo "FAIL: missing ${OUT}/${f}.png"
    exit 1
  fi
done

echo "H1 demo walkthrough: PASS (${OUT})"

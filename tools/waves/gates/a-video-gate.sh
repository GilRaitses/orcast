#!/usr/bin/env bash
# A5 video gate — record full walkthrough webm (~3 min)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CREDS="${ROOT}/.agent-credentials.env"
OUT="${ROOT}/docs/devpost/figures/_demo-run"
VIDEO="${OUT}/demo-walkthrough.webm"

if [ ! -f "$CREDS" ]; then
  echo "FAIL: missing $CREDS — run bash tools/testing/setup_agent_user.sh"
  exit 1
fi

# shellcheck disable=SC1090
source "$CREDS"

cd "$ROOT/web"
if [ ! -d node_modules/@playwright ]; then
  npm install
fi
npx playwright install chromium

export PW_BASE_URL="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
export DEMO_RECORD=1
export PW_SLOW_MO="${PW_SLOW_MO:-800}"

rm -f "$VIDEO"
mkdir -p "$OUT"

npm run demo:record

# Playwright stores video beside the test output folder
FOUND="$(find e2e/.results -name '*.webm' -type f 2>/dev/null | head -1)"
if [ -z "$FOUND" ]; then
  echo "FAIL: no webm produced by demo:record"
  exit 1
fi
cp "$FOUND" "$VIDEO"

if [ ! -s "$VIDEO" ]; then
  echo "FAIL: empty $VIDEO"
  exit 1
fi

SIZE=$(wc -c <"$VIDEO" | tr -d ' ')
if [ "$SIZE" -lt 1000000 ]; then
  echo "FAIL: $VIDEO too small (${SIZE} bytes)"
  exit 1
fi

if command -v ffprobe >/dev/null 2>&1; then
  DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO" 2>/dev/null || echo "0")
  DUR_INT=${DUR%.*}
  if [ "${DUR_INT:-0}" -lt 120 ]; then
    echo "FAIL: $VIDEO duration ${DUR}s (need >= 120s)"
    exit 1
  fi
  echo "Video duration: ${DUR}s"
else
  echo "WARN: ffprobe not found — skipping duration check"
fi

echo "A video gate: PASS ($VIDEO, ${SIZE} bytes)"

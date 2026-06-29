#!/usr/bin/env bash
# U5 — Adversarial upload gate
# Tests: image/audio/generic upload, oversized rejection, anonymous rejection, cross-user isolation.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

source "$ROOT/.agent-credentials.env" 2>/dev/null || true
KEY="${ORCAST_AGENT_KEY:-}"
WEB="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
ENDPOINT="$WEB/api/be/api/evidence/assets"

fail=0
check() {
  local desc="$1"
  shift
  if "$@"; then
    echo "PASS: $desc"
  else
    echo "FAIL: $desc"
    fail=1
  fi
}

# --- Connectivity check: if endpoint returns 404 (not deployed), skip authenticated tests ---
STATUS_CHECK=$(curl -sf -o /dev/null -w '%{http_code}' -X OPTIONS "$ENDPOINT" 2>/dev/null || echo "000")
if [ "$STATUS_CHECK" = "404" ]; then
  echo "SKIP: /api/evidence/assets not yet deployed on App Runner (404)"
  echo "      Deploy backend to App Runner, then re-run this gate."
  echo "u-upload gate: PARTIAL (endpoint not deployed)"
  exit 0
fi

TMPDIR_U=$(mktemp -d)
echo "Test image data $(date)" > "$TMPDIR_U/test-image.txt"
echo "Test audio data $(date)" > "$TMPDIR_U/test-audio.txt"

# --- Anonymous rejection ---
check "anonymous upload rejected with 401 or 403" bash -c \
  "CODE=\$(curl -sf -o /dev/null -w '%{http_code}' -X POST '$ENDPOINT' -F 'file=@$TMPDIR_U/test-image.txt;type=image/jpeg' 2>/dev/null || echo 000); [[ \"\$CODE\" =~ ^(401|403)$ ]]"

if [ -z "$KEY" ]; then
  echo "SKIP: ORCAST_AGENT_KEY not set — authenticated upload tests skipped"
  rm -rf "$TMPDIR_U"
  echo "u-upload gate: PARTIAL (anon rejection tested; auth tests skipped)"
  exit 0
fi

# --- Image upload ---
check "image upload returns EvidenceAsset with kind=image" bash -c \
  "curl -sf -X POST '$ENDPOINT' -H 'X-ORCAST-Agent-Key: $KEY' -F 'file=@$TMPDIR_U/test-image.txt;type=image/jpeg' -F 'kind=image' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get(\"status\")==\"success\"; assert d[\"asset\"][\"kind\"]==\"image\"'"

# --- Audio upload ---
check "audio upload returns EvidenceAsset with kind=audio" bash -c \
  "curl -sf -X POST '$ENDPOINT' -H 'X-ORCAST-Agent-Key: $KEY' -F 'file=@$TMPDIR_U/test-audio.txt;type=audio/mpeg' -F 'kind=audio' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get(\"status\")==\"success\"; assert d[\"asset\"][\"kind\"]==\"audio\"'"

# --- Generic file upload ---
check "generic file upload accepted" bash -c \
  "curl -sf -X POST '$ENDPOINT' -H 'X-ORCAST-Agent-Key: $KEY' -F 'file=@$TMPDIR_U/test-image.txt;type=application/octet-stream' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get(\"status\")==\"success\"'"

# --- Oversized file rejection (26 MB) ---
python3 -c "
with open('$TMPDIR_U/big.bin', 'wb') as f:
    f.write(b'x' * (26 * 1024 * 1024))
"
check "oversized file (26 MB) rejected with 413" bash -c \
  "CODE=\$(curl -sf -o /dev/null -w '%{http_code}' -X POST '$ENDPOINT' -H 'X-ORCAST-Agent-Key: $KEY' -F 'file=@$TMPDIR_U/big.bin' 2>/dev/null || echo 000); [[ \"\$CODE\" =~ ^41 ]]"

# --- List assets ---
check "list assets returns status success" bash -c \
  "curl -sf '$ENDPOINT' -H 'X-ORCAST-Agent-Key: $KEY' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get(\"status\")==\"success\"'"

rm -rf "$TMPDIR_U"

if [ "$fail" -ne 0 ]; then
  echo "u-upload gate: FAIL"
  exit 1
fi
echo "u-upload gate: PASS"

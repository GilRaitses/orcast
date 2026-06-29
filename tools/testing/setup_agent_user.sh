#!/usr/bin/env bash
# Provision ORCAST automation agent: Vercel proxy key + optional WorkOS user.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS_FILE="${REPO_ROOT}/.agent-credentials.env"
WEB_DIR="${REPO_ROOT}/web"
VERCEL_TOKEN="${VERCEL_TOKEN:-}"
AGENT_EMAIL="${ORCAST_AGENT_REVIEWER_EMAIL:-agent@orcast.dev}"
AGENT_ID="${ORCAST_AGENT_REVIEWER_ID:-agent_orcast_automation}"

if [ -z "$VERCEL_TOKEN" ]; then
  echo "Set VERCEL_TOKEN to push ORCAST_AGENT_KEY to Vercel." >&2
  exit 1
fi

if [ -f "$CREDS_FILE" ] && [ "${ORCAST_AGENT_FORCE:-}" != "1" ]; then
  # shellcheck disable=SC1090
  source "$CREDS_FILE"
  if [ -n "${ORCAST_AGENT_KEY:-}" ]; then
    echo "Using existing ORCAST_AGENT_KEY from $CREDS_FILE (set ORCAST_AGENT_FORCE=1 to rotate)."
  fi
fi

if [ -z "${ORCAST_AGENT_KEY:-}" ]; then
  ORCAST_AGENT_KEY="$(openssl rand -hex 32)"
fi

AGENT_PASSWORD="${ORCAST_AGENT_PASSWORD:-$(openssl rand -base64 18 | tr -d '/+=' | head -c 20)}Aa1"

echo "Adding ORCAST_AGENT_* env vars to Vercel production..."
printf '%s' "$ORCAST_AGENT_KEY" | npx vercel env add ORCAST_AGENT_KEY production --force --token "$VERCEL_TOKEN" --cwd "$WEB_DIR" >/dev/null
printf '%s' "$AGENT_ID" | npx vercel env add ORCAST_AGENT_REVIEWER_ID production --force --token "$VERCEL_TOKEN" --cwd "$WEB_DIR" >/dev/null
printf '%s' "$AGENT_EMAIL" | npx vercel env add ORCAST_AGENT_REVIEWER_EMAIL production --force --token "$VERCEL_TOKEN" --cwd "$WEB_DIR" >/dev/null

WORKOS_API_KEY="${WORKOS_API_KEY:-}"
if [ -z "$WORKOS_API_KEY" ]; then
  cd "$WEB_DIR"
  npx vercel env pull --yes --environment=production --token "$VERCEL_TOKEN" >/dev/null 2>&1 || true
  if [ -f .vercel/.env.production.local ]; then
    # shellcheck disable=SC1091
    source .vercel/.env.production.local
  fi
fi

WORKOS_USER_ID=""
if [ -n "${WORKOS_API_KEY:-}" ]; then
  echo "Ensuring WorkOS user $AGENT_EMAIL exists..."
  CREATE_RESP=$(curl -sS -w "\n%{http_code}" https://api.workos.com/user_management/users \
    -u "${WORKOS_API_KEY}:" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${AGENT_EMAIL}\",\"password\":\"${AGENT_PASSWORD}\",\"email_verified\":true,\"first_name\":\"Cursor\",\"last_name\":\"Agent\"}")
  HTTP_CODE=$(echo "$CREATE_RESP" | tail -n1)
  BODY=$(echo "$CREATE_RESP" | sed '$d')
  if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    WORKOS_USER_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
    echo "WorkOS user created: ${WORKOS_USER_ID:-$AGENT_EMAIL}"
  elif [ "$HTTP_CODE" = "409" ]; then
    echo "WorkOS user already exists for $AGENT_EMAIL (password not rotated)."
  else
    echo "WorkOS user create returned HTTP $HTTP_CODE (continuing with proxy agent key only):" >&2
    echo "$BODY" >&2
  fi
else
  echo "WORKOS_API_KEY not available — skipped WorkOS user (proxy agent key still works)."
fi

cat >"$CREDS_FILE" <<EOF
# ORCAST automation agent — gitignored. Do not commit.
ORCAST_AGENT_KEY=${ORCAST_AGENT_KEY}
ORCAST_AGENT_REVIEWER_ID=${AGENT_ID}
ORCAST_AGENT_REVIEWER_EMAIL=${AGENT_EMAIL}
ORCAST_WEB_BASE=https://orcast-h0.vercel.app
ORCAST_AGENT_PASSWORD=${AGENT_PASSWORD}
WORKOS_AGENT_USER_ID=${WORKOS_USER_ID}
EOF
chmod 600 "$CREDS_FILE"

echo ""
echo "Agent credentials written to $CREDS_FILE"
echo "Run: python3 tools/testing/agent_smoke.py"
echo "Optional browser login: $AGENT_EMAIL / (password in creds file)"

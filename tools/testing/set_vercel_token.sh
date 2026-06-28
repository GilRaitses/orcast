#!/usr/bin/env bash
# Securely store/rotate the Vercel deploy token in gitignored .agent-credentials.env.
# Paste the token when prompted and press Enter. Input is not echoed and never logged.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS="${REPO_ROOT}/.agent-credentials.env"

read -rs -p "Paste Vercel token, then press Enter: " TOKEN
echo

if [ -z "$TOKEN" ]; then
  echo "No token entered. Nothing changed." >&2
  exit 1
fi

touch "$CREDS"
# Upsert: drop any existing VERCEL_TOKEN line, then append the new one.
grep -v '^VERCEL_TOKEN=' "$CREDS" > "${CREDS}.tmp" || true
mv "${CREDS}.tmp" "$CREDS"
printf 'VERCEL_TOKEN=%s\n' "$TOKEN" >> "$CREDS"
chmod 600 "$CREDS"

echo "Saved VERCEL_TOKEN to ${CREDS} (gitignored, chmod 600)."
echo "The agent will read it from there to set ORCAST_STREAM_BASE and deploy orcast-h0."

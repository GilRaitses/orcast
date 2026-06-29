#!/usr/bin/env bash
# Securely store/rotate the Gemini API key in gitignored .agent-credentials.env.
# Paste the key when prompted and press Enter. Input is not echoed and never logged.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS="${REPO_ROOT}/.agent-credentials.env"

read -rs -p "Paste Gemini API key, then press Enter: " KEY
echo

if [ -z "$KEY" ]; then
  echo "No key entered. Nothing changed." >&2
  exit 1
fi

touch "$CREDS"
# Upsert: drop any existing GEMINI_API_KEY line, then append the new one.
grep -v '^GEMINI_API_KEY=' "$CREDS" > "${CREDS}.tmp" || true
mv "${CREDS}.tmp" "$CREDS"
printf 'GEMINI_API_KEY=%s\n' "$KEY" >> "$CREDS"
chmod 600 "$CREDS"

echo "Saved GEMINI_API_KEY to ${CREDS} (gitignored, chmod 600)."
echo "Test: python3 tools/testing/maps_grounding_probe.py"

#!/usr/bin/env bash
# Rotate the two exposed Google API keys after deleting/regenerating them in the
# Google Cloud console. Paste each NEW key when prompted; input is not echoed and
# is written only to the gitignored .agent-credentials.env (chmod 600).
#
# Rotate first in the browser window that just opened:
#   - Gemini (Generative Language) key: https://aistudio.google.com/app/apikey
#       or https://console.cloud.google.com/apis/credentials
#   - Maps key:                         https://console.cloud.google.com/apis/credentials
# Delete the OLD key, create a NEW one, then paste below.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS="${REPO_ROOT}/.agent-credentials.env"
touch "$CREDS"
chmod 600 "$CREDS"

upsert() { # $1=VAR $2=VALUE
  grep -v "^$1=" "$CREDS" > "${CREDS}.tmp" 2>/dev/null || true
  mv "${CREDS}.tmp" "$CREDS"
  printf '%s=%s\n' "$1" "$2" >> "$CREDS"
}

echo "== Rotate exposed Google API keys =="
echo "Leave a prompt blank and press Enter to skip that key."
echo

read -rs -p "Paste NEW Gemini API key, then Enter: " GEM; echo
if [ -n "${GEM:-}" ]; then upsert GEMINI_API_KEY "$GEM"; echo "  -> GEMINI_API_KEY updated."; else echo "  -> Gemini skipped."; fi

read -rs -p "Paste NEW Google Maps key, then Enter: " MAPS; echo
if [ -n "${MAPS:-}" ]; then upsert NEXT_PUBLIC_MAPS_KEY "$MAPS"; echo "  -> NEXT_PUBLIC_MAPS_KEY updated."; else echo "  -> Maps skipped."; fi

chmod 600 "$CREDS"
echo
echo "Saved to ${CREDS} (gitignored, chmod 600). You can close this window."

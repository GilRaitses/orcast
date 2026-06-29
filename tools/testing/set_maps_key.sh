#!/usr/bin/env bash
# Securely store/rotate the orcast Google Maps key in gitignored .agent-credentials.env.
# Paste the key when prompted and press Enter. Input is not echoed and never logged.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS="${REPO_ROOT}/.agent-credentials.env"

read -rs -p "Paste orcast Google Maps key (NEXT_PUBLIC_MAPS_KEY), then press Enter: " KEY
echo

if [ -z "$KEY" ]; then
  echo "No key entered. Nothing changed." >&2
  exit 1
fi

touch "$CREDS"
grep -v '^NEXT_PUBLIC_MAPS_KEY=' "$CREDS" > "${CREDS}.tmp" 2>/dev/null || true
mv "${CREDS}.tmp" "$CREDS"
printf 'NEXT_PUBLIC_MAPS_KEY=%s\n' "$KEY" >> "$CREDS"
chmod 600 "$CREDS"

echo "Saved NEXT_PUBLIC_MAPS_KEY to ${CREDS} (gitignored, chmod 600)."
echo "Tell the agent 'check' and it will push the key to Vercel prod env."

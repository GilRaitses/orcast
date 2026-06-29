#!/usr/bin/env bash
# Securely store/rotate the Emergent Mind API key in gitignored .agent-credentials.env.
# Paste the key when prompted and press Enter. Input is not echoed and never logged.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS="${REPO_ROOT}/.agent-credentials.env"

read -rs -p "Paste Emergent Mind API key, then press Enter: " KEY
echo

if [ -z "$KEY" ]; then
  echo "No key entered. Nothing changed." >&2
  exit 1
fi

touch "$CREDS"
grep -v '^EMERGENT_MIND_API_KEY=' "$CREDS" > "${CREDS}.tmp" || true
mv "${CREDS}.tmp" "$CREDS"
printf 'EMERGENT_MIND_API_KEY=%s\n' "$KEY" >> "$CREDS"
chmod 600 "$CREDS"

echo "Saved EMERGENT_MIND_API_KEY to ${CREDS} (gitignored, chmod 600)."
echo "Run research: python3 tools/testing/em_research.py"
echo "Run single family: python3 tools/testing/em_research.py --family SF-1"

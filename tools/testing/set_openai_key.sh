#!/usr/bin/env bash
# Securely store/rotate the OpenAI API key in gitignored .agent-credentials.env.
# Input is not echoed and never logged.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDS="${REPO_ROOT}/.agent-credentials.env"

read -rs -p "Paste OpenAI API key, then press Enter: " KEY
echo

if [ -z "$KEY" ]; then
  echo "No key entered. Nothing changed." >&2
  exit 1
fi

touch "$CREDS"
grep -v '^OPENAI_API_KEY=' "$CREDS" > "${CREDS}.tmp" || true
mv "${CREDS}.tmp" "$CREDS"
printf 'OPENAI_API_KEY=%s\n' "$KEY" >> "$CREDS"
chmod 600 "$CREDS"

echo "Saved OPENAI_API_KEY to ${CREDS} (gitignored, chmod 600)."
echo "Run TTS: python3 tools/testing/tts_narrate.py --voice-clone"

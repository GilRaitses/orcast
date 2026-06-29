#!/usr/bin/env bash
# Push NEXT_PUBLIC_MAPS_KEY to Vercel H0 and print GCP referrer checklist.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB_DIR="${REPO_ROOT}/web"
VERCEL_TOKEN="${VERCEL_TOKEN:-}"
MAPS_KEY="${NEXT_PUBLIC_MAPS_KEY:-GOOGLE_API_KEY_REDACTED}"

if [ -z "$VERCEL_TOKEN" ]; then
  echo "Set VERCEL_TOKEN to push NEXT_PUBLIC_MAPS_KEY to Vercel." >&2
  exit 1
fi

echo "Adding NEXT_PUBLIC_MAPS_KEY to Vercel production (orcast-h0)..."
printf '%s' "$MAPS_KEY" | npx vercel env add NEXT_PUBLIC_MAPS_KEY production --force --token "$VERCEL_TOKEN" --cwd "$WEB_DIR"

echo ""
echo "=== GCP Console checklist (required for maps on video beats) ==="
echo "1. Open https://console.cloud.google.com/apis/credentials"
echo "2. Select the Maps JavaScript API key matching NEXT_PUBLIC_MAPS_KEY"
echo "3. Application restrictions → HTTP referrers → add:"
echo "     https://orcast-h0.vercel.app/*"
echo "     https://*.vercel.app/*"
echo "     http://localhost:3000/*"
echo "4. Ensure Maps JavaScript API is enabled and billing is active"
echo ""
echo "Then redeploy H0 so the public env var is baked into the client bundle:"
echo "  cd web && npx vercel deploy --prod --token \"\$VERCEL_TOKEN\""
echo ""
echo "Verify: ./tools/waves/run-gate.sh a-maps"

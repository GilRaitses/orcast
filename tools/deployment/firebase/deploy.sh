#!/usr/bin/env bash
# Build Angular for Firebase hosting (orcast.org / orca-904de.web.app).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

bash scripts/inject-backend-url.sh

cd orcast-angular
npm ci
npm run build -- --configuration=firebase
cd "$ROOT"

if command -v firebase >/dev/null 2>&1; then
  firebase deploy --only hosting
  echo "Firebase hosting deployed (orcast.org when custom domain is connected)"
else
  echo "firebase CLI not found. Build output is in orcast-angular/dist/orcast-angular"
  echo "Install: npm install -g firebase-tools && firebase login"
  exit 1
fi

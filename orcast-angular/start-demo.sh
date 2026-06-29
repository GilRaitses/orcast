#!/usr/bin/env bash
# Start the orcast Angular pilot maps locally.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f package.json ]; then
  echo "Run from orcast-angular/"
  exit 1
fi

echo "Starting orcast pilot maps (reports, historical, plan)..."
npm install
ng serve --host 0.0.0.0 --port 4200 --open

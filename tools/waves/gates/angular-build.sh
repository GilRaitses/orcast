#!/usr/bin/env bash
# Angular aws configuration build (no deploy)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT/orcast-angular"

echo "== Angular build (aws configuration) =="
npm run build -- --configuration=aws

echo "Angular build gate: PASS"

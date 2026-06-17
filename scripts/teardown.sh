#!/usr/bin/env bash
# Tear down AWS ORCAST stack. Local demo/cache keeps working offline.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f demo/cache/manifest.json ]; then
  echo "==> No demo cache found — recording from local memory backend first"
  bash "$ROOT/scripts/rebuild.sh" --local-only
fi

echo "==> Tearing down AWS stack"
AWS_REGION="${AWS_REGION:-us-west-2}" bash tools/deployment/aws/teardown.sh

bash scripts/inject-backend-url.sh "http://127.0.0.1:8080"

echo ""
echo "AWS torn down. Self-contained demo still available:"
echo "  bash scripts/demo-start.sh        # cached API on :8080"
echo "  bash scripts/demo-start.sh --live # live memory backend on :8080"

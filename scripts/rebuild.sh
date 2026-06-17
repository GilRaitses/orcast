#!/usr/bin/env bash
# Rebuild ORCAST demo: AWS deploy OR local cache-only, always refresh demo/cache.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-aws}"  # aws | local

record_cache() {
  local url="$1"
  echo "==> Recording demo cache from $url"
  if [ -f "$ROOT/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$ROOT/.venv/bin/activate"
  fi
  python3 tools/demo/record_cache.py --base-url "$url"
}

if [ "$MODE" = "local" ] || [ "$MODE" = "--local-only" ]; then
  echo "==> Local rebuild (no AWS charges)"
  if [ -f "$ROOT/.venv/bin/activate" ]; then
    source "$ROOT/.venv/bin/activate"
  else
    python3 -m venv "$ROOT/.venv"
    source "$ROOT/.venv/bin/activate"
    pip install -q fastapi uvicorn boto3 requests
  fi
  ORCAST_STORAGE_BACKEND=memory ORCAST_ENV=local \
    python -m uvicorn src.aws_backend.main:app --host 127.0.0.1 --port 8080 &
  PID=$!
  trap 'kill $PID 2>/dev/null || true' EXIT
  sleep 2
  python3 tools/testing/test_aws_backend_smoke.py --base-url http://127.0.0.1:8080
  record_cache "http://127.0.0.1:8080"
  kill $PID 2>/dev/null || true
  trap - EXIT
  bash scripts/inject-backend-url.sh "http://127.0.0.1:8080"
  echo ""
  echo "Local demo cache ready. Start with: bash scripts/demo-start.sh"
  exit 0
fi

echo "==> AWS rebuild"
AWS_REGION="${AWS_REGION:-us-west-2}" bash tools/deployment/aws/deploy.sh

BACKEND_URL=$(python3 -c "import json; print(json.load(open('infra/aws/state/deployment-manifest.json'))['backend_url'])")
record_cache "$BACKEND_URL"
echo ""
echo "AWS demo rebuilt. URLs in infra/aws/state/deployment-manifest.json"
echo "Offline fallback cached in demo/cache/"

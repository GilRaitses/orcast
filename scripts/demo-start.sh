#!/usr/bin/env bash
# Start self-contained ORCAST demo (no AWS required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PID_FILE="$ROOT/demo/.demo-server.pid"
MODE="${1:-cached}"  # cached | live

stop_demo() {
  if [ -f "$PID_FILE" ]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
}

case "${1:-}" in
  stop)
    stop_demo
    echo "Demo server stopped."
    exit 0
    ;;
esac

stop_demo

if [ ! -f demo/cache/manifest.json ]; then
  echo "No demo cache — run: bash scripts/rebuild.sh --local-only"
  exit 1
fi

bash scripts/inject-backend-url.sh "http://127.0.0.1:8080"

if [ "$MODE" = "--live" ] || [ "$MODE" = "live" ]; then
  if [ -f "$ROOT/.venv/bin/activate" ]; then
    source "$ROOT/.venv/bin/activate"
  fi
  ORCAST_STORAGE_BACKEND=memory ORCAST_ENV=local \
    python -m uvicorn src.aws_backend.main:app --host 127.0.0.1 --port 8080 &
else
  python3 tools/demo/serve_cache.py &
fi

echo $! > "$PID_FILE"

echo ""
echo "ORCAST demo running at http://127.0.0.1:8080 ($MODE mode)"
echo "Angular:  cd orcast-angular && npm start"
echo "Reports:  http://localhost:4200/reports"
echo "Stop:     bash scripts/demo-start.sh stop"

#!/usr/bin/env bash
# A4/A5 composite gate — agent demo automation + video-complete
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

GATES="$ROOT/tools/waves/gates"

"$GATES/a-doc-grep.sh"
"$GATES/a-maps-smoke.sh"
python3 tools/testing/agent_smoke.py
"$GATES/h1-demo-walkthrough.sh"
"$GATES/a-video-gate.sh"

echo "A gate: PASS"

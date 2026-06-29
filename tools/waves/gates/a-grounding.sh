#!/usr/bin/env bash
# A-grounding gate — assert orcast uncited-evidence rate < Maps baseline (85%).
# Requires ORCAST_AGENT_KEY (from .agent-credentials.env) for the orcast check.
# GEMINI_API_KEY is optional — skipped if absent (CI-safe via --require-key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CREDS="${ROOT}/.agent-credentials.env"

if [ -f "$CREDS" ]; then
  # shellcheck disable=SC1090
  source "$CREDS"
fi

cd "$ROOT"

# Optional: refresh Maps baseline if Gemini key is present.
if [ -n "${GEMINI_API_KEY:-}" ]; then
  echo "GEMINI_API_KEY present — refreshing Maps baseline..."
  python3 tools/testing/maps_grounding_probe.py --case orca --json --write-baseline
else
  echo "GEMINI_API_KEY not set — skipping Maps baseline refresh (using cached 85%)."
fi

# Required: orcast-side grounding check.
if [ -z "${ORCAST_AGENT_KEY:-}" ]; then
  echo "FAIL: ORCAST_AGENT_KEY not set — run bash tools/testing/setup_agent_user.sh" >&2
  exit 1
fi

python3 tools/testing/maps_grounding_probe.py --orcast

echo "A grounding gate: PASS"

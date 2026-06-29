#!/usr/bin/env bash
# R-Echo — remediation campaign prod verification
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== R-Echo: I-suite =="
bash "$ROOT/tools/waves/gates/i-suite.sh"

echo "== R-Echo: H0 (without re-running full duplicate if nested) =="
bash "$ROOT/tools/waves/gates/h0-hackathon.sh"

echo "== R-Echo: P1 prod curl =="
bash "$ROOT/tools/waves/gates/p1-prod-curl.sh"

echo "R-Echo gate: PASS"

#!/usr/bin/env bash
# MLO-CI: run the MLM study ladder and enforce the honesty guard.
#
# This gate does NOT require the science gates (L0-L3) to pass; the model is honestly
# unvalidated today (effective confidence 0%). It enforces two things:
#   1. The study ladder runs cleanly (the harness is healthy).
#   2. Honesty guard: the served confidence must not exceed what the gates earned -- if
#      data/models/fit_report.json reports confidence > 0, the Level 2 joint gate MUST pass.
# Pure stdlib; uses system python3.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== MLM study ladder =="
python3 -m modeling.studies.run_studies

echo ""
echo "== Honesty guard (served confidence <= earned) =="
python3 - <<'PY'
import sys
from modeling.studies import level2_joint
from modeling.studies.common import load_fit_report, GATE_PASS

rep = load_fit_report() or {}
conf = rep.get("confidence", 0.0) or 0.0
l2 = level2_joint.run()
l2_pass = l2.status == GATE_PASS

print(f"served_confidence={conf} l2_gate={l2.status}")
if conf > 0.0 and not l2_pass:
    print("FAIL: served confidence > 0 but the Level 2 joint gate has not passed (unearned confidence).")
    sys.exit(1)
print("OK: served confidence is consistent with the gate ladder.")
PY

echo ""
echo "mlops-gate: ALL PASS"

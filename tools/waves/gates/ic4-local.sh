#!/usr/bin/env bash
# IC4 local gate — G5 remediation tests + doc grep + ic regression
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== IC4 local: gateDisplay logic =="
node --input-type=module <<'EOF'
import {
  cvDisplayStatus,
  computeCvDisplayPass,
} from "./web/lib/gateDisplay.ts";

const cases = [
  [{ gate_pass: true, mean_deviance_skill: -0.018 }, "caution"],
  [{ gate_pass: true, mean_deviance_skill: 0.12 }, "pass"],
  [{ gate_pass: false, mean_deviance_skill: 0.12 }, "fail"],
  [{ display_status: "caution", gate_pass: true }, "caution"],
];

for (const [input, expected] of cases) {
  const got = cvDisplayStatus(input);
  if (got !== expected) {
    console.error(`cvDisplayStatus(${JSON.stringify(input)}) = ${got}, expected ${expected}`);
    process.exit(1);
  }
}
if (computeCvDisplayPass({ gate_pass: true, mean_deviance_skill: -0.01 }) !== false) {
  process.exit(1);
}
console.log("gateDisplay: OK");
EOF

echo "== IC4 local: web tsc =="
(cd web && npx tsc --noEmit)

echo "== IC4 local: pytest (kernel + interactions) =="
PYTHONPATH=src python3 -m pytest \
  tests/aws_backend/test_kernel_serve.py \
  tests/aws_backend/test_interactions_router.py \
  tests/aws_backend/test_casting_policy.py \
  -q --tb=no

echo "== IC4 local: doc grep =="
bash "$ROOT/tools/waves/gates/ic4-doc-grep.sh"

echo "== IC4 local: ic regression =="
bash "$ROOT/tools/waves/gates/ic-local.sh"

echo "IC4 local: PASS"

#!/usr/bin/env bash
# Q1f — Whitepaper equation claims vs. code
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

fail=0
check() {
  if eval "$1" > /dev/null 2>&1; then
    echo "PASS E${3}: $2"
  else
    echo "FAIL E${3}: $2 — no code match"
    fail=1
  fi
}

echo "== Q1f: Whitepaper E1-E8 equation terms in code =="

# E1: PSTH kernel
check "test -f modeling/psth.py && grep -q 'psth\|PSTH' modeling/psth.py" \
  "E1 PSTH kernel — modeling/psth.py" 1

# E2: phase-shuffled null test
check "grep -rq 'phase_shuffle\|null_test\|level1_psth_phase_shuffle' modeling/fit_kernels.py" \
  "E2 phase-shuffle null — modeling/fit_kernels.py" 2

# E3: time-rescaling KS GoF
check "grep -rq 'time_rescaling\|kstest' modeling/fit_kernels.py" \
  "E3 time-rescaling KS — modeling/fit_kernels.py" 3

# E4: effective confidence function
check "grep -rq 'def effective_confidence\|effective_confidence' src/aws_backend/routers/kernel.py" \
  "E4 effective_confidence — src/aws_backend/routers/kernel.py" 4

# E5: deviance skill
check "grep -rq 'mean_deviance_skill\|deviance_skill' src/aws_backend/routers/kernel.py" \
  "E5 deviance skill — src/aws_backend/routers/kernel.py" 5

# E6: PIT calibration
check "grep -rq 'pit\b\|pit_calibrat\|PIT' modeling/fit_kernels.py" \
  "E6 PIT calibration — modeling/fit_kernels.py" 6

# E7: CMX graph — ProvenanceGraph renders C and M nodes
check "grep -q 'claim\|method\|M.*nodes\|C.*nodes\|buildMethodNodes\|buildClaimNodes' web/app/components/ProvenanceGraph.tsx" \
  "E7 C/M graph — web/app/components/ProvenanceGraph.tsx" 7

# E8: R_uncited grounding metric
check "grep -rq 'uncited\|R_uncited\|SCIENCE_MARKERS' tools/testing/maps_grounding_probe.py tools/testing/grounding_parallel_rag.py 2>/dev/null || false" \
  "E8 R_uncited — tools/testing/grounding_parallel_rag.py" 8

if [ "$fail" -ne 0 ]; then
  echo "Q1f: FAIL — missing equation grounding"
  exit 1
fi
echo "Q1f: PASS"

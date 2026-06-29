#!/usr/bin/env bash
# IC local gate — interaction steps, manifest-driven skills, policy tests
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== IC local: web tsc =="
(cd web && npx tsc --noEmit)

echo "== IC local: casting pytest =="
PYTHONPATH=src python3 -m pytest \
  tests/aws_backend/test_managed_agents_registry.py \
  tests/aws_backend/test_interactions_router.py \
  tests/aws_backend/test_casting_policy.py \
  tests/aws_backend/test_explore_router.py \
  -q --tb=no

echo "== IC local: manifest load =="
PYTHONPATH=src python3 - <<'PY'
from src.aws_backend.casting.manifest import enabled_skill_ids, load_manifest

manifest = load_manifest()
enabled = [s for s, spec in manifest.items() if spec.enabled]
public_enabled = [s for s in enabled if manifest[s].tier in ("T0", "T1")]
assert len(public_enabled) == 9, public_enabled
for sid in public_enabled:
    assert manifest[sid].enabled
    assert manifest[sid].tier in ("T0", "T1")
keyed_enabled = [s for s in enabled if manifest[s].tier in ("T2", "T3")]
assert len(keyed_enabled) == 6, keyed_enabled
reserved = [s for s, spec in manifest.items() if not spec.enabled]
print(f"public={len(public_enabled)} keyed={len(keyed_enabled)} reserved={len(reserved)}")
PY

echo "== IC local: no google imports in casting =="
if rg -i 'google|gemini|vertex' src/aws_backend/casting/ 2>/dev/null; then
  echo "FAIL: Google/Gemini references in casting package"
  exit 1
fi

echo "== IC local: doc grep =="
bash "$ROOT/tools/waves/gates/ic-doc-grep.sh"

echo "== IC local: M regression =="
bash "$ROOT/tools/waves/gates/m-local.sh"

echo "IC local: PASS"

#!/usr/bin/env bash
# IC6 local gate — surface planner, panel registry, T2 tier blocking on public routes
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== IC6 local: web tsc =="
(cd web && npx tsc --noEmit)

echo "== IC6 local: planner pytest =="
PYTHONPATH=src python3 -m pytest \
  tests/aws_backend/test_interactions_plan.py \
  tests/aws_backend/test_planner.py \
  tests/aws_backend/test_casting_policy.py \
  tests/aws_backend/test_interactions_router.py \
  -q --tb=no

echo "== IC6 local: panel registry =="
PYTHONPATH=src python3 - <<'PY'
from src.aws_backend.casting.panels import load_panel_registry, panel_ids

registry = load_panel_registry()
assert len(panel_ids()) >= 7
assert "map_viewport" in registry
assert "gates_summary" in registry
print(f"panels={len(registry)}")
PY

echo "== IC6 local: manifest tiers =="
PYTHONPATH=src python3 - <<'PY'
from src.aws_backend.casting.manifest import enabled_skill_ids, load_manifest

manifest = load_manifest()
public = [s for s in enabled_skill_ids() if manifest[s].tier in ("T0", "T1")]
keyed = [s for s in enabled_skill_ids() if manifest[s].tier in ("T2", "T3")]
assert len(public) == 9, public
assert len(keyed) == 6, keyed
print(f"public={len(public)} keyed={len(keyed)}")
PY

echo "== IC6 local: planner seed =="
PYTHONPATH=src python3 - <<'PY'
from src.aws_backend.casting.models import load_seed_agent

planner = load_seed_agent("surface-planner-v1")
assert planner.policy.planner_mode is True
assert "map_viewport" in planner.policy.allowed_panels
PY

echo "== IC6 local: ic regression =="
bash "$ROOT/tools/waves/gates/ic-local.sh"

echo "== IC6 local: doc grep =="
bash "$ROOT/tools/waves/gates/ic6-doc-grep.sh"

echo "IC6 local: PASS"

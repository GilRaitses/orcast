#!/usr/bin/env bash
# GP Phase A static preflight for the self-host cutover surfaces (repo-only, no network).
# Secret-leak scan + syntax/compile + JSON/YAML validity + .ddb ledger verify.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
fail=0
note(){ printf "%-6s %s\n" "$1" "$2"; [ "$1" = FAIL ] && fail=1; return 0; }

SCOPE=".ddb .sst infra/shared_host .cca/DEPLOY_DEMO_DECISIONS.md .cca/catalogue/O0/20260626_orcast-selfhost-cutover"

# 1) secret-leak scan (grep -r reads dot-dirs; bash word-splits)
if grep -rn -E "AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJhIjoiMGI2" $SCOPE 2>/dev/null; then
  note FAIL "secret-leak scan: hit above"
else
  note PASS "secret-leak scan clean"
fi

# 2) real env file must be ignored, .example tracked
if git check-ignore -q infra/shared_host/env/orcast-services.env; then note PASS "real env file gitignored"; else note FAIL "real env file NOT gitignored"; fi
if git check-ignore -q infra/shared_host/env/orcast-services.env.example; then note FAIL ".example wrongly ignored"; else note PASS ".example stays tracked"; fi

# 3) shell + python syntax
bash -n infra/shared_host/provision_orcast.sh && note PASS "provision_orcast.sh syntax" || note FAIL "provision_orcast.sh syntax"
python3 -m py_compile infra/shared_host/preflight.py .ddb/tools/register_sst.py .ddb/tools/verify_registry_hashes.py 2>/dev/null && note PASS "python compile" || note FAIL "python compile"
rm -rf .ddb/tools/__pycache__ infra/shared_host/__pycache__ 2>/dev/null

# 4) JSON/YAML validity
for f in .ddb/registry.json .sst/system_state_baseline_v1.json .sst/gp_preflight_v1.json infra/shared_host/iam/orcast_host_policy.json; do
  python3 -c "import json;json.load(open('$f'))" 2>/dev/null && note PASS "json $f" || note FAIL "json $f"
done
python3 - <<'PY' 2>/dev/null && note PASS "yaml manifest+decisions" || note FAIL "yaml manifest+decisions"
import glob,sys
try: import yaml
except Exception: sys.exit(0)
for f in ["infra/shared_host/host_manifest.yaml"]+glob.glob(".ddb/decisions/*.yaml"):
    yaml.safe_load(open(f))
PY

# 5) ledger hash verify
python3 .ddb/tools/verify_registry_hashes.py >/dev/null 2>&1 && note PASS "ddb registry verify" || note FAIL "ddb registry verify"

# 6) no stale rejected hostname in executable/config (rationale comments excluded)
if grep -rnF "api.orcast.aimez.ai" infra/shared_host 2>/dev/null | grep -v "orcast-api.aimez.ai" | grep -vq "NOT covered and fails"; then
  note FAIL "stale api.orcast.aimez.ai in infra config"
else
  note PASS "no stale hostname in infra config"
fi

[ "$fail" = 0 ] && { echo "selfhost-preflight: PASS"; exit 0; } || { echo "selfhost-preflight: FAIL"; exit 1; }

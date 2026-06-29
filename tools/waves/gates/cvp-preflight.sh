#!/usr/bin/env bash
# CVP (console-visual-pass) preflight — repo-local static battery PF-1..PF-6.
# Modeled on tools/waves/gates/selfhost-preflight.sh + the GP gap-register verdict format.
# Runs at W3 entry and before any commit. Always writes a JSON summary to the lane home
# gate_captures/cvp_preflight.json. Exits non-zero on any hard FAIL; SKIP never fails the build.
#
# Hard FAIL: tsc errors, invalid YAML, a leaked secret, a defect no longer present at the pin
# (plan-vs-reality broken), or a proven LGC/CXR boundary violation.
# SKIP: checks that only apply once W2/W3 produce edits, or that need absent dependencies.
#
# Env: CVP_STATIC=0 disables the heavy node checks (tsc/lint/test) for a fast dry run.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

LANE_HOME=".cca/catalogue/O0/20260628_console-visual-pass"
CAP_DIR="$LANE_HOME/gate_captures"
JSON="$CAP_DIR/cvp_preflight.json"
mkdir -p "$CAP_DIR"

PIN="97b6397"
HEAD_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

GLOBALS="web/app/globals.css"
ADAPT="web/app/components/AdaptiveExplore.tsx"
SCENE="web/app/components/scene/SalishScene.tsx"

pass=0; fail=0; skip=0
ITEMS=()

record(){ # id verdict detail
  local id="$1" v="$2" d="$3"
  printf "%-6s %-18s %s\n" "$v" "$id" "$d"
  case "$v" in
    PASS) pass=$((pass+1));;
    FAIL) fail=$((fail+1));;
    SKIP) skip=$((skip+1));;
  esac
  # detail is kept free of quotes/newlines so the JSON stays valid without escaping.
  ITEMS+=("{\"id\": \"$id\", \"verdict\": \"$v\", \"detail\": \"$d\"}")
}

echo "== CVP preflight (pin $PIN, HEAD $HEAD_SHA) =="

# ── Detect whether CVP has produced edits yet (gates PF-5) ────────────────────
HOT_DIFF="$(git diff "$PIN" -- "$GLOBALS" "$ADAPT" "$SCENE" 2>/dev/null || true)"
CVP_CHANGED=0
[ -n "$HOT_DIFF" ] && CVP_CHANGED=1
[ -d "web/lib/scene/markers" ] && CVP_CHANGED=1
ls web/app/styles/cvp-*.css >/dev/null 2>&1 && CVP_CHANGED=1

# ── PF-1 static ───────────────────────────────────────────────────────────────
# YAML validity (the machine files this lane owns + the edited registry).
yaml_ok=1
for f in "$LANE_HOME/wave_shape.yml" "docs/devpost/waves.registry.yaml"; do
  if python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" >/dev/null 2>&1; then
    record "PF-1.yaml:$(basename "$f")" PASS "valid YAML"
  else
    record "PF-1.yaml:$(basename "$f")" FAIL "invalid YAML"
    yaml_ok=0
  fi
done

if [ "${CVP_STATIC:-1}" = "0" ]; then
  record "PF-1.tsc"  SKIP "CVP_STATIC=0 (heavy node checks disabled for dry run)"
  record "PF-1.lint" SKIP "CVP_STATIC=0 (heavy node checks disabled for dry run)"
  record "PF-1.test" SKIP "CVP_STATIC=0 (heavy node checks disabled for dry run)"
elif [ -d web/node_modules ]; then
  ( cd web && npx --no-install tsc --noEmit ) >/dev/null 2>&1 \
    && record "PF-1.tsc" PASS "tsc --noEmit clean" \
    || record "PF-1.tsc" FAIL "tsc --noEmit reported errors"
  ( cd web && npx --no-install next lint ) >/dev/null 2>&1 \
    && record "PF-1.lint" PASS "next lint clean" \
    || record "PF-1.lint" FAIL "next lint reported problems"
  ( cd web && node --test "lib/**/*.test.mts" ) >/dev/null 2>&1 \
    && record "PF-1.test" PASS "node --test lib green" \
    || record "PF-1.test" FAIL "node --test lib reported failures"
else
  record "PF-1.tsc"  SKIP "web/node_modules absent (run npm ci in web/ first)"
  record "PF-1.lint" SKIP "web/node_modules absent (run npm ci in web/ first)"
  record "PF-1.test" SKIP "web/node_modules absent (run npm ci in web/ first)"
fi

record "PF-1.readlints" SKIP "ReadLints is an editor-run check; integrator records 0 on touched files"

# ── PF-2 secret-leak ────────────────────────────────────────────────────────────
SECRET_SCOPE="$LANE_HOME tools/waves/gates/cvp-preflight.sh"
[ -d web/lib/scene/markers ] && SECRET_SCOPE="$SECRET_SCOPE web/lib/scene/markers"
ls web/app/styles/cvp-*.css >/dev/null 2>&1 && SECRET_SCOPE="$SECRET_SCOPE web/app/styles"
# shellcheck disable=SC2086
if grep -rn -E "AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[0-9A-Za-z-]{10,}" $SECRET_SCOPE 2>/dev/null; then
  record "PF-2.secrets" FAIL "secret-leak scan: hit above"
else
  record "PF-2.secrets" PASS "secret-leak scan clean"
fi

# ── PF-3 plan-vs-reality (the 3 defects must still be present at the pin) ────────
if grep -Eq '\.chip[[:space:]]*\{' "$GLOBALS" 2>/dev/null; then
  record "PF-3.chip" FAIL "D1 gone: .chip rule now present in globals.css (built against stale state)"
else
  record "PF-3.chip" PASS "D1 present: no .chip rule in globals.css"
fi

if grep -q 'Ask about the Salish Sea' "$ADAPT" 2>/dev/null && grep -q 'rows={2}' "$ADAPT" 2>/dev/null; then
  record "PF-3.composer" PASS "D2 present: raw composer (Ask about the Salish Sea + rows={2})"
else
  record "PF-3.composer" FAIL "D2 gone: raw composer no longer matches AdaptiveExplore.tsx:335-343"
fi

if grep -Fq 'coneGeometry args={[1.6, 5, 6]}' "$SCENE" 2>/dev/null; then
  record "PF-3.beacon" PASS "D3 present: cone beacon coneGeometry args={[1.6, 5, 6]}"
else
  record "PF-3.beacon" FAIL "D3 gone: cone beacon no longer matches SalishScene.tsx:354-357"
fi

# ── PF-4 collision ───────────────────────────────────────────────────────────────
record "PF-4.rebase" SKIP "git pull --rebase is an operator action; run before W3 integrate"
DIRTY="$(git status --porcelain -- "$GLOBALS" "$ADAPT" "$SCENE" 2>/dev/null || true)"
if [ -z "$DIRTY" ]; then
  record "PF-4.worktree" PASS "3 hot files clean in the working tree (no concurrent hold)"
else
  record "PF-4.worktree" SKIP "hot file dirty in working tree; O0 must confirm the serialize order"
fi

# ── PF-5 boundary (only meaningful once CVP has produced edits) ──────────────────
if [ "$CVP_CHANGED" -eq 0 ]; then
  record "PF-5.tokens" SKIP "no CVP edits vs the pin yet; runs at W2/W3"
  record "PF-5.lgc"    SKIP "no CVP edits vs the pin yet; runs at W2/W3"
  record "PF-5.copy"   SKIP "no CVP edits vs the pin yet; runs at W2/W3"
else
  ADDED="$(printf '%s\n' "$HOT_DIFF" | grep -E '^\+' | grep -vE '^\+\+\+' || true)"
  if printf '%s\n' "$ADDED" | grep -Eq -- '--glass-|--text-ink'; then
    record "PF-5.tokens" FAIL "boundary violation: CVP diff adds an LGC token family (--glass-*/--text-ink)"
  else
    record "PF-5.tokens" PASS "CVP added no --glass-*/--text-ink token family"
  fi
  if printf '%s\n' "$ADDED" | grep -Eiq 'ghost-text|ghostText|self-hide|selfHide|consent.*preload'; then
    record "PF-5.lgc" FAIL "boundary violation: CVP diff adds ghost-text/self-hide/preload (LGC owns those)"
  else
    record "PF-5.lgc" PASS "CVP added no ghost-text/self-hide/preload"
  fi
  record "PF-5.copy" SKIP "style-only by charter; anonymous-path copy verified by cxr deny-terms + prose gate (PF-6)"
fi

# ── PF-6 prose gate (runs on W4 render captures) ─────────────────────────────────
record "PF-6.prose" SKIP "new copy clears prose gate + cxr deny-terms on W4 render captures; run tools/waves/gates/console-deny-terms.sh"

# ── verdict + JSON summary ───────────────────────────────────────────────────────
if [ "$fail" -eq 0 ]; then verdict="PASS"; else verdict="FAIL"; fi

{
  printf '{\n'
  printf '  "gate": "cvp-preflight",\n'
  printf '  "lane": "CVP",\n'
  printf '  "repo_state_verified_against": "%s",\n' "$PIN"
  printf '  "head": "%s",\n' "$HEAD_SHA"
  printf '  "generated_at": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '  "summary": {"pass": %d, "fail": %d, "skip": %d},\n' "$pass" "$fail" "$skip"
  printf '  "verdict": "%s",\n' "$verdict"
  printf '  "checks": [\n'
  n=${#ITEMS[@]}
  for i in "${!ITEMS[@]}"; do
    if [ "$i" -lt $((n-1)) ]; then sep=","; else sep=""; fi
    printf '    %s%s\n' "${ITEMS[$i]}" "$sep"
  done
  printf '  ]\n'
  printf '}\n'
} > "$JSON"

echo
echo "wrote $JSON (pass=$pass fail=$fail skip=$skip)"
[ "$fail" -eq 0 ] && { echo "cvp-preflight: PASS"; exit 0; } || { echo "cvp-preflight: FAIL"; exit 1; }

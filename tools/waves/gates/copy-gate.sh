#!/usr/bin/env bash
# orcast copy/prose gate. Enforces .cca/PROSE_GATE_RULES.md on user-facing and
# audience-facing copy. HARD-fails the unambiguous ornament patterns (em/en dash,
# arrows) and REPORTS the context-dependent ones (semicolons, colons, parentheses
# in prose, single-author voice, ', and', hedging, meta-framing) for review.
#
# Allowlist: .cca/prose_gate_allowlist.txt holds `path:line` or bare substrings to
# skip (strictly-required exceptions: machine colons, LaTeX/code syntax, etc).
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
ALLOW=".cca/prose_gate_allowlist.txt"
[ -f "$ALLOW" ] || ALLOW=/dev/null

# Surfaces. Class A frontend + class B docs/outreach. Backend prose strings are
# reported separately (mixed with docstrings) and triaged in the CX inventory.
# Audience-facing surfaces only (the prose-gate scope). Internal research notes,
# gap registers, and working charters are out of scope.
A_GLOBS=(web/app web/lib)
B_GLOBS=(
  docs/whitepaper/LX/Sections docs/whitepaper2/LX/Sections
  docs/devpost/submission/audit-deck/LX/Sections
  .cca/outreach_drafts docs/field-campaign/SUMMIT_DEMO_SCRIPT.md
  docs/devpost/DEMO_STORYBOARD.md docs/devpost/DEMO_NO_CRED_STORYBOARD.md
  docs/devpost/DEVPOST_DRAFT.md docs/devpost/SUBMISSION.md
)
EXT='--include=*.tsx --include=*.ts --include=*.md --include=*.tex --include=*.mdx'

scan() { # single fixed-string-or-BRE pattern
  grep -rIn $EXT -e "$1" "${A_GLOBS[@]}" "${B_GLOBS[@]}" 2>/dev/null \
    | grep -vF -f "$ALLOW" 2>/dev/null
}
count() { printf '%s' "$1" | grep -c . ; }

hard_fail=0
section() { echo; echo "== $1 =="; }

# HARD: em dash is the unambiguous prose ornament the gate enforces. en dash and
# arrows are REPORT (en dash has legit numeric ranges; => is JS syntax).
section "HARD: em dash (—)"
emd="$(scan '—')"; n_emd=$(count "$emd"); echo "count=$n_emd"; printf '%s\n' "$emd" | head -8
[ "$n_emd" -gt 0 ] && hard_fail=1

report() { local r; r="$(scan "$1")"; echo "$2: $(count "$r")"; }
section "REPORT (review in CX inventory; not auto-fail)"
report '–' "en-dash (incl legit numeric ranges)"
report '→' "unicode arrow"
report ';' "semicolons"
report ', and' "oxford-comma (, and)"
report '\bwe\b' "voice: we"
report '\bour\b' "voice: our"
report '\bmight\b\|\bcould\b\|\bseems\b' "hedging"
report 'In this section we\|We propose\|This paper contributes\|Our approach' "meta-framing"

# CXR-2: console deny-term grep against rendered anonymous-path captures. Runs as
# part of the copy-gate battery. Non-blocking when no captures are present, hard
# fail when a deny term is found in a captured anonymous render.
section "CXR-2: console deny-term grep (rendered anonymous path)"
deny_fail=0
if [ -x "$ROOT/tools/waves/gates/console-deny-terms.sh" ] || [ -f "$ROOT/tools/waves/gates/console-deny-terms.sh" ]; then
  if ! bash "$ROOT/tools/waves/gates/console-deny-terms.sh"; then
    deny_fail=1
  fi
fi

echo
if [ "$hard_fail" -ne 0 ] || [ "$deny_fail" -ne 0 ]; then
  [ "$hard_fail" -ne 0 ] && echo "copy-gate: FAIL ($n_emd em-dash in user-facing copy; replace with period/comma or restructure)"
  [ "$deny_fail" -ne 0 ] && echo "copy-gate: FAIL (console deny-term hit on the anonymous render path)"
  exit 1
fi
echo "copy-gate: PASS (no em-dash ornament, no console deny-term hits); review REPORT counts above for CX remediation"
exit 0

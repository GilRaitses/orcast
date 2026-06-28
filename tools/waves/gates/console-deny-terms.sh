#!/usr/bin/env bash
# orcast console deny-term gate (CXR-2). Greps RENDERED strings on the anonymous
# console path for internal / reviewer vocabulary that must never reach the
# public tier. Runs against captured render text (the gate_captures the accept
# step saves), so it checks what an anonymous visitor actually sees rather than
# source identifiers that live behind reviewer-only branches.
#
# Usage:
#   console-deny-terms.sh [path ...]
# Each path is a capture file or a directory of capture files. With no args it
# scans the CXR lane capture dir. Exit 1 on any hit, 0 otherwise. A run with no
# capture files present is a non-blocking PASS (so the copy-gate can call it
# before captures exist); pass --strict to fail when no captures are found.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DEFAULT_DIR="$ROOT/.cca/catalogue/O0/20260628_console-copy-redaction/gate_captures"

STRICT=0
PATHS=()
for arg in "$@"; do
  if [ "$arg" = "--strict" ]; then
    STRICT=1
  else
    PATHS+=("$arg")
  fi
done
[ "${#PATHS[@]}" -eq 0 ] && PATHS=("$DEFAULT_DIR")

# Deny terms (case-insensitive). Both the prose form and the code/underscore form
# are listed so a leaked identifier or a leaked phrase both fail.
DENY=(
  'promotion'
  'block promotion'
  'effective confidence'
  'effective_confidence'
  'ui_intent'
  'skill_plan'
  'managed agent'
  'managed_agent'
  'hydration_mode'
  'waveset'
  'adversarial'
)

# Build one alternation pattern for a single grep pass.
PATTERN="$(IFS='|'; echo "${DENY[*]}")"

# Collect candidate capture files.
FILES=()
for p in "${PATHS[@]}"; do
  if [ -f "$p" ]; then
    FILES+=("$p")
  elif [ -d "$p" ]; then
    # Scan render captures only. Skip gate-log artifacts (this gate echoes the
    # deny-term list, so its own logs must never be re-scanned and self-trip).
    while IFS= read -r f; do
      FILES+=("$f")
    done < <(find "$p" -type f \
      \( -name '*.txt' -o -name '*.html' -o -name '*.json' -o -name '*.md' \) \
      ! -name '*copy_gate*' ! -name '*deny*' ! -name '*battery*' ! -name '*gate_battery*' \
      2>/dev/null)
  fi
done

echo "== console deny-term gate =="
echo "terms: ${DENY[*]}"

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "no capture files found under: ${PATHS[*]}"
  if [ "$STRICT" -eq 1 ]; then
    echo "console-deny-terms: FAIL (no captures and --strict set)"
    exit 1
  fi
  echo "console-deny-terms: SKIP (no captures to scan; capture the anonymous render first)"
  exit 0
fi

echo "scanning ${#FILES[@]} capture file(s)"
hits="$(grep -inE "$PATTERN" "${FILES[@]}" 2>/dev/null)"
n=$(printf '%s' "$hits" | grep -c . )

if [ "$n" -gt 0 ]; then
  echo
  echo "$hits"
  echo
  echo "console-deny-terms: FAIL ($n deny-term hit(s) on the anonymous render path)"
  exit 1
fi

echo "console-deny-terms: PASS (0 deny-term hits across ${#FILES[@]} capture file(s))"
exit 0

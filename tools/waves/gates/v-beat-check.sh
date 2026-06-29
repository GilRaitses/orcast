#!/usr/bin/env bash
# V2 — Verify all per-beat webms exist and have expected minimum duration.
# Collects webms from Playwright e2e/.results/ into _demo-run/beats/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RESULTS_DIR="${ROOT}/web/e2e/.results"
BEATS_DIR="${ROOT}/docs/devpost/figures/_demo-run/beats"
mkdir -p "$BEATS_DIR"

fail=0
check() {
  if ! eval "$1"; then
    echo "FAIL: $2"
    fail=1
  fi
}

echo "Collecting beat webms from e2e/.results/..."
for slug in beat-01 beat-02 beat-03 beat-04 beat-05 beat-06-journal beat-06-moderation beat-07 beat-08; do
  SRC=$(find "$RESULTS_DIR" -path "*${slug}*" -name "video.webm" 2>/dev/null | head -1)
  DEST="${BEATS_DIR}/${slug}.webm"
  if [ -n "$SRC" ] && [ -f "$SRC" ]; then
    cp "$SRC" "$DEST"
    echo "  copied $slug"
  else
    echo "  WARN: no webm found for $slug"
  fi
done

echo "Verifying beat webms..."
for slug in beat-01 beat-02 beat-03 beat-04 beat-05 beat-06-journal beat-06-moderation beat-07 beat-08; do
  FILE="${BEATS_DIR}/${slug}.webm"
  check "test -f \"$FILE\"" "$slug.webm missing"
  if [ -f "$FILE" ]; then
    SIZE=$(wc -c < "$FILE")
    check "[ \"$SIZE\" -gt 50000 ]" "$slug.webm too small (${SIZE} bytes)"
    if command -v ffprobe >/dev/null 2>&1; then
      DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$FILE" 2>/dev/null | cut -d. -f1)
      check "[ \"${DUR:-0}\" -ge 5 ]" "$slug.webm too short (${DUR:-?}s)"
    fi
  fi
done

[ "$fail" -eq 0 ] && echo "V beat check: PASS (${BEATS_DIR})"
exit "$fail"

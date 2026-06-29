#!/usr/bin/env bash
# V3 — Stitch per-beat webms into demo-final.webm via ffmpeg concat.
# Requires ffmpeg. Beat webms must pass v-beat-check first.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BEATS_DIR="${ROOT}/docs/devpost/figures/_demo-run/beats"
OUT_DIR="${ROOT}/docs/devpost/figures/_demo-run"
CONCAT="${OUT_DIR}/concat.txt"
FINAL="${OUT_DIR}/demo-final.webm"

"${ROOT}/tools/waves/gates/v-beat-check.sh"

# Write concat list in storyboard order.
cat > "$CONCAT" << EOF
file '${BEATS_DIR}/beat-01.webm'
file '${BEATS_DIR}/beat-02.webm'
file '${BEATS_DIR}/beat-03.webm'
file '${BEATS_DIR}/beat-04.webm'
file '${BEATS_DIR}/beat-05.webm'
file '${BEATS_DIR}/beat-06-journal.webm'
file '${BEATS_DIR}/beat-06-moderation.webm'
file '${BEATS_DIR}/beat-07.webm'
file '${BEATS_DIR}/beat-08.webm'
EOF

echo "Stitching beats → $FINAL ..."
ffmpeg -y -f concat -safe 0 -i "$CONCAT" -c copy "$FINAL" 2>&1

if [ ! -f "$FINAL" ]; then
  echo "FAIL: $FINAL not produced" >&2
  exit 1
fi

SIZE=$(wc -c < "$FINAL")
if [ "$SIZE" -lt 5000000 ]; then
  echo "FAIL: demo-final.webm too small ($SIZE bytes)" >&2
  exit 1
fi

DUR=""
if command -v ffprobe >/dev/null 2>&1; then
  DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$FINAL" 2>/dev/null | cut -d. -f1)
  if [ "${DUR:-0}" -lt 150 ] || [ "${DUR:-0}" -gt 220 ]; then
    echo "WARN: demo-final.webm duration ${DUR}s — expected 150-220s"
  fi
  echo "Video duration: ${DUR}s"
fi

echo "V stitch: PASS ($FINAL, ${SIZE} bytes)"

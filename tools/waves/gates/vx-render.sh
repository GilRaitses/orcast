#!/usr/bin/env bash
# VX3 — Render voice-cloned beats: overlay cloned audio + drawtext title on each beat webm.
# Reads from narration/beat-NN-cloned.mp3; writes to beats-cloned/ + demo-final-cloned.webm
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BEATS_DIR="${ROOT}/docs/devpost/figures/_demo-run/beats"
NAR_DIR="${ROOT}/docs/devpost/figures/_demo-run/narration"
OUT_DIR="${ROOT}/docs/devpost/figures/_demo-run/beats-cloned"
FINAL="${ROOT}/docs/devpost/figures/_demo-run/demo-final-cloned.webm"
CONCAT="${ROOT}/docs/devpost/figures/_demo-run/concat-cloned.txt"

mkdir -p "$OUT_DIR"

get_title() {
  case "$1" in
    beat-01) echo "[PROBLEM] Evidence-bounded forecast" ;;
    beat-02) echo "[WORKING APP] Per-cell provenance" ;;
    beat-03) echo "[WORKING APP] Fitness gates + integrity" ;;
    beat-04) echo "[WORKING APP] Surface planner" ;;
    beat-05) echo "[WORKING APP] Sighting check" ;;
    beat-06-journal) echo "[DATABASE] Field journal" ;;
    beat-06-moderation) echo "[DATABASE] Decision record" ;;
    beat-07) echo "[DATABASE] Nine DynamoDB tables" ;;
    beat-08) echo "orcast — use it. defend it." ;;
    *) echo "$1" ;;
  esac
}

SLUGS=(beat-01 beat-02 beat-03 beat-04 beat-05 beat-06-journal beat-06-moderation beat-07 beat-08)

echo "Rendering voice-cloned beat videos..."
for slug in "${SLUGS[@]}"; do
  VIDEO="${BEATS_DIR}/${slug}.webm"
  AUDIO="${NAR_DIR}/${slug}-cloned.mp3"
  OUT="${OUT_DIR}/${slug}.webm"
  TITLE=$(get_title "$slug")

  if [ ! -f "$VIDEO" ]; then
    echo "  SKIP $slug: no beat webm"
    continue
  fi
  if [ ! -f "$AUDIO" ]; then
    echo "  SKIP $slug: no cloned narration mp3 — run python3 tools/testing/tts_clone.py first"
    continue
  fi

  TITLE_ESC="${TITLE//:/\\:}"

  echo "  rendering $slug..."
  ffmpeg -y \
    -i "$VIDEO" \
    -i "$AUDIO" \
    -filter_complex \
      "[0:v]drawtext=\
text='${TITLE_ESC}':\
fontsize=28:\
fontcolor=white:\
x=40:\
y=h-60:\
box=1:\
boxcolor=black@0.6:\
boxborderw=8[v]" \
    -map "[v]" \
    -map "1:a" \
    -c:v libvpx \
    -b:v 800k \
    -c:a libvorbis \
    -shortest \
    "$OUT" 2>/dev/null && echo "    OK: $OUT" || echo "    FAIL: $slug"
done

> "$CONCAT"
for slug in "${SLUGS[@]}"; do
  OUT="${OUT_DIR}/${slug}.webm"
  [ -f "$OUT" ] && echo "file '${OUT}'" >> "$CONCAT"
done

if [ ! -s "$CONCAT" ]; then
  echo "FAIL: no cloned beats produced" >&2
  exit 1
fi

echo "Stitching cloned beats → $FINAL ..."
ffmpeg -y -f concat -safe 0 -i "$CONCAT" -c copy "$FINAL" 2>/dev/null

SIZE=$(wc -c < "$FINAL")
DUR=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$FINAL" 2>/dev/null | cut -d. -f1)

echo "VX render: PASS"
echo "  ${FINAL}"
echo "  Duration: ${DUR}s   Size: $((SIZE / 1024 / 1024))MB"

#!/usr/bin/env bash
# V4 — Render narrated beat videos: overlay TTS audio + drawtext title on each beat webm.
# Requires: ffmpeg, narration mp3s from tts_narrate.py
# Output: _demo-run/beats-narrated/beat-NN.webm (audio + title)
# Then concatenates to demo-final-narrated.webm
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BEATS_DIR="${ROOT}/docs/devpost/figures/_demo-run/beats"
NAR_DIR="${ROOT}/docs/devpost/figures/_demo-run/narration"
OUT_DIR="${ROOT}/docs/devpost/figures/_demo-run/beats-narrated"
FINAL="${ROOT}/docs/devpost/figures/_demo-run/demo-final-narrated.webm"
CONCAT="${ROOT}/docs/devpost/figures/_demo-run/concat-narrated.txt"

mkdir -p "$OUT_DIR"

# Title map: slug → display text (must match tts_narrate.py TITLES)
declare_titles() {
  echo "beat-01:[PROBLEM] Evidence-bounded forecast"
  echo "beat-02:[WORKING APP] Per-cell provenance"
  echo "beat-03:[WORKING APP] Fitness gates + integrity"
  echo "beat-04:[WORKING APP] Surface planner"
  echo "beat-05:[WORKING APP] Sighting check"
  echo "beat-06-journal:[DATABASE] Field journal"
  echo "beat-06-moderation:[DATABASE] Decision record"
  echo "beat-07:[DATABASE] Nine DynamoDB tables"
  echo "beat-08:orcast — use it. defend it."
}

get_title() {
  declare_titles | grep "^${1}:" | cut -d: -f2-
}

SLUGS=(beat-01 beat-02 beat-03 beat-04 beat-05 beat-06-journal beat-06-moderation beat-07 beat-08)

echo "Rendering narrated beat videos..."
for slug in "${SLUGS[@]}"; do
  VIDEO="${BEATS_DIR}/${slug}.webm"
  AUDIO="${NAR_DIR}/${slug}.mp3"
  OUT="${OUT_DIR}/${slug}.webm"
  TITLE=$(get_title "$slug")

  if [ ! -f "$VIDEO" ]; then
    echo "  SKIP $slug: no beat webm"
    continue
  fi
  if [ ! -f "$AUDIO" ]; then
    echo "  SKIP $slug: no narration mp3 (run python3 tools/testing/tts_narrate.py first)"
    continue
  fi

  # Escape special chars in title for ffmpeg drawtext
  TITLE_ESC="${TITLE//:/\\:}"
  TITLE_ESC="${TITLE_ESC//'/\\'}"

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

# Write concat list
> "$CONCAT"
for slug in "${SLUGS[@]}"; do
  OUT="${OUT_DIR}/${slug}.webm"
  [ -f "$OUT" ] && echo "file '${OUT}'" >> "$CONCAT"
done

if [ ! -s "$CONCAT" ]; then
  echo "FAIL: no narrated beats produced" >&2
  exit 1
fi

echo "Stitching narrated beats → $FINAL ..."
ffmpeg -y -f concat -safe 0 -i "$CONCAT" -c copy "$FINAL" 2>/dev/null

SIZE=$(wc -c < "$FINAL")
DUR=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$FINAL" 2>/dev/null | cut -d. -f1)

echo "V render: PASS"
echo "  ${FINAL}"
echo "  Duration: ${DUR}s   Size: $((SIZE/1024/1024))MB"

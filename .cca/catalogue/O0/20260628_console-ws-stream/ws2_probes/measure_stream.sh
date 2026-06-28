#!/usr/bin/env bash
# WS2 measurement harness — curl variant (quick visual check).
#
# PURPOSE
#   Fast, dependency-free incremental-vs-buffered check using curl --no-buffer -N.
#   Prints each line with a millisecond client timestamp prefix so you can SEE
#   whether `event: token` lines trickle in (unbuffered) or all land at once
#   (buffered). Use measure_stream.mjs for the machine-readable JSON the report
#   cites; use this for a fast eyeball and to confirm headers.
#
# USAGE
#   ./measure_stream.sh <url> [GET|POST]
#   examples:
#     ./measure_stream.sh http://127.0.0.1:8099/__stream_probe
#     ./measure_stream.sh https://orcast-api.aimez.ai/__stream_probe
#     ./measure_stream.sh https://<preview>.vercel.app/api/__streamprobe POST
#
# WHAT TO LOOK FOR
#   - Response headers must include: content-type: text/event-stream,
#     cache-control: no-cache, no-transform, x-accel-buffering: no.
#   - token lines should appear ~150 ms apart (the probe interval). If they all
#     appear together after a multi-second pause, a layer buffered.

set -u
URL="${1:?usage: measure_stream.sh <url> [GET|POST]}"
METHOD="${2:-GET}"

echo "== headers ==" >&2
if [ "$METHOD" = "POST" ]; then
  curl -sS -D - -o /dev/null -X POST -H 'Content-Type: application/json' \
    -H 'Accept: text/event-stream' --data '{"probe":true}' "$URL" >&2 || true
else
  curl -sS -D - -o /dev/null -H 'Accept: text/event-stream' "$URL" >&2 || true
fi

echo "== stream (ms-prefixed) ==" >&2
START_NS=$(date +%s%N)
CURL_ARGS=(--no-buffer -N -sS -H 'Accept: text/event-stream')
if [ "$METHOD" = "POST" ]; then
  CURL_ARGS+=(-X POST -H 'Content-Type: application/json' --data '{"probe":true}')
fi

# Prefix each output line with elapsed milliseconds since request start.
curl "${CURL_ARGS[@]}" "$URL" | while IFS= read -r line; do
  NOW_NS=$(date +%s%N)
  ELAPSED_MS=$(( (NOW_NS - START_NS) / 1000000 ))
  printf '%6d ms | %s\n' "$ELAPSED_MS" "$line"
done

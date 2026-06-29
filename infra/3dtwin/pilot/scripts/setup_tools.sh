#!/usr/bin/env bash
# setup_tools.sh — one-time install of the node toolchain into the pilot work dir.
# Pins the CesiumGS tiles tooling + gltfpack into ~/3dtwin/pilot/work/node_modules so the
# pipeline can invoke them from the node:20 container without reinstalling each run.
set -euo pipefail
ROOT="${ROOT:-$HOME/3dtwin/pilot}"
WORK="$ROOT/work"
mkdir -p "$WORK"
cd "$WORK"
[ -f package.json ] || echo '{ "name": "orcast-3dtwin-pilot", "version": "1.0.0", "private": true }' > package.json
sudo docker run --rm --platform linux/amd64 -v "$WORK":/work -w /work node:20-bookworm \
  npm install --no-audit --no-fund gltfpack 3d-tiles-tools 3d-tiles-validator
echo "installed:"
sudo docker run --rm --platform linux/amd64 -v "$WORK":/work -w /work node:20-bookworm bash -c \
  './node_modules/.bin/gltfpack -h 2>&1 | head -1; npx 3d-tiles-validator --version 2>&1 | tail -1'

#!/usr/bin/env bash
# Fetch Orca Strike assets from orcast main into ./public/ (run from game project root).
# m4a is gitignored on GitHub — operator must attach separately (see BASH_TV_OPERATOR_ATTACH.md).

set -euo pipefail
BASE="https://raw.githubusercontent.com/GilRaitses/orcast/main"

mkdir -p public/orca/motion public/hydrophone/slice

echo "Fetching orca.glb..."
curl -fsSL "$BASE/web/public/orca/orca.glb" -o public/orca/orca.glb

echo "Fetching DTAG driver..."
curl -fsSL "$BASE/web/public/orca/motion/orca_srkw_oo14_driver.json" -o public/orca/motion/orca_srkw_oo14_driver.json
curl -fsSL "$BASE/web/public/orca/motion/orca_srkw_oo14_driver.bin" -o public/orca/motion/orca_srkw_oo14_driver.bin

echo "Fetching hydrophone classifications..."
curl -fsSL "$BASE/web/public/hydrophone/slice/classification.json" -o public/hydrophone/slice/classification.json

if [[ ! -f public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a ]]; then
  echo "MISSING: public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a"
  echo "Operator must attach this file (not on GitHub). See BASH_TV_OPERATOR_ATTACH.md"
  exit 1
fi

echo "OK: all required assets present."
ls -la public/orca/orca.glb public/orca/motion/orca_srkw_oo14_driver.* public/hydrophone/slice/

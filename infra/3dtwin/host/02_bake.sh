#!/usr/bin/env bash
# Step 2: bake full_utm.tif into an OGC 3D Tiles 1.1 LoD quadtree (glb tiles + tileset.json).
# Runs bake_tree.py inside the GDAL container (osgeo.gdal + numpy). Output under tileset/.
# Run on the EC2 host: `bash 02_bake.sh`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/env.sh"
cd "${WORKDIR}"

if [ ! -s full_utm.tif ]; then
  echo "ERROR: full_utm.tif not found - run 01_fetch_reproject.sh first" >&2
  exit 1
fi

sudo rm -rf tileset   # docker writes root-owned files; sudo to clean
mkdir -p tileset
echo "=== Baking LoD quadtree (LMAX=${LMAX}) ==="
gdal python3 /data/bake_tree.py /data/full_utm.tif /data/tileset --lmax "${LMAX}"

echo
echo "=== Baked tree ==="
echo "tiles: $(ls tileset/tiles/*.glb 2>/dev/null | wc -l)"
du -sh tileset

#!/usr/bin/env bash
# Shared configuration for the orcast 3dtwin FULL-extent batch conversion.
# Wave 2, agent batch-conversion. Runs on the aimez-services EC2 (x86_64 / Ubuntu)
# using native linux/amd64 docker images. No emulation. Source it: `source env.sh`.
#
# Provenance: this reproduces agent B's EXACT CUDEM reproject method
# (infra/3dtwin/reproject/env.sh + 01_/02_) over the FULL study bbox. Same source
# (NOAA NCEI CUDEM 1/9" topobathy, `wash_bellingham`, 4 tiles), same datum
# (NAVD88 m, preserved with NO vertical shift), same target CRS (EPSG:32610).
# It is NOT a different datum/source: B staged only the pilot window to S3, so the
# full-extent reprojected raster is regenerated here with B's identical pipeline.

set -euo pipefail

# --- GDAL container (pinned, native x86_64; ships python3 + osgeo.gdal + numpy) ---
export GDAL_IMAGE="ghcr.io/osgeo/gdal:ubuntu-small-3.8.5"
export NODE_IMAGE="node:20-bookworm"
export AWS_IMAGE="amazon/aws-cli:latest"

# --- Remote workdir on the EC2 host (own ONLY this dir) ---
export WORKDIR="${WORKDIR:-$HOME/3dtwin/host}"
export TILES_DIR="${WORKDIR}/tiles"

# --- Study extent: SAN_JUAN_BOUNDS (src/aws_backend/geo_region.py) ---
export BBOX_W=-123.25
export BBOX_E=-122.75
export BBOX_S=48.40
export BBOX_N=48.70

# --- CRS / datum (identical to agent B) ---
export SRC_HCRS="EPSG:4269"        # NAD83 geographic (horizontal)
export TARGET_CRS="EPSG:32610"     # WGS84 / UTM zone 10N, metres
export NODATA=-9999

# --- Base ground resolution of the reprojected raster (metres). Matches B's pilot. ---
export MESH_TR=10

# --- LoD hierarchy depth. LMAX=3 => 4 levels (root + 3); 8x8 leaves at full 10 m. ---
export LMAX=3

# --- NOAA NCEI CUDEM 1/9 arc-second topobathy, public S3 mirror (anonymous HTTPS) ---
export CUDEM_BASE="https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/NCEI_ninth_Topobathy_2014_8483/wash_bellingham"

# The four tiles that fully tile SAN_JUAN_BOUNDS (B's proven 100% coverage set):
export CUDEM_TILES=(
  "ncei19_n48x50_w123x25_2024v1.tif"  # lat 48.25-48.50, lng -123.25 .. -123.00
  "ncei19_n48x50_w123x00_2024v1.tif"  # lat 48.25-48.50, lng -123.00 .. -122.75
  "ncei19_n48x75_w123x25_2024v1.tif"  # lat 48.50-48.75, lng -123.25 .. -123.00
  "ncei19_n48x75_w123x00_2017v1.tif"  # lat 48.50-48.75, lng -123.00 .. -122.75
)
# If already fetched by agent B's pilot run, reuse from the reproject workdir.
export REPROJECT_DIR="${HOME}/3dtwin/reproject"

# --- S3 staging (account 198456344617, us-east-1) ---
export S3_PREFIX="s3://aimez-data/3dtwin/full"
export CF_BASE="https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full"

# --- docker run helpers ---
gdal() {
  sudo docker run --rm -i -v "${WORKDIR}:/data" -w /data "${GDAL_IMAGE}" "$@"
}
# gdal helper that can also see the reproject dir (read cached source tiles)
gdal_ro() {
  sudo docker run --rm -i -v "${WORKDIR}:/data" -v "${REPROJECT_DIR}:/src:ro" -w /data "${GDAL_IMAGE}" "$@"
}
export -f gdal gdal_ro

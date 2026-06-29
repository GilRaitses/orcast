#!/usr/bin/env bash
# Shared configuration for the orcast terrain+bathymetry reproject+mesh pipeline.
# Wave 1, agent B. Runs on the aimez-services EC2 (x86_64) using native linux/amd64
# GDAL docker images. No emulation. Source it: `source env.sh`.

set -euo pipefail

# --- GDAL container (pinned for reproducibility; native x86_64) ---
# 3.8.5 ships python3 + osgeo.gdal + numpy and is already cached on the host.
export GDAL_IMAGE="ghcr.io/osgeo/gdal:ubuntu-small-3.8.5"

# --- Remote workdir on the EC2 host (do NOT use ~/bakeoff or ~/borough) ---
export WORKDIR="${WORKDIR:-$HOME/3dtwin/reproject}"

# --- Study extent: SAN_JUAN_BOUNDS (src/aws_backend/geo_region.py) ---
export BBOX_W=-123.25
export BBOX_E=-122.75
export BBOX_S=48.40
export BBOX_N=48.70

# --- Pilot coastal chunk (land+sea+shoreline: west San Juan Island + Haro Strait) ---
# Chosen inside a 2024 COMPOUND-tagged tile so the source explicitly declares NAVD88
# height (EPSG:5498), making the vertical-datum-preservation proof unambiguous. Also
# abuts the Canadian border (Haro Strait), the coverage region the charter asked to check.
export PILOT_W=-123.20
export PILOT_E=-123.05
export PILOT_S=48.55
export PILOT_N=48.65

# --- CRS / datum ---
# Source CUDEM: COMPOUND EPSG:5498 = NAD83 (EPSG:4269) horizontal + NAVD88 height vertical.
export SRC_HCRS="EPSG:4269"        # NAD83 geographic (horizontal)
export TARGET_CRS="EPSG:32610"     # WGS84 / UTM zone 10N, metres
export NODATA=-9999

# --- Mesh decimation: target ground resolution of the reprojected raster (metres) ---
# Native CUDEM posting is 1/9 arc-second (~3.4 m). 10 m gives a clean pilot mesh.
export MESH_TR=10

# --- NOAA NCEI CUDEM 1/9 arc-second topobathy, public S3 mirror (anonymous HTTP) ---
# CORRECTION vs decision record: the San Juan bbox (lat 48.40-48.70) is covered by the
# `wash_bellingham` collection, NOT `wash_pugetsound` (whose northernmost NW-corner tile
# is n48x25, i.e. coverage <= lat 48.25). Tiles are named by their NW corner; each spans
# 0.25 deg: tile nAAxBB_wCCxDD covers lat [AA.BB-0.25, AA.BB], lng [-CC.DD, -CC.DD+0.25].
export CUDEM_BASE="https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/NCEI_ninth_Topobathy_2014_8483/wash_bellingham"

# The four tiles that fully tile the study bbox:
export CUDEM_TILES=(
  "ncei19_n48x50_w123x25_2024v1.tif"  # lat 48.25-48.50, lng -123.25 .. -123.00
  "ncei19_n48x50_w123x00_2024v1.tif"  # lat 48.25-48.50, lng -123.00 .. -122.75
  "ncei19_n48x75_w123x25_2024v1.tif"  # lat 48.50-48.75, lng -123.25 .. -123.00
  "ncei19_n48x75_w123x00_2017v1.tif"  # lat 48.50-48.75, lng -123.00 .. -122.75
)

# The single tile the pilot window falls inside (2024, COMPOUND EPSG:5498 = NAD83 + NAVD88 height):
export PILOT_TILE="ncei19_n48x75_w123x25_2024v1.tif"

# --- S3 staging (account 198456344617, us-east-1) ---
export S3_PREFIX="s3://aimez-data/3dtwin/reproject"

# --- docker run helper: mount WORKDIR at /data, run as the GDAL container ---
# -i keeps stdin open so tools that read stdin (e.g. gdaltransform) work via pipes.
gdal() {
  sudo docker run --rm -i -v "${WORKDIR}:/data" -w /data "${GDAL_IMAGE}" "$@"
}
export -f gdal

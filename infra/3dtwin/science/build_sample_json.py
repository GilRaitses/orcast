#!/usr/bin/env python3
"""Build a BathymetryAdapter-compatible sample from the CUDEM depth XYZ dump.

Input : out/depth_sanjuan_cudem.xyz  (rows "lon lat value", value = NAVD88 m,
        positive up, -9999 = nodata)
Output: sample_san_juan_bathymetry_cudem.json

Format mirrors data/geo/san_juan_bathymetry.json exactly:
    {"source","dataset","bounds","resolution_deg","points":[{lat,lng,depth_m}]}
depth_m follows the adapter convention: NEGATIVE below sea level, POSITIVE land.
CUDEM elevation is already positive-up NAVD88 m, so depth_m == elevation (no flip).

MODELED, NOT MEASURED — derived from the NOAA NCEI CUDEM 1/9 topobathy surface,
the same integrated geometry slated to feed the render tiles. NAVD88 ≈ local mean
sea level here within ~1 m; treated as the sea-level reference for sign.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
XYZ = HERE / "out" / "depth_sanjuan_cudem.xyz"
OUT = HERE / "sample_san_juan_bathymetry_cudem.json"

NODATA = -9999.0
RES_DEG = float(sys.argv[1]) if len(sys.argv) > 1 else 0.005
BOUNDS = {"min_lat": 48.40, "max_lat": 48.70, "min_lng": -123.25, "max_lng": -122.75}

PROVENANCE = (
    "MODELED, NOT MEASURED. Depth field rasterized from NOAA NCEI CUDEM 1/9 "
    "arc-second topobathy (wash_bellingham collection), the integrated "
    "land+seafloor surface that also feeds the 3D render tiles — one geometry, "
    "no second pipeline. Native vertical datum NAVD88 metres (positive up); "
    "NAVD88 treated as the sea-level reference for the negative-below-sea-level "
    "sign convention (NAVD88 differs from local MSL/MLLW by ~1 m here, "
    "unmodeled). Horizontal NAD83 (EPSG:4269) warped to WGS84 (EPSG:4326), "
    "~1-2 m shift, negligible at this grid spacing. Aggregated to "
    f"{RES_DEG} deg cells with GDAL -r average; supersedes the ETOPO1 "
    "1-arc-minute provenance of data/geo/san_juan_bathymetry.json."
)


def main() -> int:
    if not XYZ.exists():
        print(f"ERROR: {XYZ} not found; run rasterize_depth.sh first", file=sys.stderr)
        return 1

    points = []
    n_total = n_nodata = 0
    with XYZ.open("r", encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 3:
                continue
            n_total += 1
            lng, lat, val = float(parts[0]), float(parts[1]), float(parts[2])
            if not math.isfinite(val) or abs(val - NODATA) < 0.5:
                n_nodata += 1
                continue
            points.append(
                {"lat": round(lat, 6), "lng": round(lng, 6), "depth_m": round(val, 1)}
            )

    doc = {
        "source": (
            "https://coast.noaa.gov/htdata/raster2/elevation/"
            "NCEI_ninth_Topobathy_2014_8483/wash_bellingham/ (CUDEM 1/9 arc-sec topobathy)"
        ),
        "dataset": (
            "NOAA NCEI CUDEM 1/9 arc-second topobathic-topographic DEM, "
            "wash_bellingham; integrated bathymetry+topography; vertical NAVD88 m "
            "(EPSG:5703), horizontal NAD83 (EPSG:4269) -> WGS84 (EPSG:4326)"
        ),
        "bounds": BOUNDS,
        "resolution_deg": RES_DEG,
        "provenance": PROVENANCE,
        "modeled_not_measured": True,
        "points": points,
    }

    OUT.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")

    depths = [p["depth_m"] for p in points]
    print(f"rows_read={n_total} nodata_skipped={n_nodata} points={len(points)}")
    if depths:
        print(
            f"depth_m min={min(depths)} max={max(depths)} "
            f"sample_first={points[0]} sample_last={points[-1]}"
        )
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

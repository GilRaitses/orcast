#!/usr/bin/env python3
"""Ingest proof: run the REAL BathymetryAdapter against the CUDEM sample.

Confirms the existing science consumer (src/aws_backend/sources/bathymetry.py)
ingests the modeled CUDEM depth field with no code change: load(), depth_at()
for in-bbox coords, and summary(). Pure-python, no AWS needed.

Run from anywhere:  python3 infra/3dtwin/science/ingest_proof.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]  # infra/3dtwin/science -> repo root
SAMPLE = HERE / "sample_san_juan_bathymetry_cudem.json"

# Make `aws_backend` importable from src/ (mirrors the backend's own layout).
sys.path.insert(0, str(REPO / "src"))

from aws_backend.sources.bathymetry import BathymetryAdapter  # noqa: E402

# In-bbox probe coordinates (lat, lng, what we expect by eye).
PROBES = [
    (48.55, -123.20, "Haro Strait channel (deep water, strongly negative)"),
    (48.45, -122.95, "San Juan Channel / S of Shaw (water, negative)"),
    (48.53, -123.05, "near San Juan Island shore (mixed, shallow)"),
    (48.68, -122.85, "Orcas Is. / Mt Constitution upland (land, positive)"),
    (48.50, -123.00, "bbox interior"),
    (48.40, -122.75, "bbox SE corner"),
]


def main() -> int:
    print(f"adapter sample : {SAMPLE}")
    print(f"exists         : {SAMPLE.exists()}")
    adapter = BathymetryAdapter(asset_path=SAMPLE)

    pts = adapter.load()
    print(f"\nload()         : {len(pts)} points")
    print(f"  first        : {pts[0] if pts else None}")
    print(f"  last         : {pts[-1] if pts else None}")

    print("\ndepth_at(lat, lng)  [m, NEGATIVE below sea level, POSITIVE land]:")
    for lat, lng, note in PROBES:
        d = adapter.depth_at(lat, lng)
        print(f"  ({lat:>7.3f}, {lng:>8.3f}) -> {d!s:>8}  m   # {note}")

    # Out-of-bbox should still return the nearest edge point (adapter is nearest-
    # neighbour, no bounds gate) — show it degrades sanely, and None on non-finite.
    print("\nedge / robustness:")
    print(f"  depth_at(0,0)            -> {adapter.depth_at(0, 0)}   (nearest edge pt, expected)")
    print(f"  depth_at(nan, -123.0)    -> {adapter.depth_at(float('nan'), -123.0)}   (None expected)")

    print("\nsummary():")
    for k, v in adapter.summary().items():
        print(f"  {k:14}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

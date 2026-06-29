#!/usr/bin/env python3
"""Fidelity probe for the bake-off.

Builds an LOD reconstruction of the source DEM at a target vertex budget
(decimate-then-upsample), writes it as a GeoTIFF aligned to the source grid,
and reports the vertical RMSE / max error vs the source over valid cells.
This approximates the fidelity of a decimated mesh tile at that vertex budget.

Also prints the analytic vertical quantization step for the two encodings,
computed from the measured Z range:
  - Draco position quant (14-bit default): rangeZ / 2**14
  - quantized-mesh height (16-bit per-tile): rangeZ / 32767 (whole-chunk bound)

Env:
  IN_TIF       source DEM (default /data/in/pilot_utm.tif)
  OUT_RECON    LOD recon GeoTIFF (default /data/logs/lod_recon.tif)
  TARGET_VERTS approx vertex budget for the LOD (default 18782 = optimized glb)
"""
import os
import numpy as np
import rasterio
from rasterio.enums import Resampling

IN_TIF = os.environ.get("IN_TIF", "/data/in/pilot_utm.tif")
OUT_RECON = os.environ.get("OUT_RECON", "/data/logs/lod_recon.tif")
TARGET_VERTS = int(os.environ.get("TARGET_VERTS", "18782"))

with rasterio.open(IN_TIF) as ds:
    src = ds.read(1).astype(np.float64)
    nodata = ds.nodata if ds.nodata is not None else -9999.0
    profile = ds.profile
    rows, cols = src.shape

valid = src != nodata
zvals = src[valid]
zmin, zmax = float(zvals.min()), float(zvals.max())
zrange = zmax - zmin

# pick a stride so that (rows/s)*(cols/s) ~= TARGET_VERTS
import math
s = max(1, int(round(math.sqrt(rows * cols / max(1, TARGET_VERTS)))))
small = src[::s, ::s]
# upsample back to full grid (bilinear) via rasterio-less numpy: use kron-ish
from numpy import repeat
up = np.repeat(np.repeat(small, s, axis=0), s, axis=1)[:rows, :cols]
# pad if short
if up.shape != src.shape:
    pad = np.full(src.shape, nodata, dtype=np.float64)
    pad[:up.shape[0], :up.shape[1]] = up
    up = pad

both = valid & (up != nodata)
err = (up[both] - src[both])
rmse = float(np.sqrt(np.mean(err ** 2)))
maxerr = float(np.max(np.abs(err)))
approx_verts = small.shape[0] * small.shape[1]

prof = profile.copy()
prof.update(dtype="float32", count=1, nodata=nodata)
os.makedirs(os.path.dirname(OUT_RECON), exist_ok=True)
with rasterio.open(OUT_RECON, "w", **prof) as dst:
    dst.write(up.astype("float32"), 1)

print(f"z_range_m={zrange:.3f} (min={zmin:.2f} max={zmax:.2f})")
print(f"lod_stride={s} lod_grid={small.shape[0]}x{small.shape[1]} approx_verts={approx_verts}")
print(f"lod_vs_source RMSE_m={rmse:.4f} maxerr_m={maxerr:.4f}")
print(f"draco14bit_vstep_m={zrange/(2**14):.5f}")
print(f"qmesh16bit_vstep_m={zrange/32767.0:.6f}")

#!/usr/bin/env python3
"""Triangulate an integrated topobathy DEM into a clean mesh.

Reads a single-band GeoTIFF (expected EPSG:32610, vertical NAVD88 m), builds a
regular-grid triangle mesh skipping NoData cells, and writes a binary little-endian
PLY plus a sidecar JSON describing the CRS / datum / local frame for downstream
consumers (tiler agent C, science agent F).

Vertices are written in a LOCAL metric frame: X = easting - origin_e,
Y = northing - origin_n, Z = NAVD88 metres (absolute, not offset). The UTM origin
is recorded in the sidecar so the geometry georeferences back exactly (no drift).

Run inside the GDAL container, e.g.:
  docker run --rm -v $PWD:/data -w /data ghcr.io/osgeo/gdal:ubuntu-small-3.8.5 \
      python3 /data/mesh_dem.py pilot_utm.tif pilot_mesh.ply --stride 1
"""
import argparse
import json
import struct
import sys

import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="input GeoTIFF (projected, metres)")
    ap.add_argument("dst", help="output PLY path")
    ap.add_argument("--stride", type=int, default=1,
                    help="additional integer decimation on top of raster resolution")
    args = ap.parse_args()

    ds = gdal.Open(args.src, gdal.GA_ReadOnly)
    if ds is None:
        print(f"ERROR: cannot open {args.src}", file=sys.stderr)
        return 2
    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gt = ds.GetGeoTransform()
    if gt[2] != 0 or gt[4] != 0:
        print("ERROR: rotated geotransforms are not supported", file=sys.stderr)
        return 2

    arr = band.ReadAsArray().astype(np.float64)
    if args.stride > 1:
        arr = arr[:: args.stride, :: args.stride]
    h, w = arr.shape
    res_x = gt[1] * args.stride
    res_y = gt[5] * args.stride  # negative (north-up)

    # Pixel-centre planar coordinates (UTM metres).
    cols = np.arange(w)
    rows = np.arange(h)
    x_centres = gt[0] + (cols + 0.5) * res_x
    y_centres = gt[3] + (rows + 0.5) * res_y
    origin_e = float(x_centres.min())
    origin_n = float(y_centres.min())

    valid = np.ones_like(arr, dtype=bool)
    if nodata is not None:
        valid &= arr != nodata
    valid &= np.isfinite(arr)

    # Stable vertex indices for valid cells.
    vid = np.full((h, w), -1, dtype=np.int64)
    n_vert = int(valid.sum())
    vid[valid] = np.arange(n_vert, dtype=np.int64)

    rr, cc = np.nonzero(valid)
    vx = (x_centres[cc] - origin_e).astype(np.float32)
    vy = (y_centres[rr] - origin_n).astype(np.float32)
    vz = arr[rr, cc].astype(np.float32)

    # Two triangles per quad whose four corners are all valid.
    v00 = valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, :-1] & valid[1:, 1:]
    qr, qc = np.nonzero(v00)
    i00 = vid[qr, qc]
    i01 = vid[qr, qc + 1]
    i10 = vid[qr + 1, qc]
    i11 = vid[qr + 1, qc + 1]
    # CCW seen from +Z (above), with Y increasing northward.
    tris_a = np.stack([i00, i10, i11], axis=1)
    tris_b = np.stack([i00, i11, i01], axis=1)
    tris = np.concatenate([tris_a, tris_b], axis=0).astype(np.int32)
    n_tri = tris.shape[0]

    with open(args.dst, "wb") as f:
        header = (
            "ply\n"
            "format binary_little_endian 1.0\n"
            "comment orcast 3dtwin integrated topobathy mesh (modeled, not measured)\n"
            "comment crs EPSG:32610 vertical NAVD88 metres\n"
            f"comment local_frame origin_easting={origin_e:.3f} origin_northing={origin_n:.3f}\n"
            f"element vertex {n_vert}\n"
            "property float x\nproperty float y\nproperty float z\n"
            f"element face {n_tri}\n"
            "property list uchar int vertex_indices\n"
            "end_header\n"
        )
        f.write(header.encode("ascii"))
        verts = np.empty((n_vert, 3), dtype="<f4")
        verts[:, 0] = vx
        verts[:, 1] = vy
        verts[:, 2] = vz
        f.write(verts.tobytes())
        face_buf = bytearray()
        pack = struct.Struct("<Biii").pack
        for t in tris:
            face_buf += pack(3, int(t[0]), int(t[1]), int(t[2]))
        f.write(face_buf)

    sr = osr.SpatialReference()
    sr.ImportFromWkt(ds.GetProjection())
    epsg = sr.GetAuthorityCode(None)

    meta = {
        "format": "PLY (binary_little_endian)",
        "crs": f"EPSG:{epsg}" if epsg else ds.GetProjection(),
        "units": "metres",
        "vertical_datum": "NAVD88 metres (orthometric height; below 0 = below NAVD88 geoid)",
        "local_frame": {
            "x": "easting_m - origin_easting",
            "y": "northing_m - origin_northing",
            "z": "NAVD88 m (absolute, not offset)",
            "origin_easting": round(origin_e, 3),
            "origin_northing": round(origin_n, 3),
        },
        "resolution_m": abs(res_x),
        "n_vertices": n_vert,
        "n_triangles": n_tri,
        "z_min_navd88_m": float(np.nanmin(vz)) if n_vert else None,
        "z_max_navd88_m": float(np.nanmax(vz)) if n_vert else None,
        "bbox_utm_m": {
            "min_easting": round(float(x_centres.min()), 3),
            "max_easting": round(float(x_centres.max()), 3),
            "min_northing": round(float(y_centres.min()), 3),
            "max_northing": round(float(y_centres.max()), 3),
        },
        "provenance": "NOAA NCEI CUDEM 1/9 arc-second topobathy, wash_bellingham; "
                      "reprojected NAD83->EPSG:32610, NAVD88 m preserved. Modeled, not measured.",
    }
    with open(args.dst.rsplit(".", 1)[0] + ".meta.json", "w") as mf:
        json.dump(meta, mf, indent=2)

    print(json.dumps({"n_vertices": n_vert, "n_triangles": n_tri,
                      "resolution_m": abs(res_x),
                      "z_min": meta["z_min_navd88_m"], "z_max": meta["z_max_navd88_m"],
                      "origin_easting": round(origin_e, 3),
                      "origin_northing": round(origin_n, 3)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

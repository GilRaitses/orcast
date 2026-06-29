#!/usr/bin/env python3
"""
dem_to_glb.py — turn a reprojected DEM GeoTIFF into a binary glTF (.glb) grid mesh.

Reads a single-band elevation GeoTIFF (expected EPSG:32610 / UTM 10N, meters,
elevation in meters). Emits one Y-up glTF mesh in a LOCAL engineering frame
centered on the DEM centroid:

  glTF  X = easting  - centroid_easting   (meters)
  glTF  Y = elevation                     (meters, true scale, no exaggeration)
  glTF  Z = -(northing - centroid_north)  (meters; negated so that the built-in
            3D Tiles glTF y-up -> z-up transform maps +north to tiles +Y)

The mesh is a regular triangulated grid (one vertex per pixel center). Vertex
normals are computed and oriented to face up (+Y). No textures; vertex geometry
only — colour/shading is the renderer's job.

Pure stdlib + numpy + GDAL. No pygltflib dependency (self-contained glb writer).

Usage:
  dem_to_glb.py <in_dem.tif> <out.glb> [--stride N]
"""
import sys
import json
import struct
import argparse
import numpy as np
from osgeo import gdal

gdal.UseExceptions()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_tif")
    ap.add_argument("out_glb")
    ap.add_argument("--stride", type=int, default=1,
                    help="decimation stride over the grid (1 = full resolution)")
    args = ap.parse_args()

    ds = gdal.Open(args.in_tif)
    if ds is None:
        sys.exit(f"cannot open {args.in_tif}")
    band = ds.GetRasterBand(1)
    gt = ds.GetGeoTransform()  # (ox, px, 0, oy, 0, py)
    ox, px, _, oy, _, py = gt
    nodata = band.GetNoDataValue()

    arr = band.ReadAsArray().astype(np.float64)
    if args.stride > 1:
        arr = arr[:: args.stride, :: args.stride]
        px *= args.stride
        py *= args.stride
    H, W = arr.shape

    # Fill nodata / NaN (GMRT leaves NaN floats) so the mesh is closed and valid.
    mask = ~np.isfinite(arr)
    if nodata is not None:
        mask |= arr == nodata
    if mask.any():
        if (~mask).any():
            fill = float(arr[~mask].mean())
        else:
            fill = 0.0
        arr[mask] = fill

    # Pixel-center coordinates in projected meters.
    j = np.arange(W)
    i = np.arange(H)
    east = ox + (j + 0.5) * px          # shape (W,)
    north = oy + (i + 0.5) * py         # shape (H,) ; py is negative

    cx = float(east.mean())
    cy = float(north.mean())

    EAST, NORTH = np.meshgrid(east, north)   # (H, W)
    X = (EAST - cx).astype(np.float32)
    Y = arr.astype(np.float32)
    Z = (-(NORTH - cy)).astype(np.float32)

    positions = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)  # (H*W, 3)

    # Triangle indices over the grid.
    idx = np.arange(H * W).reshape(H, W)
    v00 = idx[:-1, :-1].ravel()
    v01 = idx[:-1, 1:].ravel()
    v10 = idx[1:, :-1].ravel()
    v11 = idx[1:, 1:].ravel()
    tri_a = np.stack([v00, v10, v01], axis=-1)
    tri_b = np.stack([v01, v10, v11], axis=-1)
    indices = np.concatenate([tri_a, tri_b], axis=0).reshape(-1).astype(np.uint32)

    # Vertex normals (area-weighted accumulation of face normals).
    normals = np.zeros((H * W, 3), dtype=np.float64)
    tris = indices.reshape(-1, 3)
    p0 = positions[tris[:, 0]]
    p1 = positions[tris[:, 1]]
    p2 = positions[tris[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    for k in range(3):
        np.add.at(normals, tris[:, k], fn)
    # Orient up: a terrain heightfield should have normals with +Y on average.
    if normals[:, 1].sum() < 0:
        indices = indices.reshape(-1, 3)[:, ::-1].reshape(-1).copy()
        normals = -normals
    lens = np.linalg.norm(normals, axis=1)
    lens[lens == 0] = 1.0
    normals = (normals / lens[:, None]).astype(np.float32)

    write_glb(args.out_glb, positions.astype(np.float32), normals, indices)

    pmin = positions.min(axis=0)
    pmax = positions.max(axis=0)
    summary = {
        "in_tif": args.in_tif,
        "out_glb": args.out_glb,
        "grid": [int(W), int(H)],
        "vertices": int(H * W),
        "triangles": int(len(indices) // 3),
        "centroid_utm10n": [cx, cy],
        "local_bbox_min": [float(v) for v in pmin],
        "local_bbox_max": [float(v) for v in pmax],
        "elev_min_m": float(Y.min()),
        "elev_max_m": float(Y.max()),
    }
    print(json.dumps(summary, indent=2))
    with open(args.out_glb + ".bounds.json", "w") as f:
        json.dump(summary, f, indent=2)


def write_glb(path, positions, normals, indices):
    """Write a minimal valid glTF 2.0 binary container."""
    pos_bytes = positions.tobytes()
    nrm_bytes = normals.tobytes()
    idx_bytes = indices.tobytes()

    def pad4(b, fill=b"\x00"):
        r = (4 - (len(b) % 4)) % 4
        return b + fill * r

    pos_off = 0
    nrm_off = pos_off + len(pos_bytes)
    idx_off = nrm_off + len(nrm_bytes)
    bin_blob = pos_bytes + nrm_bytes + idx_bytes
    bin_blob = pad4(bin_blob)

    pmin = positions.min(axis=0).tolist()
    pmax = positions.max(axis=0).tolist()

    gltf = {
        "asset": {"version": "2.0", "generator": "orcast dem_to_glb.py"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 2,
                "mode": 4,
            }]
        }],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_off, "byteLength": len(pos_bytes),
             "target": 34962},
            {"buffer": 0, "byteOffset": nrm_off, "byteLength": len(nrm_bytes),
             "target": 34962},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx_bytes),
             "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(positions),
             "type": "VEC3", "min": pmin, "max": pmax},
            {"bufferView": 1, "componentType": 5126, "count": len(normals),
             "type": "VEC3"},
            {"bufferView": 2, "componentType": 5125, "count": len(indices),
             "type": "SCALAR"},
        ],
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes = pad4(json_bytes, b" ")

    total = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    with open(path, "wb") as f:
        f.write(b"glTF")
        f.write(struct.pack("<I", 2))
        f.write(struct.pack("<I", total))
        f.write(struct.pack("<I", len(json_bytes)))
        f.write(b"JSON")
        f.write(json_bytes)
        f.write(struct.pack("<I", len(bin_blob)))
        f.write(b"BIN\x00")
        f.write(bin_blob)


if __name__ == "__main__":
    main()

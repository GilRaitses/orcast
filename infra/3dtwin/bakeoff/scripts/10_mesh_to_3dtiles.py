#!/usr/bin/env python3
"""Candidate 1: meshed-surface -> OGC 3D Tiles 1.1 (glTF).

Reads a single-band DEM (NAVD88 m, projected metric CRS), builds a regular
triangulated grid mesh in a LOCAL engineering frame (XY centred on the tile
centroid, Y = elevation so the glTF is Y-up), skips triangles that touch
NoData, writes a binary glTF (.glb), and wraps it in a minimal 3D Tiles 1.1
tileset.json whose root content is the .glb.

The local-frame origin offset (UTM easting/northing of the tile centroid) is
written into the tileset `asset.extras` and printed, so Wave 2 can place the
tile in the SalishScene local frame.

Env:
  IN_TIF      input DEM (default /data/in/pilot_utm.tif)
  OUT_DIR     output dir   (default /data/mesh3dtiles)
  STRIDE      grid decimation factor, int >=1 (default 1 = full resolution)
"""
import json
import os
import struct
import numpy as np
import rasterio

IN_TIF = os.environ.get("IN_TIF", "/data/in/pilot_utm.tif")
OUT_DIR = os.environ.get("OUT_DIR", "/data/mesh3dtiles")
STRIDE = max(1, int(os.environ.get("STRIDE", "1")))
os.makedirs(OUT_DIR, exist_ok=True)


def build():
    with rasterio.open(IN_TIF) as ds:
        band = ds.read(1).astype(np.float64)
        nodata = ds.nodata if ds.nodata is not None else -9999.0
        tr = ds.transform
        px, py = tr.a, tr.e  # py is negative (north-up)
        ox, oy = tr.c, tr.f  # upper-left corner UTM

    z = band[::STRIDE, ::STRIDE]
    rows, cols = z.shape
    # UTM coords of each sampled node (cell-corner sampling)
    xs = ox + (np.arange(cols) * STRIDE) * px
    ys = oy + (np.arange(rows) * STRIDE) * py
    cx = float((xs.min() + xs.max()) / 2.0)
    cy = float((ys.min() + ys.max()) / 2.0)

    # local frame: x=east-cx, z=-(north-cy) (so +Y is up, right-handed Y-up)
    X = (xs - cx)[None, :].repeat(rows, axis=0)
    Zn = (ys - cy)[:, None].repeat(cols, axis=1)
    valid = z != nodata
    # vertex array; invalid heights set to 0 but referenced only if all-4 valid
    Yv = np.where(valid, z, 0.0)

    verts = np.empty((rows * cols, 3), dtype=np.float32)
    verts[:, 0] = X.reshape(-1)
    verts[:, 1] = Yv.reshape(-1)
    verts[:, 2] = (-Zn).reshape(-1)

    def vid(r, c):
        return r * cols + c

    # two triangles per cell, only if all 4 corners valid
    faces = []
    v = valid
    r0 = np.arange(rows - 1)
    c0 = np.arange(cols - 1)
    RR, CC = np.meshgrid(r0, c0, indexing="ij")
    cell_ok = v[:-1, :-1] & v[:-1, 1:] & v[1:, :-1] & v[1:, 1:]
    rr = RR[cell_ok]
    cc = CC[cell_ok]
    tl = rr * cols + cc
    tr_ = tl + 1
    bl = tl + cols
    br = bl + 1
    # winding for Y-up, viewed from +Y
    f1 = np.stack([tl, bl, tr_], axis=1)
    f2 = np.stack([tr_, bl, br], axis=1)
    faces = np.concatenate([f1, f2], axis=0).astype(np.uint32)

    # drop unreferenced vertices to keep the glb tight
    used = np.unique(faces.reshape(-1))
    remap = np.full(verts.shape[0], -1, dtype=np.int64)
    remap[used] = np.arange(used.shape[0])
    verts = verts[used]
    faces = remap[faces].astype(np.uint32)

    # per-vertex normals
    normals = np.zeros_like(verts)
    a = verts[faces[:, 0]]
    b = verts[faces[:, 1]]
    c = verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    for i in range(3):
        np.add.at(normals, faces[:, i], fn)
    ln = np.linalg.norm(normals, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    normals = (normals / ln).astype(np.float32)

    write_glb(os.path.join(OUT_DIR, "pilot.glb"), verts, normals, faces)
    write_tileset(OUT_DIR, verts, cx, cy)
    print(f"vertices={verts.shape[0]} triangles={faces.shape[0]} "
          f"stride={STRIDE} rows={rows} cols={cols} "
          f"centroid_utm=({cx:.3f},{cy:.3f})")


def write_glb(path, verts, normals, faces):
    pos = verts.astype("<f4").tobytes()
    nor = normals.astype("<f4").tobytes()
    idx = faces.reshape(-1).astype("<u4").tobytes()

    def pad4(b, fill=b"\x00"):
        r = (-len(b)) % 4
        return b + fill * r

    pos = pad4(pos)
    nor = pad4(nor)
    idx = pad4(idx)
    bin_blob = pos + nor + idx
    pmin = verts.min(axis=0).tolist()
    pmax = verts.max(axis=0).tolist()

    gltf = {
        "asset": {"version": "2.0", "generator": "orcast-bakeoff mesh->3dtiles"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1},
            "indices": 2, "mode": 4}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(verts),
             "type": "VEC3", "min": pmin, "max": pmax},
            {"bufferView": 1, "componentType": 5126, "count": len(verts),
             "type": "VEC3"},
            {"bufferView": 2, "componentType": 5125,
             "count": faces.size, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos), "target": 34962},
            {"buffer": 0, "byteOffset": len(pos), "byteLength": len(nor), "target": 34962},
            {"buffer": 0, "byteOffset": len(pos) + len(nor), "byteLength": len(idx), "target": 34963},
        ],
        "buffers": [{"byteLength": len(bin_blob)}],
    }
    json_blob = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_blob = json_blob + b" " * ((-len(json_blob)) % 4)
    total = 12 + 8 + len(json_blob) + 8 + len(bin_blob)
    with open(path, "wb") as f:
        f.write(b"glTF")
        f.write(struct.pack("<II", 2, total))
        f.write(struct.pack("<I", len(json_blob)))
        f.write(b"JSON")
        f.write(json_blob)
        f.write(struct.pack("<I", len(bin_blob)))
        f.write(b"BIN\x00")
        f.write(bin_blob)


def write_tileset(out_dir, verts, cx, cy):
    pmin = verts.min(axis=0)
    pmax = verts.max(axis=0)
    center = ((pmin + pmax) / 2.0).tolist()
    half = ((pmax - pmin) / 2.0)
    # 3D Tiles oriented bounding box: [cx,cy,cz, hx,0,0, 0,hy,0, 0,0,hz]
    box = [center[0], center[1], center[2],
           float(half[0]), 0, 0,
           0, float(half[1]), 0,
           0, 0, float(half[2])]
    diag = float(np.linalg.norm(pmax - pmin))
    tileset = {
        "asset": {
            "version": "1.1",
            "extras": {
                "orcast": {
                    "frame": "local-engineering, Y-up, Y=NAVD88 m",
                    "utm_crs": "EPSG:32610",
                    "local_origin_utm_xy": [cx, cy],
                    "note": "stand-in pilot clipped from CUDEM (see BAKEOFF.md)",
                }
            },
        },
        "geometricError": diag,
        "root": {
            "boundingVolume": {"box": box},
            "geometricError": 0,
            "refine": "REPLACE",
            "content": {"uri": "pilot.glb"},
        },
    }
    with open(os.path.join(out_dir, "tileset.json"), "w") as f:
        json.dump(tileset, f, indent=2)


if __name__ == "__main__":
    build()

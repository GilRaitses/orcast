#!/usr/bin/env python3
"""
bake_tree.py - bake a reprojected topobathy DEM into an OGC 3D Tiles 1.1 LoD quadtree.

Input:  a single-band EPSG:32610 / NAVD88 m GeoTIFF (agent B's reproject, full extent).
Output: <out>/tileset.json  +  <out>/tiles/L{level}_{ix}_{iy}.glb  (one glb per tile)

LoD design (REPLACE refinement quadtree, depth = LMAX):
  - level 0 (root): the whole extent decimated by stride 2^LMAX  (coarsest)
  - level L:        a 2^L x 2^L grid; each tile decimated by stride 2^(LMAX-L)
  - level LMAX:     leaves at full resolution (stride 1)
  Each tile renders to a ~constant vertex budget (full_dim / 2^LMAX per side), so the
  cost per tile is bounded; the renderer loads EITHER coarse parents OR fine leaves.

Geometry (reuses agent D's dem_to_glb / make_tileset mapping exactly):
  glTF (Y-up), ONE shared local engineering frame centered on the full-extent centroid:
      glTF X = easting  - cx        (m)
      glTF Y = NAVD88 elevation     (m, true scale, no exaggeration)
      glTF Z = -(northing - cy)     (m; negated so 3D Tiles' built-in y-up->z-up maps +N to +Y)
  3D Tiles applies the glTF y-up->z-up transform, so each tile's boundingVolume.box
  is in the z-up tile frame:
      tile.X =  gltf.X            tile.Y = -gltf.Z            tile.Z = gltf.Y
  Boxes use the tile's GEOMETRIC window extent horizontally (child windows nest exactly
  inside parent windows) and the GLOBAL elevation range vertically, which guarantees
  child boundingVolume is contained in the parent's and that content fits the box.

NoData cells are SKIPPED (no fake fill), matching mesh_dem.py / the served pilot bake.
Vertices in local metres, true 1:1 scale, NAVD88 m. Modeled, not measured.

Usage: bake_tree.py <full_utm.tif> <out_dir> [--lmax 3] [--margin 1.02]
"""
import argparse
import json
import os
import struct
import sys

import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()


def write_glb(path, positions, normals, indices):
    """Minimal valid glTF 2.0 binary container (POSITION + NORMAL + indices)."""
    pos_bytes = positions.astype("<f4").tobytes()
    nrm_bytes = normals.astype("<f4").tobytes()
    idx_bytes = indices.astype("<u4").tobytes()

    def pad4(b, fill=b"\x00"):
        return b + fill * ((4 - (len(b) % 4)) % 4)

    pos_off = 0
    nrm_off = pos_off + len(pos_bytes)
    idx_off = nrm_off + len(nrm_bytes)
    bin_blob = pad4(pos_bytes + nrm_bytes + idx_bytes)

    pmin = positions.min(axis=0).tolist()
    pmax = positions.max(axis=0).tolist()

    gltf = {
        "asset": {"version": "2.0", "generator": "orcast bake_tree.py"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1},
            "indices": 2, "mode": 4,
        }]}],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_off, "byteLength": len(pos_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": nrm_off, "byteLength": len(nrm_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx_bytes), "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": int(len(positions)),
             "type": "VEC3", "min": pmin, "max": pmax},
            {"bufferView": 1, "componentType": 5126, "count": int(len(normals)), "type": "VEC3"},
            {"bufferView": 2, "componentType": 5125, "count": int(len(indices)), "type": "SCALAR"},
        ],
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes = json_bytes + b" " * ((4 - (len(json_bytes) % 4)) % 4)

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


def build_tile_mesh(arr, valid_full, x_centres, y_centres, cs, ce, rs, re_, stride, cx, cy):
    """Build a Y-up glTF grid mesh for the window cols [cs,ce], rows [rs,re_] at `stride`.

    Skips NoData cells (no fake fill). Returns (positions, normals, indices) in the shared
    global gltf frame, or None if the window has no complete valid quad.
    """
    cols = np.arange(cs, min(ce + 1, arr.shape[1]), stride)
    rows = np.arange(rs, min(re_ + 1, arr.shape[0]), stride)
    if len(cols) < 2 or len(rows) < 2:
        return None
    sub = arr[np.ix_(rows, cols)]
    vmask = valid_full[np.ix_(rows, cols)]
    h, w = sub.shape

    ex = (x_centres[cols] - cx).astype(np.float64)   # gltf X
    nz = -(y_centres[rows] - cy).astype(np.float64)   # gltf Z = -(north - cy)

    vid = np.full((h, w), -1, dtype=np.int64)
    n_vert = int(vmask.sum())
    if n_vert == 0:
        return None
    vid[vmask] = np.arange(n_vert, dtype=np.int64)

    rr, cc = np.nonzero(vmask)
    positions = np.empty((n_vert, 3), dtype=np.float64)
    positions[:, 0] = ex[cc]
    positions[:, 1] = sub[rr, cc]
    positions[:, 2] = nz[rr]

    quad = vmask[:-1, :-1] & vmask[:-1, 1:] & vmask[1:, :-1] & vmask[1:, 1:]
    qr, qc = np.nonzero(quad)
    if len(qr) == 0:
        return None
    i00 = vid[qr, qc]
    i01 = vid[qr, qc + 1]
    i10 = vid[qr + 1, qc]
    i11 = vid[qr + 1, qc + 1]
    tri_a = np.stack([i00, i10, i11], axis=1)
    tri_b = np.stack([i00, i11, i01], axis=1)
    tris = np.concatenate([tri_a, tri_b], axis=0)

    # area-weighted vertex normals, oriented up (+Y)
    normals = np.zeros((n_vert, 3), dtype=np.float64)
    p0 = positions[tris[:, 0]]
    p1 = positions[tris[:, 1]]
    p2 = positions[tris[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    for k in range(3):
        np.add.at(normals, tris[:, k], fn)
    if normals[:, 1].sum() < 0:
        tris = tris[:, ::-1].copy()
        normals = -normals
    lens = np.linalg.norm(normals, axis=1)
    lens[lens == 0] = 1.0
    normals = normals / lens[:, None]

    indices = tris.reshape(-1)
    return positions, normals, indices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("--lmax", type=int, default=3)
    ap.add_argument("--margin", type=float, default=1.02)
    args = ap.parse_args()
    LMAX = args.lmax
    MARGIN = args.margin

    ds = gdal.Open(args.src, gdal.GA_ReadOnly)
    if ds is None:
        sys.exit(f"cannot open {args.src}")
    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gt = ds.GetGeoTransform()
    ox, px, _, oy, _, py = gt
    arr = band.ReadAsArray().astype(np.float64)
    H, W = arr.shape
    base_res = abs(px)  # ground sample distance of the base raster (m)

    valid_full = np.isfinite(arr)
    if nodata is not None:
        valid_full &= arr != nodata

    # Crop to a multiple of 2^LMAX so the quadtree partitions evenly.
    cells = 1 << LMAX
    Wc = (W // cells) * cells
    Hc = (H // cells) * cells
    arr = arr[:Hc, :Wc]
    valid_full = valid_full[:Hc, :Wc]

    cols_all = np.arange(Wc)
    rows_all = np.arange(Hc)
    x_centres = ox + (cols_all + 0.5) * px
    y_centres = oy + (rows_all + 0.5) * py
    cx = float(x_centres.mean())
    cy = float(y_centres.mean())

    vz = arr[valid_full]
    emin = float(vz.min())
    emax = float(vz.max())

    tiles_dir = os.path.join(args.out_dir, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)

    # Global elevation box (z-up tile.Z), shared by every tile => guarantees Z containment.
    z_center = (emin + emax) / 2.0
    z_half = (emax - emin) / 2.0 * MARGIN

    sr = osr.SpatialReference()
    sr.ImportFromWkt(ds.GetProjection())
    epsg = sr.GetAuthorityCode(None)

    stats = {"tiles": 0, "vertices": 0, "triangles": 0, "by_level": {}}

    def geom_box(ix, iy, level):
        """z-up boundingVolume.box from the tile's geometric window extent (nests exactly)."""
        n = 1 << level
        c0 = ix * (Wc // n)
        c1 = (ix + 1) * (Wc // n)
        r0 = iy * (Hc // n)
        r1 = (iy + 1) * (Hc // n)
        e0 = ox + c0 * px          # window easting edges
        e1 = ox + c1 * px
        nN = oy + r0 * py          # north edge (top row, py<0 => larger north)
        nS = oy + r1 * py
        gx0, gx1 = (e0 - cx), (e1 - cx)                 # gltf X
        gz0, gz1 = -(nN - cy), -(nS - cy)               # gltf Z = -(north-cy)
        tx_c = (gx0 + gx1) / 2.0
        tx_h = abs(gx1 - gx0) / 2.0 * MARGIN
        ty_c = -(gz0 + gz1) / 2.0                       # tile.Y = -gltf.Z
        ty_h = abs(gz1 - gz0) / 2.0 * MARGIN
        return [round(v, 4) for v in (
            tx_c, ty_c, z_center,
            tx_h, 0.0, 0.0,
            0.0, ty_h, 0.0,
            0.0, 0.0, z_half,
        )]

    def make_tile(level, ix, iy):
        """Recursively build a tile node (+glb) and its children. Returns node dict or None."""
        n = 1 << level
        stride = 1 << (LMAX - level)
        tw = Wc // n
        th = Hc // n
        cs = ix * tw
        ce = cs + tw            # include neighbour's first sample (shared edge => no crack)
        rs = iy * th
        re_ = rs + th
        mesh = build_tile_mesh(arr, valid_full, x_centres, y_centres,
                               cs, ce, rs, re_, stride, cx, cy)
        children = []
        if level < LMAX:
            for dy in (0, 1):
                for dx in (0, 1):
                    child = make_tile(level + 1, ix * 2 + dx, iy * 2 + dy)
                    if child is not None:
                        children.append(child)
        if mesh is None:
            # No geometry here; promote children so the branch is not lost.
            return None if not children else {
                "boundingVolume": {"box": geom_box(ix, iy, level)},
                "geometricError": round(base_res * stride, 3),
                "refine": "REPLACE",
                "children": children,
            }

        positions, normals, indices = mesh
        name = f"L{level}_{ix}_{iy}.glb"
        write_glb(os.path.join(tiles_dir, name), positions, normals, indices)
        stats["tiles"] += 1
        stats["vertices"] += int(len(positions))
        stats["triangles"] += int(len(indices) // 3)
        stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

        node = {
            "boundingVolume": {"box": geom_box(ix, iy, level)},
            "geometricError": round(base_res * stride, 3),  # ground sample distance at this level (m)
            "refine": "REPLACE",
            "content": {"uri": f"tiles/{name}"},
        }
        if children:
            node["children"] = children
        return node

    root = make_tile(0, 0, 0)
    if root is None:
        sys.exit("no valid geometry produced")

    tileset = {
        "asset": {
            "version": "1.1",
            "generator": "orcast bake_tree.py (Wave 2 batch-conversion, full extent)",
            "extras": {"orcast": {
                "label": "modeled, not measured",
                "provenance": "NOAA NCEI CUDEM 1/9\" topobathy wash_bellingham; reprojected "
                              "NAD83->EPSG:32610, NAVD88 m preserved (no vertical shift). "
                              "Reproduces agent B's reproject method over the full SAN_JUAN_BOUNDS.",
                "crs": f"EPSG:{epsg}" if epsg else ds.GetProjection(),
                "vertical_datum": "NAVD88 m (absolute, true 1:1 scale, no exaggeration)",
                "local_frame_centroid_utm10n": [round(cx, 3), round(cy, 3)],
                "elevation_range_navd88_m": [round(emin, 3), round(emax, 3)],
                "resolution_base_m": round(base_res, 3),
                "lod_levels": LMAX + 1,
            }},
        },
        "geometricError": round(base_res * (1 << (LMAX + 1)), 3),  # above root
        "root": root,
    }
    with open(os.path.join(args.out_dir, "tileset.json"), "w") as f:
        json.dump(tileset, f, indent=2)

    summary = {
        "tiles": stats["tiles"],
        "vertices": stats["vertices"],
        "triangles": stats["triangles"],
        "tiles_by_level": stats["by_level"],
        "lod_levels": LMAX + 1,
        "centroid_utm10n": [round(cx, 3), round(cy, 3)],
        "elevation_range_navd88_m": [round(emin, 3), round(emax, 3)],
        "raster_grid_cropped": [int(Wc), int(Hc)],
        "resolution_base_m": round(base_res, 3),
    }
    with open(os.path.join(args.out_dir, "full.bounds.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

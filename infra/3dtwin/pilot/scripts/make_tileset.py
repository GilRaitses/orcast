#!/usr/bin/env python3
"""
make_tileset.py — emit a valid OGC 3D Tiles 1.1 tileset.json for a single glb tile.

Reads the bounds sidecar written by dem_to_glb.py (<glb>.bounds.json) and writes a
tileset.json next to the content. The content glTF is Y-up in a local meters frame;
3D Tiles applies the built-in glTF y-up -> z-up transform, so the tile bounding box
is expressed in the z-up tile frame:

  tile.X = gltf.X  (easting offset, m)
  tile.Y = -gltf.Z (northing offset, m)   [dem_to_glb.py already negated Z]
  tile.Z = gltf.Y  (elevation, m)

Usage:
  make_tileset.py <bounds.json> <content_uri> <out_tileset.json>
"""
import sys
import json

MARGIN = 1.02  # small slack so the validator's content-fits-tile check is robust


def main():
    bounds_path, content_uri, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(bounds_path) as f:
        b = json.load(f)

    xmin, ymin, zmin = b["local_bbox_min"]   # gltf X, Y(elev), Z
    xmax, ymax, zmax = b["local_bbox_max"]

    # Map gltf local frame -> 3D Tiles z-up frame.
    tx_half = (xmax - xmin) / 2.0 * MARGIN          # easting half-extent
    ty_half = (zmax - zmin) / 2.0 * MARGIN          # northing half-extent (from gltf Z)
    tz_half = (ymax - ymin) / 2.0 * MARGIN          # elevation half-extent (from gltf Y)
    tz_center = (ymax + ymin) / 2.0                 # elevation center

    box = [
        0.0, 0.0, tz_center,
        tx_half, 0.0, 0.0,
        0.0, ty_half, 0.0,
        0.0, 0.0, tz_half,
    ]

    # Geometric error of the root tile: diagonal of the horizontal extent is a
    # reasonable single-tile screen-space error budget.
    diag = (tx_half ** 2 + ty_half ** 2) ** 0.5

    tileset = {
        "asset": {
            "version": "1.1",
            "generator": "orcast make_tileset.py",
        },
        "geometricError": round(diag, 3),
        "root": {
            "boundingVolume": {"box": [round(v, 4) for v in box]},
            "geometricError": 0.0,
            "refine": "REPLACE",
            "content": {"uri": content_uri},
        },
    }

    with open(out_path, "w") as f:
        json.dump(tileset, f, indent=2)
    print(json.dumps(tileset, indent=2))


if __name__ == "__main__":
    main()

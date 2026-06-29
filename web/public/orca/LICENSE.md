# orca.glb - source mesh license and attribution

`orca.glb` in this directory is a converted, reoriented, and meshopt-compressed
derivative of a Creative Commons licensed killer whale model. CC-BY requires that
this attribution travel with the asset and any published build.

## Honesty label

This is a stylized **modeled** animal (low-poly geometry by an artist). It is not a
3D scan of a real, named orca, and it is not derived from measured biologging data.
Motion applied to it elsewhere in the twin is driven by separately labeled simulated /
partnership-gated telemetry, not by this mesh.

## Source asset actually used (the authorized backup)

- Title: **Killer Whale**
- Author: **Poly by Google**
- License: **Creative Commons Attribution 3.0 (CC-BY 3.0)** - https://creativecommons.org/licenses/by/3.0/
- Source page: https://poly.pizza/m/7pqZEQ9b_E-
- Direct source file downloaded: https://static.poly.pizza/a7baa268-485e-4bc8-a936-64087228e963.glb
- Date acquired: 2026-06-28

### Required attribution text (reproduce wherever the asset is shown)

> "Killer Whale" by Poly by Google, licensed under CC-BY 3.0
> (https://creativecommons.org/licenses/by/3.0/), via Poly Pizza
> (https://poly.pizza/m/7pqZEQ9b_E-). Modified: reoriented, scaled to metric, and
> meshopt-compressed for the ORCAST underwater twin.

## Why this asset and not the primary candidate

The OM-R research ranked the Sketchfab **"Killer Whale" by Trouvaille (@dashdu),
CC-BY 4.0** (https://sketchfab.com/3d-models/killer-whale-63b680d7e58f463a9868ed7bf163094a)
as the primary pick. Its public Sketchfab API metadata confirms `isDownloadable: true`
and license `CC Attribution` (CC-BY 4.0), but the download endpoint requires an
authenticated/interactive login (HTTP 401 without credentials), which is an interactive
gate this build lane is instructed to stop at. The CC-BY 3.0 Poly by Google model is the
research-listed, sign-off-authorized backup and downloads without login, so it was used.
If the operator later supplies the Trouvaille mesh, swap the source file and update this
file's attribution to CC-BY 4.0 / Trouvaille (@dashdu) accordingly.

## Changes made to produce orca.glb (CC-BY "indicate changes" requirement)

- Reoriented to the twin frame: rotated +90 degrees about Y so the rostrum points +X
  (forward) with +Y up. Source orientation had the body length along Z.
- Uniformly scaled to a body length of **7.0 m** (midpoint of the 6-8 m adult range in
  docs/orca/SKELETON.md), placing the mesh in a metric frame (1 unit = 1 meter).
- Recentered on the bounding-box origin.
- Welded, deduplicated, and pruned (no geometry decimation; triangle count unchanged).
- Applied `EXT_meshopt_compression` (the compression already decoded by the existing
  tile runtime). The original 32x32 PNG baseColor texture was retained unchanged
  (KTX2 was intentionally skipped - it would add a runtime decoder dependency and is
  pointless for a 32x32 texture).

## Resulting asset

- Triangles: 636. Vertices: 1137. Bounding box (m): X(length)=7.00, Y(up)=3.48, Z(lateral)=2.94.
- File size: ~28.4 KB (`orca.glb`).

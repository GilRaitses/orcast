# infra/3dtwin/bakeoff -- Wave 1 tiler bake-off (agent C)

Compares two pipelines for serving the orcast integrated land+seafloor surface to
`3d-tiles-renderer`, on one real pilot chunk, with measured sizes / draw counts /
fidelity. See `BAKEOFF.md` for results and the recommendation, and
`WIRING-tiler.md` for the chosen pipeline's exact steps.

- Candidate 1: meshed-surface -> OGC 3D Tiles 1.1 (glTF) -- **recommended**.
- Candidate 2: quantized-mesh terrain tiles (cesium-terrain-builder).

Everything runs natively on the `aimez-services` EC2 (x86_64, Ubuntu 22.04) as
official `linux/amd64` docker images (no emulation). Docker needs `sudo` there.

## Layout

```
scripts/
  Dockerfile.py          python image (numpy + rasterio) for mesh + fidelity
  00_prep_pilot.sh       stage pilot chunk (agent B's, or a CUDEM stand-in clip)
  10_mesh_to_3dtiles.py  Candidate 1: raster -> grid mesh -> glb + tileset.json
  15_mesh_compress.sh    build + Draco/meshopt compress + measure (Candidate 1)
  20_qmesh_ctb.sh        Candidate 2: CTB quantized-mesh + measure
  40_fidelity.py         RMSE vs source + vertical quant steps (LOD recon tif)
  30_stage_s3.sh         scp outputs to a credentialed host, upload to S3
  run_all.sh             end-to-end, reproduces every number in BAKEOFF.md
figures/                 hillshade + color-relief PNGs (visual fidelity)
BAKEOFF.md               comparison table + recommendation + S3 URIs + risks
WIRING-tiler.md          chosen pipeline, exact docker steps for Wave 2
```

## Reproduce

```bash
# from this dir, with ~/.ssh/pax-ec2-key.pem present and AWS creds for aimez-data
bash scripts/run_all.sh b          # 'b' = use agent B's chunk (default)
# bash scripts/run_all.sh standin  # fallback: clip CUDEM directly
```

Pilot chunk: agent B's reprojected `pilot_utm.tif` (CUDEM 1/9 topobathy,
San Juan Islands, EPSG:32610, NAVD88 m, 10 m). Outputs:
`s3://aimez-data/3dtwin/bakeoff/`.

No git commit; large artifacts live in S3 only.

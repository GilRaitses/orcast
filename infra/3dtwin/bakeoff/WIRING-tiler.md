# WIRING-tiler.md -- chosen pipeline: meshed-surface -> OGC 3D Tiles 1.1 (glTF)

For the Wave 2 integrator and the batch-conversion agent. This is the exact,
reproducible recipe for the recommended pipeline (Candidate 1), run natively on
the `aimez-services` EC2 (x86_64) as `linux/amd64` docker images.

## Inputs / outputs contract

- Input: a single-band DEM, projected metric CRS, NAVD88 m, NoData -9999.
  This wave used agent B's `pilot_utm.tif` (EPSG:32610, 10 m). Agent B's format
  spec: `s3://aimez-data/3dtwin/reproject/pilot_mesh.meta.json`.
- Output: `tileset.json` (3D Tiles 1.1) + `pilot.glb` (glTF tile content).
  - Local engineering frame, **Y-up**, Y = NAVD88 m (absolute), X = easting,
    Z = -northing, all relative to the tile centroid (recorded in
    `tileset.json -> asset.extras.orcast.local_origin_utm_xy`).
  - 3D Tiles 1.1 allows glTF/glb directly as `content.uri` (no b3dm wrapper).

## Host prep (one-time)

```bash
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177
mkdir -p ~/3dtwin/bakeoff_twin/{in,mesh3dtiles_B,logs}
# images (all linux/amd64, native on this x86_64 host):
sudo docker pull ghcr.io/osgeo/gdal:ubuntu-small-3.8.5
sudo docker pull node:20-slim
# python image with numpy+rasterio (Dockerfile.py in scripts/):
cd ~/3dtwin/bakeoff_twin && sudo docker build -f Dockerfile.py -t bakeoff-py .
# NOTE: docker requires sudo on this host (ubuntu user is not in the docker group).
```

## Step 1 -- mesh the surface and write the glTF tile + tileset

`scripts/10_mesh_to_3dtiles.py` (copied into `~/3dtwin/bakeoff_twin/`):

```bash
RWD=/home/ubuntu/3dtwin/bakeoff_twin
sudo docker run --rm -v $RWD:/data \
  -e IN_TIF=/data/in/B_pilot_utm.tif \
  -e OUT_DIR=/data/mesh3dtiles_B \
  -e STRIDE=1 \
  bakeoff-py python /data/10_mesh_to_3dtiles.py
# -> mesh3dtiles_B/pilot.glb  (raw float32 glTF)
# -> mesh3dtiles_B/tileset.json (3D Tiles 1.1, root.content.uri = pilot.glb)
```

The script: reads the raster, builds a regular-grid triangulation skipping any
triangle touching NoData, drops unreferenced vertices, computes per-vertex
normals, writes a GLB by hand, and emits a minimal `tileset.json` with an
oriented `box` bounding volume.

## Step 2 -- compress for delivery (gltf-transform, node container)

```bash
sudo docker run --rm -v $RWD:/data node:20-slim bash -c '
  cd /data/mesh3dtiles_B
  # full-fidelity (Draco only, no decimation):
  npx --yes @gltf-transform/cli@4 draco pilot.glb pilot.dracoonly.glb
  # optimized LOD (error-aware meshopt simplify + Draco):
  npx --yes @gltf-transform/cli@4 optimize pilot.glb pilot.draco.glb \
      --compress draco --texture-compress false
'
```

Measured on B's chunk: raw 56.2 MB -> Draco-only 2.75 MB (lossless) ->
optimize 274 KB (121,560 tris, ~3-4 m RMSE). Wave 2/agent D chooses the point;
`3d-tiles-renderer` decodes both Draco (`KHR_draco_mesh_compression`) and meshopt
(`EXT_meshopt_compression`).

If `tileset.json` should point at a compressed glb, update `root.content.uri`:

```bash
sed -i 's/"pilot.glb"/"pilot.draco.glb"/' $RWD/mesh3dtiles_B/tileset.json
```

## Step 3 -- stage to S3

The EC2 role cannot PutObject to `aimez-data`. Pull to a credentialed host and
upload (see `scripts/30_stage_s3.sh`):

```bash
scp -i ~/.ssh/pax-ec2-key.pem -r \
  ubuntu@44.197.243.177:~/3dtwin/bakeoff_twin/mesh3dtiles_B /tmp/bo/
aws s3 cp /tmp/bo/mesh3dtiles_B s3://aimez-data/3dtwin/bakeoff/mesh3dtiles/ --recursive
```

## Step 4 -- mount in `3d-tiles-renderer` (Wave 2 hand-off)

- Tileset URL: `s3://aimez-data/3dtwin/bakeoff/mesh3dtiles/tileset.json`
  (serve over HTTPS/CDN; the renderer fetches `tileset.json` then `pilot.glb`).
- gltfUpAxis = Y (3D Tiles default); the mesh is authored Y-up with Y=NAVD88 m.
- Place the tile in the SalishScene local frame using
  `tileset.json -> asset.extras.orcast.local_origin_utm_xy` (this tile's UTM
  centroid) or agent B's frame origin (485245.194, 5377443.419). Apply the
  easting/northing offset as the tileset/group transform; do not bake a global
  ECEF transform (keep it in the local UTM frame the scene + science share).
- The renderer-sandbox agent (E) proves the r3f + `TilesRenderer` lifecycle
  (`update()` per frame, camera sync, dispose) -- follow `WIRING-renderer.md`.

## What NOT to use

quantized-mesh (`.terrain`) is rejected for this twin: ~532 draw calls vs 1 at
native resolution, and it requires a CesiumGS-ellipsoid global-geodetic runtime
that `3d-tiles-renderer` does not natively provide. See `BAKEOFF.md`.

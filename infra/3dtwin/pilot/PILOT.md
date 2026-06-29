# Pilot 3D Tiles tileset — orcast terrain+bathymetry coastal twin (Wave 1→2 gate, rebuilt on agent B CUDEM/NAVD88)

One valid, optimized **OGC 3D Tiles 1.1** pilot tileset for the San Juan / Salish Sea
coastal twin. Built natively on the `aimez-services` EC2 (x86_64 Ubuntu 22.04) with official
`linux/amd64` docker images, no emulation. All numbers below are **measured**, not estimated.

> **Wave 1→2 gate rebuild (2026-06-27).** The served pilot has been rebuilt from
> **agent B's real CUDEM 1/9″ topobathy mesh (`wash_bellingham`), NAVD88 m, EPSG:32610**
> (`s3://aimez-data/3dtwin/reproject/pilot_utm.tif`, 1108×1113 @ 10 m). It **supersedes**
> the earlier GMRT (~MSL) substitute pilot. The served `pilot.glb` is now datum-correct:
> NAVD88 m preserved with **no vertical shift** (Y = NAVD88 m, true 1:1 scale). Still
> **modeled, not measured**, and still a single untiled tile. Mesh path follows agent C's
> recommended mesh→OGC 3D Tiles 1.1 (glTF) bake (`10_mesh_to_3dtiles.py`, NoData-skipped grid),
> compressed with `gltfpack -cc`, tileset assembled with `make_tileset.py`.

## TL;DR

| Item | Value |
|------|-------|
| Tileset format | OGC 3D Tiles 1.1 (glTF/glb content) |
| Validator | CesiumGS `3d-tiles-validator` |
| **Validation** | **0 errors, 0 warnings, 1 info** (PASS) |
| Tiles | 1 root tile, 1 glb content, no children |
| Source | NOAA NCEI CUDEM 1/9″ topobathy `wash_bellingham` (agent B), NAVD88 m, EPSG:32610 |
| Vertices / triangles | 1,229,170 / 2,453,900 |
| Optimized content (`pilot.glb`, `gltfpack -cc`) | **5,856,764 bytes (5.59 MiB)** |
| `tileset.json` | 454 bytes |
| Raw glb (pre-gltfpack) | 58,947,692 bytes (56.2 MiB) |
| Compression ratio | **10.07×** |
| Elevation range (NAVD88 m, preserved) | −264.367 … +273.882 m |
| Public URL (CloudFront, CORS) | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json` |
| S3 staging URI | `s3://aimez-data/3dtwin/pilot/tileset.json` |
| Served `pilot.glb` ETag | `e85028927628098b6faefc04632ab159` |
| Served `tileset.json` ETag | `8bfed2ee638800955499bb0297e964ec` |

## Data source (current served pilot — datum-correct)

The served pilot is built from **agent B's real CUDEM/NAVD88 surface**:

- **Source:** NOAA NCEI CUDEM 1/9″ arc-second topobathy, `wash_bellingham`; reprojected
  NAD83 → EPSG:32610 (UTM 10N, m) with **NAVD88 m preserved** (no vertical datum shift).
  Provenance: `s3://aimez-data/3dtwin/reproject/pilot_mesh.meta.json` + `navd88_proof.txt`.
- **Input raster:** `s3://aimez-data/3dtwin/reproject/pilot_utm.tif` — 1108×1113, 10 m posting,
  Float32, NoData −9999, NAVD88 m. Elevation −264.367 … +273.882 m, mean −19.6 m.
- **NAVD88 preserved:** B's `navd88_proof.txt` shows reprojected samples equal the NAD83/NAVD88
  source samples to sub-metre (no ~−22 m geoid offset), proving no implicit ellipsoid shift.
  The mesher copies elevation directly to glTF Y, so the served glb is NAVD88 m, 1:1, no shift.
- **Label: modeled, not measured.** Vertical scale is true (1:1, no exaggeration).

> **Supersedes the prior GMRT substitute.** In Wave 1, agents B/C/D ran in parallel; agent B's
> CUDEM mesh was not yet available, so the first served pilot was baked from a **GMRT GridServer**
> (≈MSL, EPSG:4326) stand-in over `SAN_JUAN_BOUNDS`. That GMRT note is now obsolete: the served
> objects at `s3://aimez-data/3dtwin/pilot/` have been overwritten with this CUDEM/NAVD88 build.

**Remaining Wave 2 item:** CUDEM `wash_bellingham` covers the pilot extent (485245–496315 E,
5377443–5388563 N); the full study bbox still needs CHS/GEBCO fill for the Canadian/San Juan
side, and an LoD hierarchy instead of one untiled tile (see Risks).

## Pipeline (reproducible — current CUDEM/NAVD88 build)

Run on the EC2 box (`ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177`); workdir
`~/3dtwin/pilot_rebuild/`. Inputs and tools are already staged on the host. Stages and the
docker image each uses (all `linux/amd64`, native on this x86_64 host, `sudo docker`):

1. **Input** agent B's `pilot_utm.tif` (CUDEM `wash_bellingham`, EPSG:32610, NAVD88 m, 10 m,
   1108×1113), pulled from `s3://aimez-data/3dtwin/reproject/` (instance role, `amazon/aws-cli`).
2. **Mesh** to a Y-up glTF in a local meters frame skipping NoData triangles
   (`bakeoff/scripts/10_mesh_to_3dtiles.py`, `bakeoff-py` image numpy+rasterio):
   **1,229,170 vertices, 2,453,900 triangles** (matches B's `pilot_mesh.ply`), per-vertex normals.
   Raw glb 58,947,692 bytes. Y = NAVD88 m (absolute, no shift).
3. **Optimize** with `gltfpack -cc` (EXT_meshopt_compression + KHR_mesh_quantization). Output
   `pilot.glb` **5,856,764 bytes (10.07×)**. `node:20-bookworm`.
4. **Assemble** `tileset.json` (3D Tiles 1.1, single z-up `box`-bounded REPLACE root,
   `make_tileset.py`; box mapped gltf→z-up with a 1.02 margin). `ghcr.io/osgeo/gdal`.
5. **Validate** with CesiumGS `3d-tiles-validator` → 0 errors. `node:20-bookworm`.
6. **Upload** `pilot.glb` (`model/gltf-binary`) + `tileset.json` (`application/json`) over the
   same S3 keys (`amazon/aws-cli`, instance role PutObject; overwrite, no delete).

## Geometry frame (measured)

- Target CRS: **EPSG:32610** (UTM zone 10N, meters). Vertical: **NAVD88 m** (absolute).
- Centroid (subtracted to make the local frame): **490775.194 E, 5383008.419 N**.
- Agent B scene-frame origin (for Wave 2 placement): **485245.194 E, 5377443.419 N**
  (`pilot_mesh.meta.json`); apply the easting/northing offset as the group transform, keep
  the local UTM frame (no global ECEF bake).
- glTF content axes (Y-up): `X = easting − cx`, `Y = NAVD88 elevation (m)`, `Z = −(northing − cy)`.
- `tileset.json` root `boundingVolume.box` (3D Tiles z-up frame, meters):
  - center `(0, 0, 4.7572)`  half-extents `(5645.7, 5671.2, 274.507)` (incl. 1.02 margin)
  - i.e. ≈ 11.07 km (E-W) × 11.12 km (N-S), elevation span −264.367…+273.882 m NAVD88.
- No root `transform`; this is a **local engineering frame**, not ECEF/geographic. The sandbox
  mounts it directly (see `WIRING-pilot.md`).

## Validator output (verbatim, `validation_report.json`)

```json
{
  "date": "2026-06-27T08:08:31.882Z",
  "numErrors": 0,
  "numWarnings": 0,
  "numInfos": 1,
  "issues": [
    {
      "type": "CONTENT_VALIDATION_INFO",
      "path": "pilot.glb",
      "causes": [{
        "causes": [
          { "path": "/extensionsUsed/1",
            "message": "Cannot validate an extension as it is not supported by the validator: 'EXT_meshopt_compression'.",
            "severity": "INFO" },
          { "path": "/buffers/0", "message": "This object may be unused.", "severity": "INFO" }
        ]
      }]
    }
  ]
}
```

The single INFO is not a defect: this validator version does not deep-inspect
`EXT_meshopt_compression` (a standard, widely-supported glTF extension that `3d-tiles-renderer`
decodes via the meshopt decoder), and the "buffer may be unused" note is the expected
consequence of meshopt's fallback-buffer layout. **Errors = 0, warnings = 0.**

## Artifacts

| Object | S3 URI | Public URL |
|--------|--------|-----------|
| tileset.json | `s3://aimez-data/3dtwin/pilot/tileset.json` | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json` |
| pilot.glb | `s3://aimez-data/3dtwin/pilot/pilot.glb` | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/pilot.glb` |
| validation_report.json | `s3://aimez-data/3dtwin/pilot/validation_report.json` | (same prefix) |
| pilot.bounds.json | `s3://aimez-data/3dtwin/pilot/pilot.bounds.json` | (same prefix) |

Hosting: bucket `aimez-data` has full S3 Block Public Access **on**, so the tileset is served
through a dedicated CloudFront distribution **`EOMERK64CS5CE`** (`d8kxxpcnj3ub5.cloudfront.net`)
using Origin Access Control `E38MFEYPYOOAUT` and the AWS managed **CORS-with-preflight**
response-headers policy. A scoped bucket policy grants that distribution `s3:GetObject` on
`3dtwin/pilot/*` only (not the whole bucket; principal is the CloudFront service with an
`AWS:SourceArn` condition — not a public policy, so BPA is preserved).

## Risks / caveats

- **Datum now correct; coverage not yet full.** The served pilot is CUDEM/NAVD88 m
  (`wash_bellingham`) over the pilot extent only. The full study bbox still needs CHS/GEBCO
  fill for the Canadian/San Juan side (north of CUDEM coverage) — a Wave-2 item.
- **Single untiled tile.** 2.45M triangles in one glb is fine as a pilot but is not an LoD
  hierarchy; the full-extent Wave-2 bake should tile/decimate for multiple LoDs.
- **`EXT_meshopt_compression` requires the meshopt decoder** in the renderer (see WIRING).
- **CloudFront cache.** The new objects served immediately (`x-cache: Miss from cloudfront`,
  ETags match S3), so **no invalidation was required**. Cached responses now carry the new
  ETags (`pilot.glb e85028927628098b6faefc04632ab159`, `tileset.json 8bfed2ee638800955499bb0297e964ec`).

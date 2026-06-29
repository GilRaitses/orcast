# Full-extent batch conversion — orcast terrain+bathymetry 3D twin (Wave 2)

Bakes the **full `SAN_JUAN_BOUNDS` extent** (lat 48.40–48.70, lng −123.25..−122.75)
into an **OGC 3D Tiles 1.1** tileset with a real **LoD quadtree** (multiple tiles,
decimation per level), glTF (`.glb`) content, gltfpack meshopt compression, validated
with the CesiumGS `3d-tiles-validator` (0 errors), served via CloudFront with CORS.

All heavy work runs natively on the `aimez-services` EC2 (x86_64 Ubuntu) with official
`linux/amd64` docker images — no emulation. **Modeled, not measured.** True 1:1 vertical
scale (no exaggeration); NAVD88 m preserved; local engineering frame in metres (no ECEF).

## TL;DR (measured)

| Item | Value |
|------|-------|
| Tileset format | OGC 3D Tiles 1.1 (glTF/glb content, `EXT_meshopt_compression`) |
| **Validation** | **0 errors, 0 warnings, 85 infos** (CesiumGS `3d-tiles-validator`) — PASS |
| Tiles | **85** (level 0: 1, level 1: 4, level 2: 16, level 3: 64) |
| LoD depth | **4 levels** (root + 3), REPLACE refinement |
| Vertices / triangles | 16,343,109 / 32,537,090 |
| Geometric error (m) | tileset 160 → root 80 → L1 40 → L2 20 → **leaf 10** (= ground sample distance) |
| Raw glb bytes (pre-gltfpack) | 782,755,000 (746 MiB) |
| Optimized glb bytes (post-gltfpack) | **79,437,040 (75.8 MiB)** — 9.85× |
| On S3 (tiles + tileset + sidecars) | 88 objects, **75.9 MiB** |
| Source surface | `full_utm.tif` 3690×3335 @ 10 m, EPSG:32610, NAVD88 m, valid 99.89% |
| Elevation range (NAVD88 m, preserved) | −376.431 … +733.885 m |
| Local frame centroid (UTM 10N) | 499935.748 E, 5377497.227 N |
| Public URL (CloudFront, CORS) | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` |
| S3 prefix | `s3://aimez-data/3dtwin/full/` |

## Provenance & honesty

Agent B staged only the **pilot-window** reprojected surface to S3
(`s3://aimez-data/3dtwin/reproject/pilot_utm.tif`, ~11 km). There is **no pre-baked
full-extent reprojected raster** on S3. This bake therefore **reproduces agent B's exact
reproject method** (`infra/3dtwin/reproject/01_*`, `02_*`) over the full bbox using the
**identical source and datum**:

- **Source:** NOAA NCEI CUDEM 1/9″ topobathy, `wash_bellingham` — the same **4 tiles**
  agent B proved cover 100% of `SAN_JUAN_BOUNDS` (incl. the Haro Strait / Canadian-side
  strip). No GEBCO/CHS fill is required inside the bbox.
- **Datum:** NAVD88 m, preserved with **no vertical shift** (a single-band warp changes
  only the horizontal CRS; no `+vto`, no geoid grid). Re-proven on the full extent in
  `navd88_proof_full.txt` (sample deltas ≤ 0.14 m, i.e. resampling noise — not a ~−22 m
  geoid offset).
- **Target CRS:** EPSG:32610 (UTM 10N, m), 10 m posting.

This is **not** a substitution of a different datum/source — it is B's own documented,
reproducible pipeline applied to the full window.

## Pipeline (reproducible)

Run on the EC2 host (`ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177`), workdir
`~/3dtwin/host/`. Driver: `bash run_all.sh`. Stages:

1. **`01_fetch_reproject.sh`** — fetch the 4 `wash_bellingham` tiles (reuses B's cache),
   VRT mosaic (`-allow_projection_difference`), `gdalwarp` the full bbox → `full_utm.tif`
   (EPSG:32610, 10 m, NAVD88 m), coverage + NAVD88-preservation proof. `gdal:ubuntu-small-3.8.5`.
2. **`02_bake.sh` → `bake_tree.py`** — bake the LoD quadtree: per level a 2^L×2^L grid,
   each tile decimated by stride 2^(LMAX−L) so every tile holds a ~constant vertex budget;
   leaves at full 10 m. One shared local frame centered on the full-extent centroid.
   NoData cells are **skipped** (no fake fill). Emits `tileset/tiles/L{lvl}_{ix}_{iy}.glb`
   + nested `tileset/tileset.json`.
3. **`03_compress.sh`** — `gltfpack -cc` each glb (EXT_meshopt_compression +
   KHR_mesh_quantization). `node:20-bookworm`.
4. **`04_validate.sh`** — CesiumGS `3d-tiles-validator` over `tileset.json` (follows the
   whole tree + content). Require 0 errors. `node:20-bookworm`.
5. **`05_upload.sh`** — `aws s3 sync` to `s3://aimez-data/3dtwin/full/` (instance role),
   correct content types, then `curl -I` CloudFront + CORS.

## Geometry frame (reuses agent D's mapping)

- glTF content is **Y-up** in ONE shared local engineering frame (metres), centered on the
  full-extent centroid `cx, cy` (UTM 10N): `X = easting − cx`, `Y = NAVD88 m`,
  `Z = −(northing − cy)`. All tiles share this frame → no per-tile transform.
- 3D Tiles applies the built-in glTF y-up→z-up transform, so each tile's
  `boundingVolume.box` is z-up: `tile.X = gltf.X`, `tile.Y = −gltf.Z`, `tile.Z = gltf.Y`
  (agent D's `make_tileset.py` mapping, generalized to non-centered tiles). Boxes use the
  tile's **geometric window** extent horizontally (child windows nest exactly inside parent
  windows) and the **global** elevation range vertically — this guarantees child ⊆ parent
  and content-fits-box, so the validator passes 0 errors.
- **No root `transform`** — local engineering frame, not ECEF/geographic. The Wave-2
  integrator derives scale/placement from the runtime bounding sphere (per WAVE2_DISPATCH).

## Validator output (verbatim header)

```json
{
  "date": "2026-06-27T09:24:14.406Z",
  "numErrors": 0,
  "numWarnings": 0,
  "numInfos": 85,
  ...
}
```

Each of the 85 infos is the benign pair (one per tile, identical to the served pilot):

```
"Cannot validate an extension as it is not supported by the validator: 'EXT_meshopt_compression'." (INFO)
"/buffers/0 This object may be unused." (INFO)
```

`EXT_meshopt_compression` is a standard glTF extension the validator does not deep-inspect;
`3d-tiles-renderer` decodes it via the meshopt decoder. The unused-buffer note is the
expected meshopt fallback-buffer layout. **Errors = 0, warnings = 0.**

## CloudFront / CORS

`curl -I https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` →
`HTTP/2 200`, `content-type: application/json`, `access-control-allow-origin: *`,
`access-control-allow-methods: GET, HEAD`. Tiles serve `model/gltf-binary` with the same
CORS headers.

The bucket `aimez-data` keeps Block-Public-Access **on**; objects are served through the
existing CloudFront distribution `EOMERK64CS5CE` (`d8kxxpcnj3ub5.cloudfront.net`) via OAC.
The OAC bucket policy was scoped to `3dtwin/pilot/*`; this wave **added an analogous
least-privilege statement** for `3dtwin/full/*` to the **same** distribution
(`bucket_policy_full.json`) — additive, non-public, BPA preserved.

## Risks / caveats

- **Modeled, not measured.** CUDEM is a modeled integrated topobathy surface.
- **10 m posting.** CUDEM native is ~3.4 m; the bake matches B's 10 m pilot posting. A
  finer bake would re-run `01_*` at a smaller `-tr` and raise counts/bytes proportionally.
- **Corner nodata wedges.** Reprojecting the lat/lng bbox to UTM leaves small NoData
  triangles at the rotated corners (valid 99.89%); these cells are skipped (no fake fill).
- **Meshopt decoder required** in the renderer (register `MeshoptDecoder`).
- **No commit.** Per charter; artifacts live in S3.

## Files

`env.sh` · `01_fetch_reproject.sh` · `bake_tree.py` · `02_bake.sh` · `03_compress.sh` ·
`04_validate.sh` · `05_upload.sh` · `run_all.sh` · `bucket_policy_full.json` ·
`WIRING-host.md` · figures `full_color.png` / `full_hs.png` (surface verification).

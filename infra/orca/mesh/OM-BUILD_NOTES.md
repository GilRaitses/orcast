# OM-BUILD notes - orca mesh acquisition + conversion

Wave OM-BUILD for the ORCA biologging twin. Dated 2026-06-28. Net-new build lane:
files created only under `web/public/orca/` and `infra/orca/mesh/`. No web runtime
dependency added. No git commit (operator gate is the commit).

## 1. Acquisition outcome

| Candidate | License | Result |
|---|---|---|
| **Primary** - Sketchfab "Killer Whale" by Trouvaille (@dashdu) | CC-BY 4.0 (verified live) | **STOPPED at login wall.** Download requires auth. Manual step below. |
| **Backup** - Poly Pizza "Killer Whale" by Poly by Google | CC-BY 3.0 (verified live) | **Downloaded non-interactively, no login.** Used for the build. |

### Primary probe (Sketchfab)

```
curl https://api.sketchfab.com/v3/models/63b680d7e58f463a9868ed7bf163094a
  -> HTTP 200; name "Killer Whale"; isDownloadable true; license "CC Attribution" (CC-BY 4.0,
     http://creativecommons.org/licenses/by/4.0/); user dashdu / Trouvaille; faceCount 3072.
curl https://api.sketchfab.com/v3/models/63b680d7e58f463a9868ed7bf163094a/download
  -> HTTP 401 {"detail":"Authentication credentials were not provided."}
```

The model is genuinely CC-BY 4.0 and downloadable, but only via an authenticated
session (interactive login + "Download 3D Model"). No Sketchfab credentials exist in
this environment, so per the charter the lane stops rather than guessing.

#### MANUAL STEP to use the primary (Trouvaille) mesh instead

1. Log in to Sketchfab and open:
   https://sketchfab.com/3d-models/killer-whale-63b680d7e58f463a9868ed7bf163094a
2. Click **Download 3D Model**, choose the **glTF (.glb / .gltf)** format (autoconverted glb is fine).
3. Save the downloaded file to:
   `infra/orca/mesh/_src/killer-whale-source.glb`
4. Re-run the conversion (section 3) pointing at that file, then update
   `web/public/orca/LICENSE.md` attribution to **CC-BY 4.0, "Killer Whale" by Trouvaille
   (@dashdu), https://sketchfab.com/dashdu** and copy the exact attribution string Sketchfab
   shows in its download dialog.

### Backup download (used)

```
GET https://poly.pizza/m/7pqZEQ9b_E-                 -> page confirms CC-BY 3.0, "Poly by Google", "No login required"
GET https://static.poly.pizza/a7baa268-485e-4bc8-a936-64087228e963.glb  -> HTTP 200, glTF binary
saved: infra/orca/mesh/_src/killer-whale-poly-source.glb  (44,292 bytes)
```

## 2. Tooling (build-only)

- Node.js v24.10.0
- @gltf-transform/cli, @gltf-transform/core, @gltf-transform/extensions, @gltf-transform/functions: **4.4.0**
- meshoptimizer (encoder/decoder): **1.1.1**
- Installed in an isolated `infra/orca/mesh/_tools/` package (gitignored node_modules).
- Scripts: `_tools/analyze.mjs` (geometry/orientation probe), `_tools/convert.mjs` (the build),
  `_tools/preview.html` (three.js + MeshoptDecoder visual check, mirrors the production loader).

## 3. Conversion command

```
node infra/orca/mesh/_tools/convert.mjs \
  infra/orca/mesh/_src/killer-whale-poly-source.glb \
  web/public/orca/orca.glb
```

What it does:
1. Measures the source bbox; body length runs along source +Z (nose +Z, fluke -Z, dorsal fin +Y,
   determined empirically by binning cross-section width/height - see analyze.mjs output).
2. Bakes a single matrix into the geometry: rotate +90 deg about Y (nose +Z -> +X forward, +Y up),
   uniform scale to 7.0 m body length, recenter on bbox origin.
3. weld + dedup + prune.
4. EXT_meshopt_compression (QUANTIZE). Texture left as-is (32x32 PNG; no KTX2, to avoid a runtime dep).

## 4. Before / after

| Metric | Source (Poly) | Output (orca.glb) |
|---|---|---|
| Triangles | 636 | 636 (no decimation) |
| Vertices | 1198 | 1137 (welded) |
| File size | 44,292 bytes (43.3 KB) | 29,128 bytes (28.4 KB) |
| Units | arbitrary (length ~559.7) | meters (length 7.00) |
| Orientation | length along Z | +X forward, +Y up (per SKELETON.md) |
| Bbox (m) | - | X 7.00, Y 3.48, Z 2.94 |
| Compression | none | EXT_meshopt_compression |

## 5. Validation

- `gltf-transform validate web/public/orca/orca.glb` -> no errors, no warnings (only an INFO that
  the validator does not itself support EXT_meshopt_compression).
- Loaded in a headless three.js page via `GLTFLoader.setMeshoptDecoder(MeshoptDecoder)` (the exact
  runtime path used by `web/lib/scene/tiles/useTilesLayer.ts`): loads ok, bbox X=7.00 Y=3.48 Z=2.94.
- Visual check (side / top / 3-quarter renders): recognizable orca, dorsal fin up (+Y), rostrum at
  +X, lateral fluke blades at -X. Screenshots taken during the build (not committed).

## 6. Honesty / caveats

- The mesh is a stylized, low-poly **modeled** orca, not a scan of a real individual. Recorded in
  `web/public/orca/LICENSE.md`.
- Proportions are stylized: at 7.0 m length the model's dorsal-to-belly height is 3.48 m, taller than
  a real orca; the metric anchor is body length. The OR (rig) wave may retopo/adjust if a smoother
  fluke or truer proportions are wanted (OM-R flagged this for the primary too).
- The backup has only a tiny 32x32 baseColor texture (vertex-ish coloring), no PBR maps. If higher
  fidelity is needed, obtain the Trouvaille primary (section 1) or retexture in OR.

## 7. Outputs

- `web/public/orca/orca.glb` (28.4 KB, 636 tris, meshopt)
- `web/public/orca/LICENSE.md` (CC-BY 3.0 attribution + change log)
- `infra/orca/mesh/_src/killer-whale-poly-source.glb` (unmodified source)
- `infra/orca/mesh/_tools/` (build scripts; node_modules gitignored)

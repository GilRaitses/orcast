# WIRING-host — full-extent tileset contract (batch-conversion → Wave-2 integrator)

The full `SAN_JUAN_BOUNDS` OGC 3D Tiles 1.1 LoD tree produced by the `batch-conversion`
agent. Swap this in where the integrator currently mounts the pilot URL.

## What to consume

| Field | Value |
|-------|-------|
| Tileset URL | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` |
| S3 prefix | `s3://aimez-data/3dtwin/full/` (`tileset.json` + `tiles/L{lvl}_{ix}_{iy}.glb`) |
| Format | OGC 3D Tiles 1.1, glTF/glb content, `EXT_meshopt_compression` |
| LoD | quadtree, 4 levels, **REPLACE** refinement, 85 tiles |
| Up axis | glTF Y-up (default `gltfUpAxis = Y`); 3D Tiles z-up box applied by the runtime |
| Root transform | **none** — local engineering frame (EPSG:32610-derived), metres, not ECEF |
| Vertical | NAVD88 m, **true 1:1 scale** (no exaggeration); Y = NAVD88 elevation |
| Elevation range | −376.431 … +733.885 m NAVD88 |
| Local frame centroid (UTM 10N) | 499935.748 E, 5377497.227 N |
| Root box (z-up, m) | center ≈ (0, 0, 178.73); half-extents ≈ (18808.8, 16972.8, 566.3) |
| Full extent | ≈ 36.9 km E-W × 33.3 km N-S (root half-extents include a 1.02 margin) |

## Integrator notes (matches WAVE2_DISPATCH `tiles-layer` / `integrator`)

- Mount via `useTilesLayer` exactly as the pilot: register `ImplicitTilingPlugin` is **not**
  needed (this is an **explicit** tileset, not implicit tiling), but DO register
  `GLTFExtensionsPlugin({ meshoptDecoder: MeshoptDecoder })` — meshopt is required.
- `groupRotationX = -Math.PI/2`, `fitScaleToWidth = SCENE_WIDTH`, and use the `onFit`
  **runtime bounding sphere** for camera framing + OrbitControls min/max distance. Do NOT
  hardcode extents from any sidecar; derive at runtime (the dispatch's reconciliation #2).
- The full extent is ~3.3× the pilot per side. Sea level (NAVD88 0 m) maps to scene Y 0 as
  before (Y = NAVD88 m through the uniform fit scale), so the water plane at Y 0 stays correct.
- Geometric errors are ground-sample-distance per level (tileset 160 → root 80 → 40 → 20 →
  leaf 10 m); tune `errorTarget` for the desired LoD aggressiveness.
- Georeference back to lat/lng for picking: `easting = gltfX + cx`,
  `northing = −gltfZ + cy` (cx, cy above), then EPSG:32610 → EPSG:4326.

## Provenance

NOAA NCEI CUDEM 1/9″ topobathy `wash_bellingham`, reprojected NAD83 → EPSG:32610 with
NAVD88 m preserved (reproduces agent B's method over the full bbox; see `README.md` and
`navd88_proof_full.txt`). **Modeled, not measured.**

## Sidecars on S3

- `full/full.bounds.json` — tile counts, per-level counts, centroid, elevation range, grid.
- `full/validation_report.txt` — full `3d-tiles-validator` output (0 errors).
- `full/navd88_proof_full.txt` — NAVD88-preservation proof over the full extent.

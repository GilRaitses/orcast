# WIRING-science: how this replaces the ETOPO1 provenance (later wave)

Audience: the Wave 2/3 integrator who promotes the modeled CUDEM depth field into
the live `s_space` covariate. This spike does NOT touch the committed asset; it
proves the path and hands over the exact steps.

## What exists today (do not break)

- Consumer: `src/aws_backend/sources/bathymetry.py` -> `BathymetryAdapter`.
  Reads a JSON `{"source","dataset","bounds","resolution_deg","points":[{lat,lng,depth_m}]}`.
  `depth_m` is NEGATIVE below sea level, POSITIVE land. API: `load()`,
  `depth_at(lat,lng)` (nearest-neighbour), `summary()`.
- Committed asset (ETOPO1, 1 arc-minute): `data/geo/san_juan_bathymetry.json`.
- Downstream: `src/aws_backend/spatial_enrichment.py` over `SAN_JUAN_BOUNDS`
  (`src/aws_backend/geo_region.py`, 48.40/48.70/-123.25/-122.75). Covariate
  `s_space` in `docs/methodology/FORECAST_KERNELS.md`.

The adapter reads the asset by a fixed relative path (`data/geo/san_juan_bathymetry.json`)
unless constructed with `asset_path=`. So the new field can be adopted either by
replacing the file in place (same path, no code change) or by passing
`asset_path=` at the call site.

## The replacement (one geometry, no second pipeline)

The new field is rasterized from the SAME NOAA NCEI CUDEM 1/9 topobathy surface
that feeds the render tiles, so render and science share one provenance chain
instead of two independent ETOPO1 copies. Format is byte-compatible with the
adapter; only the numbers and `source`/`dataset`/`resolution_deg`/`provenance`
metadata change.

### Option A (drop-in, smallest change)

Replace `data/geo/san_juan_bathymetry.json` with the regenerated CUDEM sample
(same schema). No backend code changes. `summary()["source"]` then reports the
CUDEM provenance instead of ETOPO1. This is the intended later-wave swap. (NOT
done this wave by rule.)

### Option B (side-by-side, safer rollout)

Keep both files, point the consumer at the new one via `asset_path=`, and compare
`s_space` output before retiring the ETOPO1 file. Useful if you want an A/B on the
forecast before committing.

## How to regenerate the field (reproducible)

On the `aimez-services` EC2 (x86_64), GDAL via native linux/amd64 docker:

```bash
scp infra/3dtwin/science/{rasterize_depth.sh,build_sample_json.py} \
    ubuntu@44.197.243.177:~/3dtwin/science/
ssh ubuntu@44.197.243.177 'cd ~/3dtwin/science && bash rasterize_depth.sh && python3 build_sample_json.py 0.005'
scp ubuntu@44.197.243.177:~/3dtwin/science/sample_san_juan_bathymetry_cudem.json <dest>
```

Knobs: `RES=<deg>` (grid spacing, default 0.005) and the resampler in
`rasterize_depth.sh` (`-r average`).

## Source-of-truth upgrade when Agent B lands

This spike clipped CUDEM directly because Agent B's reprojected mesh was not
ready. The clean end state: rasterize the depth field from Agent B's exact
integrated surface (the EPSG:32610 mesh, per `infra/3dtwin/reproject/WIRING-geometry.md`),
so the render mesh and the science raster are literally the same geometry, not
two clips of the same source. Concretely, when B's output exists:

1. Take B's surface (its S3 URI / mesh or the reprojected GeoTIFF it warps from).
2. If it is the EPSG:32610 mesh, sample depth on a lat/lng grid (warp back to
   EPSG:4326 for the adapter), preserving NAVD88 m and the sign convention.
3. Feed the resulting grid through `build_sample_json.py` unchanged.

Until then, this CUDEM clip and B's CUDEM reprojection read the identical NCEI
`wash_bellingham` tiles, so they already agree to within resampling.

## Provenance line to carry into the committed asset

> MODELED, NOT MEASURED. NOAA NCEI CUDEM 1/9 arc-second topobathy
> (wash_bellingham), NAVD88 m (positive up) used as the sea-level reference;
> rasterized from the same integrated surface that feeds the render tiles.
> Supersedes the ETOPO1 1-arc-minute provenance.

## Companion fields (optional, not yet consumed)

`slope_sanjuan_cudem.tif` and `aspect_sanjuan_cudem.tif` (same 0.005 deg grid)
exist on the EC2 host. `BathymetryAdapter` only reads `depth_m`, so slope/aspect
need either a new adapter or extra keys per point if `s_space` (or a habitat
prior) wants them. Out of scope for this spike; flagged for the science-substrate
wave.

## Collision note

This wave did not edit `web/app/components/scene/SalishScene.tsx`,
`web/package.json`, or `data/geo/san_juan_bathymetry.json`, and made no commit.

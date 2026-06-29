# 3d-twin

A reusable waveset charter template for building a geospatial 3D digital twin and unifying
its render geometry with a downstream spatial-science consumer. Generalized from the pax
"Realistic NYC 3D viewer" waveset (DoITT buildings as 3D Tiles + shading upgrade + shared
shade geometry).

Carried worked example: a terrain + bathymetry twin (land DEM joined to seafloor bathymetry
across a coastline, rendered in one scene, with the same geometry feeding a depth/habitat or
line-of-sight science consumer).

## Files

- `WAVESET_CHARTER_TEMPLATE.md`: the canonical prose template. Start here. Fill section 1
  (decision record), keep section 2 (execution model) verbatim, instantiate the three waves.
- `wave_shape.template.yml`: the machine-readable shape. Copy, rename, fill `<PLACEHOLDERS>`.

## How to ground a new project off this

1. Copy this directory to a new dated home and rename for the project.
2. Fill the decision record before launching any agent.
3. Use the per-agent prompt skeleton (charter section 4) for each parallel agent.
4. Hold the operator gates (charter section 6).

## Lineage

- pax plan: `~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md`
- pax viewer: `pax_v0/lib/comfort/viewer/createComfortMapViewer.ts`, `constants.ts`

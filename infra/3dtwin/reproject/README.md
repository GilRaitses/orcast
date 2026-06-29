# infra/3dtwin/reproject — CUDEM topobathy reproject + mesh (Wave 1, agent B)

Reprojects NOAA NCEI CUDEM 1/9 arc-second integrated topobathy to a clean triangulated
land+seafloor surface in EPSG:32610 (UTM 10N, metres), vertical NAVD88 m, for the orcast
Salish Sea 3D twin. Owns the two footguns: **vertical-datum preservation** and the
**coastline seam**. Heavy work runs as native x86_64 GDAL docker on the `aimez-services` EC2.

- `RECIPE.md` — exact docker commands, CRS/datum proof, coverage findings, weld procedure.
- `WIRING-geometry.md` — output contract (mesh + raster + shoreline) for agents C and F.
- `env.sh` — parameters + the `gdal()` docker helper. Source it first.
- `01_coverage.sh` · `02_clip_reproject.sh` · `03_mesh_shoreline.sh` · `run_pipeline.sh`.
- `mesh_dem.py` — grid → binary-PLY triangle mesh (runs inside the GDAL container).

Outputs (large artifacts) live in `s3://aimez-data/3dtwin/reproject/`, not git.

Quick start (on the EC2 host, scripts in `~/3dtwin/reproject/`):

```bash
cd ~/3dtwin/reproject && bash run_pipeline.sh
```

Modeled, not measured.

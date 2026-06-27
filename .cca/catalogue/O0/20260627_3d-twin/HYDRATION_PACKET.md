# Hydration packet, 3d-twin lane orchestrator

Ordered read list for the incoming thread. Read in order; do not read the chat transcript
linearly. Paths are repo-relative to `/Users/gilraitses/orcast` unless noted.

## 1. Governance / canon (read first)

- `.cca/catalogue/O0/20260627_3d-twin/HANDOFF_CHARTER.md` (this rotation's authority doc; locked
  decisions, dispatch table, return contract)
- `.cca/STANDING_DECISIONS_REGISTER.md` (settled decisions of record, including the orcast
  write policy SD-024 surgical commits and SD-006 single-author voice)

## 2. The 3d-twin charter (the lane canon)

- `.cca/catalogue/O0/20260627_3d-twin/WAVESET_CHARTER_TEMPLATE.md` (the canonical prose template:
  section 1 decision record, section 2 execution model verbatim, section 3 the three waves,
  section 4 per-agent prompt skeleton, section 5 collision rules, section 6 gates, section 7 open
  questions)
- `.cca/catalogue/O0/20260627_3d-twin/wave_shape.template.yml` (machine-readable shape; copy,
  rename, fill the `<PLACEHOLDERS>`, keep the execution-model fields)
- `.cca/catalogue/O0/20260627_3d-twin/README.md` (home overview + how to ground a new project)

## 3. Reference implementation (read-only lineage)

- `~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md` (the pax NYC viewer plan this
  template generalizes)
- `pax_v0/lib/comfort/viewer/createComfortMapViewer.ts`, `constants.ts` (the pax viewer; read-only,
  do not write pax surfaces)

## 4. Code surface to extend (orcast worked example)

- The orcast web viewer / scene assembler (the convergence file) under `web/` (identify the
  Three.js scene that mounts the map and overlays; it is the single convergence-file editor target)
- `src/aws_backend/sources/bathymetry.py` and the existing ETOPO1 bathymetry asset (current
  depth covariate; the science consumer side)
- `docs/methodology/FORECAST_KERNELS.md` (the `s_space` habitat term the twin geometry can feed)

## 5. Skill

- `~/.cursor/skills/orchestrator-rotation/SKILL.md` (how this handoff was built; use it to rotate
  again if token velocity climbs)

## 6. Environments

- Web: Next.js console under `web/` (Vercel project `orcast-h0`, Root Directory `web`).
- Heavy geo conversion (PostGIS, tilers, gltfpack) runs natively on a matching-arch host, not
  under emulation (charter section B.6 / template section 5).
- Large artifacts (tilesets, rasters, meshes) go to S3/CDN origin, never to git.

## 7. Repo map (orientation)

- `web/` Next.js console + Three.js scene (render target). `src/aws_backend/` FastAPI backend +
  data sources (science consumer side). `docs/methodology/` modeling canon. `.cca/catalogue/O0/`
  waveset homes (this lane lives in `20260627_3d-twin/`). `tools/` harnesses + gates.

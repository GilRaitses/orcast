# Orchestrator dispatch prompt (3d-twin lane)

Paste the block below into the fresh thread.

```
You are resuming as the orcast 3d-twin lane orchestrator (O0, 3d-twin only). Hydrate from
files, not from any chat transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260627_3d-twin/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260627_3d-twin/HYDRATION_PACKET.md
3. .cca/catalogue/O0/20260627_3d-twin/WAVESET_CHARTER_TEMPLATE.md and wave_shape.template.yml
4. ~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md (read-only lineage)

Locked, do not reopen (restated): geometry source is owned/public data, not managed photoreal
tiles (a science consumer must extract geometry); tiles are OGC 3D Tiles 1.1 (glTF) in plain
Three.js via 3d-tiles-renderer; extend the existing scene, do not adopt a new engine; one
geometry feeds both render and science (no drift); heavy converters run natively on the matching
CPU arch, never under emulation; per wave there is exactly one convergence-file editor and one
manifest editor, no dev server or full build during a parallel wave (type-check only), large
artifacts to object storage not git, one integration commit per wave; modeled outputs are
labeled "modeled, not measured"; for the terrain+bathymetry worked example, unify the land and
bathymetry vertical datums to one metric reference before meshing and weld the coastline seam
with no gap or overlap.

Active lane: 3d-twin only (the MLM/MLO forecast lane stays with the originating thread). You are
at the decision gate: instantiate the template for the orcast terrain+bathymetry twin, fill the
section 1 decision record, and surface the section 7 open questions. Do NOT launch Wave 1 until
the operator confirms the decision record. Do NOT commit or push without an explicit operator
ask. Do not write pax surfaces. Do not read the chat transcript linearly.

Return the section H ack from HANDOFF_CHARTER.md before acting.
```

## More context (need to file, not transcript)

| Need | File |
|------|------|
| Locked decisions + footguns | `.cca/catalogue/O0/20260627_3d-twin/HANDOFF_CHARTER.md` (B) |
| The waveset charter (decisions, execution model, waves) | `.cca/catalogue/O0/20260627_3d-twin/WAVESET_CHARTER_TEMPLATE.md` |
| Machine-readable shape | `.cca/catalogue/O0/20260627_3d-twin/wave_shape.template.yml` |
| Reference implementation | `~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md` |
| Open operator decisions | `WAVESET_CHARTER_TEMPLATE.md` (sections 1 and 7) |
| Rotation skill | `~/.cursor/skills/orchestrator-rotation/SKILL.md` |
| Uncommitted state rule | HANDOFF_CHARTER.md (G) |

# 3d-twin lane home

Home for the 3d-twin lane: a reusable waveset charter template for building a geospatial 3D
digital twin and unifying its render geometry with a downstream spatial-science consumer
(generalized from the pax "Realistic NYC 3D viewer" waveset), plus the orchestrator-rotation
handoff packet that hands this lane to a fresh thread.

Carried worked example: a terrain + bathymetry twin (land DEM joined to seafloor bathymetry
across a coastline, rendered in one scene, with the same geometry feeding a depth/habitat or
line-of-sight science consumer).

## Files

Template (the lane canon):
- `WAVESET_CHARTER_TEMPLATE.md`: the canonical prose template. Fill section 1 (decision record),
  keep section 2 (execution model) verbatim, instantiate the three waves.
- `wave_shape.template.yml`: the machine-readable shape. Copy, rename, fill `<PLACEHOLDERS>`.

Handoff packet (orchestrator-rotation skill):
- `HANDOFF_CHARTER.md`: authority doc (purpose, locked decisions, registry, open items, dispatch
  table, gate state, uncommitted state, return contract, provenance).
- `HYDRATION_PACKET.md`: ordered read list for the incoming thread.
- `ORCHESTRATOR_DISPATCH_PROMPT.md`: the paste block for the new thread + a context table.
- `STEP_LOG.md`: synthesis trace (S01, S02, ...).

## Start the fresh thread

Paste the block in `ORCHESTRATOR_DISPATCH_PROMPT.md` into a new thread, then require the section H
ack from `HANDOFF_CHARTER.md` before any action.

Lane status: template done; handoff packet written and committed. The lane is at the decision
gate: the receiving thread instantiates the template for the orcast terrain+bathymetry twin,
fills the section 1 decision record, and surfaces the section 7 open questions to the operator.
No waves launched. No commit or push without an explicit operator ask.

## How to ground a new project off this

1. Copy this directory to a new dated home and rename for the project.
2. Fill the decision record before launching any agent.
3. Use the per-agent prompt skeleton (charter section 4) for each parallel agent.
4. Hold the operator gates (charter section 6).

## Lineage

- pax plan: `~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md`
- pax viewer: `pax_v0/lib/comfort/viewer/createComfortMapViewer.ts`, `constants.ts`

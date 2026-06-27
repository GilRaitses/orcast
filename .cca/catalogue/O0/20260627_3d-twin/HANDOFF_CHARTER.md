# Handoff charter, 3d-twin lane orchestrator

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `70526ee` (in sync with
`origin/main`). This charters a fresh thread that takes over the 3d-twin lane: building a
realistic geospatial 3D digital twin and unifying its render geometry with a downstream
spatial-science consumer, instantiated for the orcast terrain + bathymetry coastal twin.
Hydrate from files, not from the transcript linearly.

## A. Purpose

The new thread owns the 3d-twin lane and nothing else. The MLM/MLO forecast modeling lane
stays with the originating O0 thread. The 3d-twin home holds a reusable waveset charter
template (generalized from the pax "Realistic NYC 3D viewer" waveset) plus this handoff. The
job is to instantiate the template for the orcast worked example (a land DEM joined to seafloor
bathymetry across the Salish Sea coastline, rendered in one Three.js scene, with the same
geometry feeding a depth/habitat or line-of-sight science consumer), make the section 1 decision
record, and prepare Wave 1 to the operator-decision gate. Do not launch the build waves until
the decision record and the section 7 open questions are answered by the operator.

## B. Decisions that are LOCKED, do not reopen

1. Write policy. No commit or push without an explicit operator ask (orcast workspace rule).
   Do not write pax surfaces. This lane writes only under its own home and the viewer/science
   code paths it is assigned.
2. Geometry source is owned/public data, not managed photoreal tiles. A science/measurement
   consumer must extract geometry, and managed photoreal tiles commonly forbid measurement and
   geodata extraction (`WAVESET_CHARTER_TEMPLATE.md` section 1).
3. Tile format is OGC 3D Tiles 1.1 (glTF), rendered in plain Three.js via `3d-tiles-renderer`
   with no Cesium runtime, so existing overlays stay native.
4. Render runtime extends the existing Three.js scene; it does not adopt a new engine, so
   route/camera/overlay code is preserved.
5. Single source of truth: one geometry feeds both the render (vector mesh) and the science
   (rasterized field). Two pipelines would let the picture and the numbers drift apart.
6. Conversion host: heavy native converters (PostGIS, tilers) run natively on the matching CPU
   architecture, not under emulation, which crashes them. Provision a matching-arch box and
   confirm reachability before the first heavy conversion.
7. Parallelism discipline (the hard-won part, keep verbatim from charter section 2 and 5):
   one file one owner per wave; exactly one convergence-file editor per wave (everyone else
   ships a module plus a wiring spec); exactly one dependency-manifest editor per wave; no dev
   server or full build during a parallel wave (type-check only); large artifacts go to object
   storage, never git; each wave ends with one integration commit and push.
8. Honesty constraint carried into every wave: modeled outputs stay labeled "modeled, not
   measured"; no agent invents coverage or metrics it did not produce. A visual-only backdrop
   (if any) is hard-separated from the science pipeline and is never a science input.
9. Worked-example footguns (terrain + bathymetry). Vertical datum reconciliation is the analog
   of the NYC feet-to-meters and z-up-to-y-up fix: land DEM is on a land vertical datum
   (NAVD88 / ellipsoid), bathymetry on a tidal datum (MLLW / mean sea level); convert both to
   one metric vertical reference before meshing or the coastline will not join. Coastline seam
   handling is the analog of the NYC "double-drawn buildings" gate: terrain and bathymetry must
   meet at the shoreline with no gap and no overlap.

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| Template | `WAVESET_CHARTER_TEMPLATE.md`, `wave_shape.template.yml`, `README.md` | done (reusable template, generalized from pax NYC viewer) |
| Handoff | this charter + hydration packet + dispatch prompt + step log | done (this rotation) |
| Decision record | section 1 of the charter template | open (operator input needed) |
| Wave 1 (foundation/de-risk) | realism, reproject+datum, tiler bake-off, optimize, renderer sandbox, science spike | not started (gated on the decision record) |
| Waves 2-3 | integrate, scale, science, hardening | not started |

## D. PRIMER, open items

The operator asked this lane to be rotated to a fresh orchestrator so it can take over the
3d-twin while the originating thread completes its ML ops work. Before any build launch, the new
thread must resolve the charter section 7 open questions: first-wave scope (include the science
spike or defer it), conversion host (local vs shared vs dedicated matching-arch box), subagent
model (inherit vs pin for build-heavy agents), and the worked-example specifics (which DEM, which
bathymetry source, target CRS, one metric vertical reference, and the exact downstream science
consumer). These are operator decisions; surface them, do not guess.

## E. Dispatch table

| Lane | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| Decision record | operator + orchestrator | charter section 1 + section 7 | every cell filled with a rationale | open |
| Wave 1 foundation | orchestrator (6 parallel agents) | filled decision record; data sources confirmed | pilot tileset validates AND sandbox renders it | gated on decisions |
| Wave 2 integrate | orchestrator (1 convergence editor) | landed Wave 1 modules + wiring specs | full-extent tiles render at interactive rate; legacy path removed | blocked (W1) |
| Wave 3 scale/science | orchestrator (6 parallel agents) | landed Wave 2 scene | full twin hosted + validated with provenance; perf in budget | blocked (W2) |

## F. Open gate / metric state

Nothing is fit or rendered yet; the lane is at the decision gate. The template's gates are:
Wave 1 to Wave 2 requires a validated pilot tileset that the sandbox route renders; Wave 2 to
Wave 3 requires full-extent tiles at interactive frame rate with the legacy placeholder removed;
Wave 3 exit requires the hosted twin validated against an external reference with a "modeled, not
measured" provenance line and an error band. No metrics exist until Wave 1 runs.

## G. Pending uncommitted local state

As of this rotation the 3d-twin home (template + this handoff packet) is committed and pushed at
the operator's request (see the lane STEP_LOG for the hash). If the operator later edits the
decision record or instantiates the template into a new dated home, update this section. The rest
of the working tree carries pre-existing uncommitted state unrelated to this lane (see the repo
`git status`); do not sweep it into a 3d-twin commit. Surgical staging only.

## H. Return contract (ack on first response)

The new thread returns, before acting:
- Hydration confirmed, list of files read.
- The locked items (section B) restated in your own words, especially the owned-geometry/3D-Tiles
  decision, the single-convergence-file-editor parallelism rule, and the terrain/bathymetry
  vertical-datum and coastline-seam footguns.
- Current lane state in one line (at the decision gate; no waves launched).
- The exact operator decisions you need before launching Wave 1 (charter section 1 + section 7).
- One risk still needing attention.

## I. Transcript / provenance pointer

Originating session: `~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/b67452d8-e353-4eb2-b95f-48cd71b286d6/b67452d8-e353-4eb2-b95f-48cd71b286d6.jsonl`.
Search by keyword (3d-twin, rotate, wildlife, L2, harmonic), do not read linearly. The lineage of
the template is the pax "Realistic NYC 3D viewer" plan at
`~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md` (read-only reference).

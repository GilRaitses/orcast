# WS-BATHY implementation dispatch

Home: `.cca/catalogue/O0/20260627_console-ws-bathy/`
Date: 2026-06-27. Status: PROPOSED. Held for the program orchestrator to gate and to serialize the phase-B `SalishScene.tsx` edit after WS-SCENIC.

This dispatch does not run. It is the plan the program orchestrator gates. Producers commit, deploy, and promote nothing, per B.10. Secrets stay in `.env`. Never `git add -A`.

## Shape

- Phase A, four parallel producers, one file family each, no shared file, no dev server during the parallel build. Validate by type-check and fixture.
- Phase B, one editor mounts the phase-A modules into `SalishScene.tsx`, after WS-SCENIC has released the file. Validate by type-check plus a REAL rendered depth-read visual check at acceptance.

## Common acceptance instrument, the real depth-read visual check

Every visual claim is verified by reading the rendered output, never claimed unseen, per the visual-verification rule and the six-wave acceptance gate. The water2 fragment shader already carries `uDebug` and `uDebugScale`, which render the water-column thickness as grayscale. The acceptance procedure at phase B and at the waveset acceptance wave, run the live scene, capture a beat frame in normal mode and a matched frame in depth-debug mode, and confirm by reading both frames that shoals read light, channels read dark, the deep Haro Strait channel reads deepest, the shoreline shows no double-draw or seam at Y = 0, and the measured-coverage overlay matches the source flag. Capture screenshots into `gate_screenshots/` in this home.

## Phase A, producer A1, Bathy Data Engineer

- Task. Build `web/lib/scene/bathy/provenance/`, a typed loader and coverage model for the MEASURED reference. Source NOAA BlueTopo on the US side, keyed on the per-pixel `bathy_coverage` boolean, true means measured, false means interpolated. Source CHS NONNA presence on the BC side of Haro Strait and Boundary Pass. Copy a derived coverage asset verbatim into `web/public/geo/`, fetched at runtime like the substrate JSON, source of truth staged under `infra/3dtwin/`. Carry the provenance and licence strings.
- Deliverables. The module with a public surface that answers measured-versus-modeled for a lat or lng and returns the carried provenance and licence, the fetched coverage asset(s), and a `WIRING-bathy-provenance.md` contract mirroring `WIRING-substrate.md`.
- Honesty. Returns measured only where the source flag asserts it, BlueTopo `bathy_coverage` true or NONNA present. Defaults to modeled everywhere else. Never infers measured. NONNA datum noted, chart datum not NAVD88.
- Validation. `cd web && npm run typecheck` exit 0. A fixture test that a known measured cell returns measured and a known gap returns modeled.
- Collision avoidance. Owns only `web/lib/scene/bathy/provenance/` and its new `web/public/geo/` asset(s). Does not touch `substrate/`, `water2/`, or `SalishScene.tsx`.

## Phase A, producer A2, Bathy Terrain Builder

- Task. Build `web/lib/scene/bathy/field/`, a seabed depth-field reader that wraps the existing `SubstrateField` and exposes a normalized depth suitable for tinting, reconciled to the live tile frame and the NAVD88 Y = 0 datum. Provide the `project` callback that maps a field point into the live tile frame so a tint overlay aligns with the rendered terrain. Does NOT author a second seabed mesh, the seabed is the baked CUDEM topobathy.
- Deliverables. The module exposing normalized depth and the tile-frame projector, plus a short `WIRING-bathy-field.md`.
- Honesty. Modeled, not measured, mirrors `SUBSTRATE_LABEL`. Reads the modeled substrate and the modeled seabed only.
- Validation. `npm run typecheck` exit 0. A fixture test that normalized depth is monotonic in depth and that the projector round-trips a known lat or lng into the expected scene XZ.
- Collision avoidance. Owns only `web/lib/scene/bathy/field/`. Reads the substrate public surface, requests any substrate internal change through `science-substrate`.

## Phase A, producer A3, Water and Depth Stylist

- Task. Build `web/lib/scene/bathy/style/`. Produce a bathymetric seabed tint as a tuned `SubstrateOverlayOptions` set for `buildSubstrateOverlay`, using a perceptually uniform `deep` family ramp, light shallow to dark blue and purple deep, blended with the existing relief lighting, mapped over the scene depth extent from `minDepthM` and `maxDepthM`. Produce the proposed `Water2Options` tuning set, palette and depth scales tuned against the full-extent tileset, plus a written request to the water2 owner for a per-channel RGB absorption upgrade with proposed coefficients.
- Deliverables. The style module returning the overlay options and the `Water2Options` set, a `WATER2_TUNING_REQUEST.md` addressed to the water2 owner, and tuning notes.
- Honesty. The tint styles a modeled seabed, label modeled. Foam and Fresnel are physics and atmosphere, not a survey.
- Validation. `npm run typecheck` exit 0. A fixture test that the ramp maps the deepest depth to the deep endpoint and 0 m to the shore endpoint. The real depth-read visual confirmation happens at phase B with the integrator, since styling needs the live render.
- Collision avoidance. Owns only `web/lib/scene/bathy/style/`. Proposes water2 changes through the owner, does not edit `depthWater.ts`.

## Phase A, producer A4, Honesty Labeler

- Task. Build `web/lib/scene/bathy/honesty/`, the canonical label model for the waveset. Stamp `modeledNotMeasured` and a measured-coverage label onto every bathy object and any UI string, reusing `SUBSTRATE_LABEL` and adding a measured-coverage label keyed to the A1 provenance signal. Provide the honesty note text the phase-B editor adds to the scene honesty record.
- Deliverables. The honesty helpers, the label constants, and the proposed scene honesty-note text.
- Honesty. This is the enforcement surface for B.6, no invented depths presented as measured.
- Validation. `npm run typecheck` exit 0. A fixture test that a modeled surface never receives a measured label and a measured-coverage surface carries both the coverage label and its source attribution.
- Collision avoidance. Owns only `web/lib/scene/bathy/honesty/`. Pure helpers, no scene edits.

## Phase B, the single scene-mount editor, after WS-SCENIC

- Task. Edit `web/app/components/scene/SalishScene.tsx` once, only after WS-INTENT and WS-SCENIC have released the file per the convergence calendar. Add a `BathyRig` that mounts the A3 seabed tint through `buildSubstrateOverlay` with the A2 projector, applies the A3 `Water2Options` tuning to the existing `Water2Rig` construction, mounts the A1 plus A4 measured-coverage honesty layer, and keeps the pick `depth_m` modeled-labeled. Add no second per-frame depth pass, the water2 pre-pass stays the only one. Update the scene honesty note with the A4 text.
- Deliverables. The mounted BathyRig, the applied water tuning, the honesty note update, and the captured acceptance frames in `gate_screenshots/`.
- Validation. `cd web && npm run typecheck` exit 0, then the real depth-read visual check above, normal and depth-debug frames read and confirmed. Sign-off is by the orchestrator, not the builder.
- Collision avoidance. WS-BATHY holds the `SalishScene.tsx` lock for this single edit only, after SCENIC. No other waveset edits it concurrently. No water2 or substrate internal edits in this file.

## Sequencing and dependencies

- A1, A2, A3, A4 run in parallel, no shared file.
- A3 depends on A2 for the projector and on the substrate `minDepthM` and `maxDepthM`, both available read-only at build time.
- The water2 per-channel absorption upgrade is a request to the water2 owner, it is not on the WS-BATHY critical path. If the owner declines or defers, A3 ships the two-stop tuning and the upgrade is a follow-up.
- Phase B waits on the convergence calendar, INTENT then SCENIC then BATHY.

## Open decisions for the operator, see README and the return summary

1. Adopt BlueTopo plus NONNA as the measured reference and accept staging derived coverage assets under `infra/3dtwin/` and `web/public/geo/`, or hold the measured overlay and ship modeled-only with the honesty label.
2. Approve requesting the per-channel absorption upgrade from the water2 owner, or keep the two-stop ramp tuning only.
3. Confirm the phase-B `SalishScene.tsx` serialization slot after WS-SCENIC.

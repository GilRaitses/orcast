# STX-Q decision — DEFER (cost stated)

- Lane: BSWR-STX (station-tileset-extent, OPTIONAL)
- Gate: STX-Q (gated-on-O0)
- Decision: DEFER. The lane closes here. O0 ruled on the STX-R return.
- Date: 2026-06-29 (America/New_York)
- Verified against origin/main `61ba1d6`.

## Why defer (the stated cost)

- The rendered extent `lat 48.40-48.70, lng -123.25 to -122.75` is shared identically by the tileset, the substrate depth field, and the scene projection frame. The 3-node `STATION_CATALOG` is correct by construction (the backend filters to that extent), not a defect.
- The two charter-named out-of-extent real nodes (Port Townsend `48.135743,-122.760614`; Bush Point `48.0336664,-122.6040035`) sit in Admiralty Inlet ~45-55 km southeast of the San Juan core. Honesty is satisfiable (both have real catalog positions), but the cost is not justified now:
  - Widening requires a 3D-TWIN host re-bake of the tileset AND a re-bake of the substrate field (the source CUDEM may not reach Admiralty), then a single-editor INT edit on the shared `SalishScene.tsx` / `useTilesLayer.ts`.
  - Load cost at a fixed 10 m leaf GSD scales with area. A union bbox is ~3.27x the area: first paint ~19 -> ~60 MiB, engaged ~76 -> ~248 MiB (about +41 MiB first paint, +172 MiB engaged), most of it empty water and unrelated land in the gap.
  - Framing regression: the fit scales the whole sphere to 120 scene units, so the core halves on screen, directly reversing the just-landed W-PERFUX RP2 tightening that fixed the operator's "so far back" complaint. No single-frame framing keeps the core tight AND shows the new nodes at rest.
  - Thin value: the PT/BP region expansion is itself operator-gated and uningested (TB1 D1), the nodes add 0 net-new summer presence-days, and they would be off-frame live-listen-only beacons. No approved load/frame-time budget exists, and the binding client-tier frame-time number is unmeasured (owned by the PRF lane).

## Reconsideration conditions (all three required to reopen)

1. The PT/BP region expansion is approved and ingested (TB1 D1 cleared).
2. An approved load + frame-time budget exists AND a measured client-tier frame-time number is in hand (PRF lane delivered).
3. A product decision to build a separate Admiralty VIEW (a two-box tileset with its own frame) rather than widen the single core frame.

If and when all three hold, reopen STX-Q with a two-box-view plan rather than a single-frame extent widen.

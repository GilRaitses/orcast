# STX — station-tileset-extent (waveset charter, OPTIONAL)

- Lane code: `STX`  Family: `BSWR`  Owner: dispatched sub-orchestrator (answers to O0)
- Type: research-first, then 3D-TWIN-owned execution (OPTIONAL, deferrable)
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/` ; dispatch `dispatch/STX/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
- Umbrella: `PROGRAM.md` ; dependency: 3D-TWIN family (`../20260627_terrain-bathymetry-twin/`)

## Intent

Decide, with cost in hand, whether to widen the station player to Puget Sound
nodes outside the current tileset extent (Port Townsend, Bush Point), and if so,
land it as a 3D-TWIN-owned extent change. This lane may legitimately return a
deferral decision rather than build.

## Grounding (real seams + verified root cause)

- The BST station player selects from `STATION_CATALOG`; the homepage twin renders
  the current 3D-TWIN tileset extent.
- The DCLDE-2027 eval already references `port_townsend` and `bush_point` as
  station-days, so the data exists; the limit is the rendered tileset extent.
- 3D-TWIN owns the tileset extent and framing: `web/lib/scene/tiles/useTilesLayer.ts`,
  `web/app/components/scene/SalishScene.tsx`, plus the W2.6 datum fix and the
  W-PERFUX framing work. TWIN-W-PERFUX found the load cost is leaf terrain
  geometry (64 L3 leaves = 74.7% of 75.75 MiB), so a wider extent has a real,
  measured load-cost implication.

Root cause: wider nodes need a tileset-extent change owned by 3D-TWIN, with a
load-cost trade-off that W-PERFUX already quantified. This is a cost/coordination
decision before any build.

## Locked decisions (do NOT reopen)

1. OPTIONAL and deferrable. `STX-Q` may return "defer" to O0 with the cost
   stated; that is a valid, successful outcome. Do not build on a hunch.
2. 3D-TWIN owns the extent. Any tileset-extent or framing change is 3D-TWIN-owned
   and serialized on `SalishScene.tsx` / `useTilesLayer.ts` across 3D-TWIN / WFX /
   ORCA / OCN / ENV. STX does not edit the tileset extent unilaterally.
3. No load-cost regression beyond an O0-approved budget. The W-PERFUX leaf-geometry
   cost is the baseline; widening the extent must keep the resting framing within
   an O0-approved load + frame-time budget, or it does not ship.
4. Honesty unchanged. Wider nodes are real stations; no station is shown that the
   catalog cannot back with a real position.

## Wave structure

- `STX-R` (research + discovery, read-only). Parallel; each owns one `dispatch/STX/findings/STX-<TOPIC>.md`:
  - R1 extent + catalog: the current tileset extent, `STATION_CATALOG` bounds, and which real nodes fall outside it (Port Townsend, Bush Point, others).
  - R2 3D-TWIN ownership: how `useTilesLayer` sets extent + framing; the W2.6 datum + W-PERFUX framing constraints; the cleanest extent-widening seam.
  - R3 load cost: the W-PERFUX leaf-geometry cost model; the measured load + frame-time implication of a wider extent.
  - R4 adversarial: framing regression, load-cost blowup, and the case for deferral.
- `STX-Q` (qualify methodology + decision). GATED. Returns either "defer (cost stated)" OR a costed, 3D-TWIN-coordinated extent-widening plan with an O0-approved budget. Returns to O0.
- `STX-B` (implement, only if Q says proceed). 3D-TWIN-coordinated extent + catalog change; net-new prep where possible.
- `STX-INT` (integrate, only if proceeding). GATED. Single editor lands the extent + catalog change in `useTilesLayer.ts` / `SalishScene.tsx`; serialize across 3D-TWIN/WFX/ORCA/OCN/ENV.
- `STX-ADV` (adversarial review). Audits framing + load-cost regression; loops back until within budget.
- `STX-ACCEPT` (accept). GATED. GPU frames at the wider extent at rest/near; Read-examined; load + frame-time within the approved budget.

## Acceptance criteria (hard, checkable)

- Either a deferral decision with the load cost stated, OR: the wider nodes render at the new extent with the resting framing intact, Read-examined on GPU frames, and load + frame-time within the O0-approved budget.
- No station shown without a real catalog position.
- No 3D-TWIN extent edit happened outside the single-editor `STX-INT` slot.

## Escalation

Per PROGRAM.md. Pause and return to O0 on the build-vs-defer decision, the
3D-TWIN coordination, the load-cost budget, the convergence edit slot, the GPU
capture, or commit.

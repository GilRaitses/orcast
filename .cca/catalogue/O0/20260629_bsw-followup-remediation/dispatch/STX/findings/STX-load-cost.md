# STX-R3 load cost (findings)

Lane STX. Wave STX-R, member R3. Read-only. Reports to O0 via the STX
sub-orchestrator. repo_state_verified_against:
`61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
Method: reuse the measured W-PERFUX RP1 numbers (measured over the wire against
the served CloudFront origin) and apply the bake's area-scaling law to the
candidate wider bboxes. No code edited, no fetch run this lane.

## 1. The W-PERFUX leaf-geometry cost model (measured baseline)

RP1 (`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/research/RP1_load_perf.md`)
measured the served full-extent tileset tile by tile.

| Level | Tiles | MiB | Share |
|---|---|---|---|
| L0 root | 1 | 0.94 | 1.2% |
| L1 | 4 | 3.72 | 4.9% |
| L2 | 16 | 14.54 | 19.2% |
| L3 leaves | 64 | 56.55 | 74.7% |
| Total | 85 | 75.75 | 100% |

The load-bearing facts:

- The 64 L3 leaves are 74.7% of the bytes. Leaf-level terrain geometry is the
  dominant cost.
- Per-tile size is roughly flat at about 900 KiB at every level, because
  `bake_tree.py` decimates by stride `2^(LMAX-L)` so each tile carries a near
  constant vertex budget. Total cost therefore tracks tile COUNT, not per-tile
  weight.
- Tiles are geometry only, no textures (POSITION and NORMAL, meshopt encoded). So
  texture compression cannot help and is not the lever.
- At a fixed 10 m leaf ground-sample-distance, the leaf grid is proportional to
  ground AREA. The current 64 leaves cover about 1,225 km2, about 19 km2 per leaf,
  which matches the measured roughly 193k positions per leaf.

The decisive corollary for STX: at a fixed 10 m leaf GSD, tile count and bytes
scale with the baked AREA. Widening the bbox multiplies the leaf set by the area
ratio.

## 2. The current startup mitigation (what a widen also scales)

The resting wide frame does not pay the full 75.75 MiB. `SalishScene.tsx` starts
coarse: `RESTING_ERROR_TARGET = 32`, `RESTING_MAX_DEPTH = 2`, holding the tree at
L0..L2 (at most 1 + 4 + 16 = 21 tiles, about 19 MiB), then lifts to leaves on the
first user grab or focus journey (`SalishScene.tsx:215-218, 1604-1618`). This is
the W-PERFUX win: about 75% fewer first-paint bytes. A wider extent scales BOTH
the capped startup set and the full leaf set by the area ratio, so the mitigation
does not rescue a widen, it regresses with it.

## 3. Cost of the candidate wider extents (area-scaling applied)

Geometry of the candidates (R1 coords, lng metres at 73.6 km/deg, lat at
111 km/deg):

| Extent | lat span | lng span | area | ratio vs current |
|---|---|---|---|---|
| Current `SAN_JUAN_BOUNDS` | 0.30 deg (33.3 km) | 0.50 deg (36.8 km) | ~1,225 km2 | 1.00x |
| Union bbox (core + PT + BP) | 0.70 deg (77.7 km) | 0.70 deg (51.5 km) | ~4,002 km2 | ~3.27x |
| Admiralty-only box (TB1) | 0.20 deg (22.2 km) | 0.30 deg (22.1 km) | ~491 km2 | ~0.40x |

### 3a. Seam A, one union tileset (core plus PT plus BP in a single quadtree)

Apply the 3.27x area ratio at the same 10 m leaf GSD and the same per-tile budget:

| Quantity | Current | Union estimate |
|---|---|---|
| Total tiles | 85 | ~278 |
| L3 leaves | 64 | ~209 |
| Total payload | 75.75 MiB | ~248 MiB |
| Leaf payload | 56.55 MiB | ~185 MiB |
| Startup-capped set (L0..L2) | ~19 MiB | ~60 MiB (L2 ~52 tiles) |

So a union bake roughly triples both the first-paint capped load (about 19 to
about 60 MiB) and the engaged full-leaf load (about 76 to about 248 MiB). And the
added area is almost entirely empty water and unrelated land in the roughly 45 to
55 km gap between the San Juan core and the two Admiralty nodes, terrain the user
never looks at while watching the core. The cost buys two pinpoint nodes plus a
large low-value surface.

### 3b. Seam B, separate Admiralty-only tileset (two-box)

The Admiralty box alone is about 0.40x the current area, so about 34 tiles and
about 30 MiB if baked at the same GSD. That payload is modest. But it is a SECOND
tileset, not a wider one, and it does not compose with the single-bbox scene
frame (`projectToScene`, one fit, `SCENE_CENTER`). Either the two are placed at
true relative offset inside one `SCENE_WIDTH = 120` frame, which reintroduces the
union-scale framing blowup (R4), or a second projection frame and view are built,
which is a new feature, not an extent widen. The bytes are cheap; the integration
is not.

## 4. Frame-time, not just bytes

RP1 also flags per-frame cost that scales with the streamed leaf set:

- `Water2Rig` runs a full opaque depth pre-pass every frame ahead of the
  auto-render (`SalishScene.tsx:415-426`), so the GPU pays roughly twice per frame
  while geometry arrives. Tripling the streamed triangle count (union seam) makes
  that doubled pass markedly heavier during the stream.
- meshopt decode is real CPU work that scales with leaves pulled. Tripling leaves
  triples decode.
- `enableShadows` is already false at the call site, so shadows are not a current
  cost and must stay false in any wider mount.

No client-tier frame-time number is on hand for this lane. The binding 30 fps
client-tier number is the open question the sibling PRF lane is chartered to
measure; the T4 captures are vsync-capped server-class upper bounds, not the
binding number. So a widen would need a real frame-time budget from PRF before
any proceed, and STX cannot assert "within frame-time budget" without it.

## 5. R3 conclusions for the decision

- The W-PERFUX cost model is leaf-geometry-dominated and area-proportional at a
  fixed 10 m GSD. Tile count, not per-tile weight, is the cost axis.
- A single union tileset widening to reach Port Townsend and Bush Point is about
  a 3.3x load regression: about 19 to about 60 MiB at first paint and about 76 to
  about 248 MiB engaged, most of it empty water and unrelated land between the
  core and the two nodes.
- A separate Admiralty-only tileset is byte-cheap (about 30 MiB) but does not
  compose with the single-bbox scene frame, so it is a second view, not a widen.
- No load-cost or frame-time budget is approved, and the binding client-tier
  frame-time number is unmeasured (PRF lane). STX cannot certify any budget.
- Stated load cost for the build-vs-defer decision: about +172 MiB engaged and
  about +41 MiB at first paint for the union seam, against zero net-new summer
  acoustic value and two nodes that are off-frame at the resting view (R1, R4).

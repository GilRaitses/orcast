# WS-PERF research synthesis (WP1)

Output of the Research wave. Three read-only investigators (T1, T2, T3) named
concrete techniques per track. Two findings change scope and are flagged.

## T1: connection fan-out concurrency

**Technique (recommended): bounded `ThreadPoolExecutor`, not async/httpx.**

- `POST /api/interactions/plan` is a synchronous handler (`interactions.py:154`)
  and every leg uses blocking `requests` (`wsf.py:126`, `wsdot_traffic.py:166`).
  A `ThreadPoolExecutor(max_workers=4)` wrapping the blocking leg calls makes
  wall time approach `max(leg)` instead of `sum(legs)` with no adapter rewrite.
  Async + httpx would force `async def` through the whole planner stack and
  rewrite four source modules: out of scope for the latency target.
- Per-leg timeouts already exist inside `requests` (`_TIMEOUT = 20.0`). Each
  pool task mirrors the existing `try/except -> {} / []` so one failed leg never
  fails the plan.
- The four independent legs for the ferry branch: `predict_eta`,
  `schedule`, `sailing_space`, `vessel_locations`. Matching / feasibility /
  composite-label / freshness assembly stays sequential (CPU-only, order
  sensitive).

## T2: traffic_flows off the request path

**Finding (scope change): `traffic_flows()` is NOT on the request path today.**

- Zero production callers of `traffic_flows()`. It exists in
  `wsdot_traffic.py:230` and is referenced only by unit tests.
- The visiting / here-now drive leg reaches WSDOT only via
  `_corridor_eta_adapter()` -> `corridor_route_ids()` -> `corridor_routes()` ->
  `travel_times()` (`wsdot_traffic.py:265`), which is the ~95 ms call, not the
  ~1.8 s `traffic_flows()`.
- The background poller `tools/corridor_poll.py` also uses `travel_times()`
  only, on a 300 s loop.

**So T2 is a regression guard, not a fix.** The benchmark's 1.8 s number was
`traffic_flows()` measured in isolation; it never reaches a plan turn. The work
is a cheap pytest that PROVES it stays that way (a planned future "northern-leg
congestion" feature, `WS-TRIPS DISCOVERY_MAP:150`, would be the thing that could
wire it in). Bonus finding: the poller calls `travel_times()` twice per cycle
(explicit + via `corridor_route_ids()`); a one-line fix saves ~95 ms/poll, off
the request path.

## T3: tile first-paint LOD

**Finding (premise correction): the live console serves the FULL tileset, not
the 5.9 MB pilot.**

- `SalishScene.tsx:85` mounts
  `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` (85 tiles, 4
  LoD levels, geometricError ladder 160 -> 10 m).
- The **5.9 MB** I measured at acceptance was the obsolete single-tile **pilot**
  (`/3dtwin/pilot/`, `pilot.glb` = 5,856,764 bytes, `PILOT.md:26`). A single-tile
  pilot CANNOT be deferred by any renderer setting; but it is not what the
  console loads. **The full tileset's coarse L0 root is expected to be far
  smaller, so the first-paint baseline must be re-measured against
  `/3dtwin/full/` before T3 commits to a target.**

**Technique (if a real first-paint cost remains on the full tileset):**

- Runtime levers in `web/lib/scene/tiles/useTilesLayer.ts:137-143`: `errorTarget`
  (screen-space error; higher = coarser/fewer tiles first) and `maxDepth`.
  `lruCache`, `downloadQueue`, `displayActiveTiles` are unset and available.
- Republish lever (only if the coarsest published GLB is still too large):
  `infra/3dtwin/host/bake_tree.py` (`LMAX`, decimation stride, `gltfpack`).
- Governance snag: `SalishScene.tsx:744` hard-overrides `errorTarget: 16`, so a
  config-only change needs a one-line phase-B edit to that mount (a collision
  exception against the INTENT/SCENIC/BATHY-owned SalishScene, to be granted by
  the program orchestrator).
- No first-paint byte harness exists. Build one with Playwright + CDP
  `Network.enable`, summing `.glb` content bytes from the first `tileset.json`
  fetch to the first `load-model` event, at the default console camera.

## Gate verdict (WP1)

PASS for T1 (concrete technique + seam). PASS for T2 and T3 with scope
corrections recorded above: T2 is a guard, and T3 requires a re-measurement
step against the full tileset before its target is fixed.

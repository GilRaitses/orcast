# WS-PERF discovery map (WP2)

Output of the Discovery wave. Every file to create or edit, its owner, the
integration seam, and the honesty surfaces that must stay byte-identical.

## One-file-one-owner map

| Track | Create / edit | Owner | Phase | Convergence? |
|-------|---------------|-------|-------|--------------|
| T1 | `src/aws_backend/casting/trips/fanout.py` (NEW pure helper) | T1-A | A | no |
| T1 | `src/aws_backend/casting/trips/connections.py` (wire fan-out) | T1-B | B | YES (single editor) |
| T2 | `tests/aws_backend/test_planner_trips_branch.py` (add guard test) | T2 | A | no |
| T3 | `web/lib/scene/tiles/tilesConfig.ts` (NEW) | T3-A | A | no |
| T3 | `web/lib/scene/tiles/useTilesLayer.ts` (apply config) | T3-B | B | YES (single editor) |
| T3 | `web/app/components/scene/SalishScene.tsx:744` (drop `errorTarget:16`) | T3-B | B | collision exception (see below) |
| T3 | `docs/tileset-publish-notes.md` (NEW, republish lever) | T3-A | A | no |
| T3 | `web/e2e/perf/tile-first-paint.spec.ts` (NEW measurement) | T3-A | A | no |

## T1 seams (connections.py)

- Sequential I/O lives in `plan_connection` ferry branch (`connections.py:717`),
  `_build_drive_leg` (`216`, calls `predict_eta` at `264`), and `_build_ferry_leg`
  (`451`, calls `schedule` `474`, `sailing_space` `497`, `vessel_locations` `507`).
- Phase B splits each `_build_*` into fetch + assemble, runs the four fetches
  through `fanout.fetch_legs_concurrently({...})`, then feeds the results into the
  unchanged assemble/match path.
- Invoked only from `planner.py` visiting / here-now branches via
  `build_connection_plan` -> `plan_connection`.

## T1 honesty surfaces (must stay byte-identical)

- `connections.py:17-28` rules: empty adapter output is "unknown" never "zero".
- unknown-vs-zero points: drive `eta_minutes:None` (`274`), space `None` not `0`
  (`501`, test `test_suppressed_space_count_is_none_not_zero`), vessel `None`
  (`511`), feasibility `verdict:"unknown"` (`602`).
- composite `weakest_label` ignores `None` (`74`); freshness `_youngest` over
  measured stamps only (`724`). Leg output ordering (drive before ferry) must be
  preserved; only fetches parallelize, not the appended `plan["legs"]` order.

## T2 seam (guard test)

- Add `test_visiting_and_here_now_never_call_traffic_flows` to
  `tests/aws_backend/test_planner_trips_branch.py`.
- Wire `predict_eta=_corridor_eta_adapter()` (imported from `planner`), NOT the
  existing `_corridor_adapter` stub, so the real `corridor_route_ids` ->
  `travel_times` path runs.
- Monkeypatch `src.aws_backend.sources.wsdot_traffic.traffic_flows` to raise;
  mock `travel_times` from `tests/aws_backend/fixtures/wsdot_traffic/travel_times.json`;
  run `draft_ui_intent(..., focus={"branch": b, "connection": _connection_intent()})`
  for `b in ("visiting","here-now")`. Assert no raise.

## T3 seam (tiles config)

- `TilesRenderer` built in `useTilesLayer.ts:89`; LOD applied at `137-143`
  (`errorTarget`, `maxDepth`), per-frame `update()` at `171-175`.
- New `tilesConfig.ts` exports typed defaults (`errorTarget`, `maxDepth`, optional
  `lruCache`). `useTilesLayer.ts` applies `options.errorTarget ?? tilesConfig...`.
- **Collision exception required:** `SalishScene.tsx:744` passes `errorTarget:16`,
  overriding the hook. T3-B makes the one-line removal in the same phase-B commit;
  the program orchestrator grants this narrow exception (analogous to the
  AdaptiveExplore.tsx grant in the program charter section 4). T3 touches nothing
  else in SalishScene.
- Measurement: new Playwright spec under `web/e2e/perf/` using CDP `Network.enable`
  to sum `.glb` content bytes to first `load-model`; no harness exists today.

## Pre-implementation blocker (must clear before WP3)

**Re-measure first-paint on `/3dtwin/full/`.** The 5.9 MB baseline was the
obsolete pilot tileset. If the full tileset's coarse root is already < 1.5 MB at
the default camera, T3 reduces to "add the measurement spec + confirm" and the
LOD tuning is unnecessary. This re-measurement is the WP2 exit condition for T3.

## Gate verdict (WP2)

PASS. Every file owned; two convergence files named (`connections.py`,
`useTilesLayer.ts`) with single phase-B editors; one narrow SalishScene collision
exception identified for operator grant; honesty surfaces enumerated; the T3
re-measurement blocker recorded.

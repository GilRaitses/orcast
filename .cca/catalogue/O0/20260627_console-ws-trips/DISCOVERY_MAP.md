# WS-TRIPS discovery map

Grounds the research in this codebase: the exact structure, seams, the
one-file-one-owner table, and the honesty map. Read-only wave. The gate is a map
where every created/edited file has an owner and an integration seam, with no
unowned convergence-file edits.

## 1. planner.py structure and the branch seam

`src/aws_backend/casting/planner.py`:
- `draft_ui_intent(agent, message, *, viewport, focus)` (`planner.py:28`) is the
  deterministic core. Today it keyword-matches `message` into one of four
  hard-coded skill/panel sets (decision/audit, dossier/review, promotion, else
  default) (`planner.py:41-67`), then layers map panels when a lat/lng is present
  (`planner.py:69-96`), filters `skill_plan` to `agent.skills` (`planner.py:98-99`)
  and `panels` to `agent.policy.allowed_panels` or the registry fallback
  (`planner.py:101-102`), and returns the `ui_intent` dict (`planner.py:109-118`).
- `plan_interaction(...)` (`planner.py:140`) resolves the agent, calls
  `draft_ui_intent`, validates (`validate_ui_intent` `planner.py:127`), executes the
  skill plan via `prepare_interaction_with_skills` (concierge), inserts a
  `plan_output` step, and returns `PlanResult(ui_intent, prepare, resolved_spec_hash)`.

The branch seam: the orienting question (visiting / here-now / kayak / curious) is
a NEW branch dimension that does not exist today. It enters `draft_ui_intent`
before the keyword block. Cleanest seam: read an explicit branch signal from the
turn (a `focus.branch` field, or a `surface_state` field on `PlanRequest`
`interactions.py:122-123`) and, when present, dispatch to a per-branch
skill/panel builder; fall back to today's keyword rules when absent. The four
`JourneyBranch` values already exist as the contract (`web/lib/trips/model.ts:23`),
so the branch strings are fixed. `planner.py` is the single phase-B editor for
this seam (B.8, charter section 4).

## 2. How skills / panels register (the multi-file registration seam)

A panel id must clear THREE gates before it renders, plus a label and a renderer.
This is wider than "register in ActiveSurfaceHost" and is the key discovery
finding:

1. `src/aws_backend/casting/panel_registry.json` — the id must be a known panel
   (`panels.py:24-42` raises `invalid_panels` otherwise). Currently 8 panels;
   none of the trips panels exist.
2. `src/aws_backend/casting/seeds/surface-planner-v1.json` — the id must be in the
   planner agent's `policy.allowed_panels` (`planner.py:101-102`, seed lines
   25-34). Same for any NEW skill in `skills` (lines 5-13).
3. `src/aws_backend/casting/skills_manifest.json` — if a branch runs a NEW skill
   (e.g. a connections skill), it must be a known, enabled, correctly-tiered skill
   (`manifest.py:58-78`; `validate_skill_plan` `policy.py:14`). T0/T1 stay
   anonymous-public; T2/T3 are keyed-only (`interactions.py:170`, `manifest.py:71`).
4. `web/app/components/ActiveSurfaceHost.tsx` — `renderPanel()` switch
   (`ActiveSurfaceHost.tsx:117-158`) needs a `case` per new panel id, or it renders
   `null` (`ActiveSurfaceHost.tsx:155`).
5. `web/lib/uiIntent.ts` — `PANEL_LABELS` (`uiIntent.ts:41-51`) for the panel's
   display label; sidebar panels render via `sidebarPanels` (`uiIntent.ts:79`),
   `surface: "map" | "sidebar"` (`uiIntent.ts:6`). Trips panels are `sidebar`
   except `map_viewport` which already exists.

Decision for the operator: items 1-3 and 5 are registry/seed/label files NOT
listed in the W3 locked edit set (which names only `planner.py` and
`ActiveSurfaceHost.tsx`). To keep one-file-one-owner clean and avoid a phase-A
collision, this map assigns all of them to the phase-B editor (Agent E), since
they co-register the same panels the planner emits and the host renders. Confirm
or split (section 5).

## 3. How the connections planner consumes the W2 clients + corridor model

`connections.py` `plan_connection(intent)` (to build) is pure assembly over
existing adapters; it owns no I/O of its own:
- ferries: `wsf.schedule`, `wsf.sailing_space`, `wsf.vessel_locations`,
  `wsf.routes` / `wsf.terminals` for id resolution (`wsf.py:326-421`).
- road: `wsdot_traffic.travel_times`, `wsdot_traffic.corridor_routes` /
  `corridor_route_ids` (`wsdot_traffic.py:222-293`).
- modeled future ETA: `modeling/traffic/corridor.py` `predict_eta` (to build).
- flights/seaplane: `sources/flights.py` + `sources/seaplane.py` (to build).
All W2 read helpers degrade to `[]` / `{}` when `WSDOT_ACCESS_CODE` is absent
(`wsf.py:10-12`, `wsdot_traffic.py:222-235`), so the planner must treat empty
inputs as "unknown, not zero" and label the leg accordingly. Output is a
structured plan dict (per-leg label + composite label + freshness stamp) that the
phase-B editor attaches to the `connections_plan` panel `props`.

## 4. The interactions route turn shape

`POST /api/interactions/plan` (`interactions.py:154`) takes a `PlanRequest`
(`session_id`, `message`, `agent_id`/inline `agent`, `viewport`, `focus`, optional
`surface_state`, `narrate`) (`interactions.py:35-128`), requires Aurora
(`_require_aurora`), enforces `public_route` (anonymous = no keyed T2/T3 skills,
`interactions.py:170`), calls `plan_interaction`, and returns `_plan_response`
(`interactions.py:131-151`): `ui_intent` + `prepare` (context, citations,
deep_links, tools_used, steps, annotations). The browser builds panels from
`ui_intent.panels` and pulls panel data from `prepare.context`
(`ActiveSurfaceHost.tsx:123`). So connection/kayak/sidequest data reaches the
panel either as `panel.props` (set in `planner.py` when drafting the intent) or
inside `prepare.context` (set by an executed skill). The branch carries no new
route; it rides the existing plan turn. A real plan turn read at acceptance is
the validation bar (`W3_DISPATCH.md:54-56`); no live external calls in CI.

## 5. One-file-one-owner table

### CREATE (phase A, parallel producers)

| File | Owner | Seam | Notes |
|------|-------|------|-------|
| `src/aws_backend/casting/trips/__init__.py` | A (Connections Planner) | new package marker | trivial; created with connections.py |
| `src/aws_backend/casting/trips/connections.py` | A (Connections Planner) | exports `plan_connection(intent)`; consumes wsf, wsdot_traffic, corridor, flights, seaplane | pure assembly; no I/O of its own |
| `src/aws_backend/sources/flights.py` | A2 (Flight + Seaplane Source) | contract at `CONNECTIONS_RESEARCH.md:232-241`; OpenSky via `OPENSKY_PROXY_URL` | NOT in the original W3 edit list; split from A to keep one file one owner |
| `src/aws_backend/sources/seaplane.py` | A2 (Flight + Seaplane Source) | `seaplane_schedule()` static published table | no network |
| `modeling/traffic/__init__.py` | B (Corridor Traffic Model) | new package marker | created with corridor.py |
| `modeling/traffic/corridor.py` | B (Corridor Traffic Model) | exports `predict_eta(depart_dt)`; fits on `data/external/traffic_corridor/seatac_anacortes.jsonl` | history is live + accruing |
| `web/app/components/console/KayakPanel.tsx` | C (Kayak Panel) | renders from kayak-branch panel props / a tide endpoint | reuse `modeling/tide_*` via backend (see kayak tide seam) |
| `web/app/components/console/SidequestPanel.tsx` | D (Sidequests + Auth Chip) | renders sidequests; the chip emits an auth action; reuse `GatedAction` (`ui/GatedAction.tsx`) | does NOT edit ActiveSurfaceHost or planner |

### EDIT (phase B, single editor = Agent E, Trips Planner Branch)

| File | Owner | Seam | Notes |
|------|-------|------|-------|
| `src/aws_backend/casting/planner.py` | E | add the orienting-question branch + per-branch skill/panel selection; wire `plan_connection` into visiting / here-now | CONVERGENCE FILE, single editor (B.8) |
| `web/app/components/ActiveSurfaceHost.tsx` | E | add `renderPanel` cases for `compare_places`, `local_area`, `connections_plan`, `kayak_plan`, `sidequests`; mount `KayakPanel` / `SidequestPanel` | CONVERGENCE FILE (charter section 4) |
| `src/aws_backend/casting/panel_registry.json` | E | register the new panel ids | registry co-edit (decision: assign to E) |
| `src/aws_backend/casting/seeds/surface-planner-v1.json` | E | add new panel ids to `allowed_panels` (+ any new skill to `skills`) | seed co-edit (decision: assign to E) |
| `src/aws_backend/casting/skills_manifest.json` | E | add any NEW trips skill (only if a branch runs one) | may be unnecessary if connections rides panel props |
| `web/lib/uiIntent.ts` | E | add `PANEL_LABELS` entries for the new panels | label-only edit |

No producer edits a convergence file. All convergence + registry/seed/label edits
are serialized into the single phase-B editor.

## 6. Kayak tide seam (decision)

`modeling/tide_harmonic.py` / `tide_phase.py` are Python; `KayakPanel.tsx` is the
browser. There is no HTTP route exposing tide/current windows for a launch point
today (confirmed: no tide endpoint in `routers/`). Two options:
- (a) compute windows server-side in the kayak branch (in `planner.py` prepare or
  a small helper that wraps `modeling/tide_*`) and pass them as `kayak_plan` panel
  `props` — no new route, keeps the panel a pure renderer. Preferred.
- (b) add a dedicated tide-window endpoint the panel fetches (like
  `HydrophoneSignalPanel` fetches `/api/be/...` `HydrophoneSignalPanel.tsx:41`) —
  more code, a new router file (a NEW owner outside the locked set).
Recommend (a). Flag for the operator if a fetch-based panel is preferred.

## 7. Honesty map (every connections field labeled)

| Field / signal | Source | Label |
|----------------|--------|-------|
| Sailing departure / arrival times | `wsf.schedule` | published/measured |
| Drive-up / reservable space counts | `wsf.sailing_space` (`drive_up_space_count`, `reservable_space_count`; `None` when `display_*` false) | measured (~5 s) |
| Live vessel position + ETA | `wsf.vessel_locations` (`eta`, `eta_basis`) | measured (~5 s) |
| Wait-time notes | `wsf.wait_times` (`wait_time_notes` free text) | heuristic/advisory (never parsed to a number) |
| Southern I-5 leg current vs typical | `wsdot_traffic.travel_times` (`current_time` / `average_time`) | measured (realtime) |
| Future-departure corridor ETA + interval | `corridor.predict_eta` basis `modeled_history` | modeled |
| Future-departure ETA, thin history | `corridor.predict_eta` basis `modeled_synthetic_bootstrap` | modeled (synthetic, clearly flagged) |
| Arlington -> Anacortes (northern) leg | always modeled; TravelTimes ends ~MP 208 | modeled (measured absence) |
| Northern-leg congestion color | `wsdot_traffic.traffic_flows` where a station exists | heuristic (best-effort, not a duration) |
| SeaTac flight board | `flights.skylink_board` | published/measured |
| Live aircraft position cue | `flights.opensky_states` (via off-AWS proxy) | measured (position only, no schedule) |
| Seaplane times | `seaplane.seaplane_schedule` | published (static, not live) |
| Kayak tide / current windows | `modeling/tide_*` harmonic predictor | modeled (measured-anchored only where NOAA currents exist) |
| Whale forecast on the map | hotspot heuristic + `effective_confidence` gate | unchanged; no ML promoted (B.9) |

Composite plan label = the weakest label on the path used (measured > published >
modeled > heuristic), with a freshness stamp from the youngest measured source.
The northern-leg gap is surfaced explicitly, never hidden. No forecast promotion.

## 8. Lazy-rollup foot-gun (carried)

`web/lib/trips/model.ts` rolls up `totalCost` / `overallProbability` / `confidence`
only in `addDay` / `addDayTrip` (`model.ts:503-565`); `addStop` / `addActivity` /
`addViewingZone` do not. Any code that builds a Trip for a panel MUST call
`updateTripMetadata(trip)` (and `updateDayMetadata` per day) before serializing,
or the served totals are stale. This binds the visiting / here-now / kayak
producers and the phase-B editor.

## Discovery gate

Met. Every file to create or edit has an owner and a seam, no producer touches a
convergence file, and the registry/seed/label co-edits are serialized into the
single phase-B editor with the open decisions flagged (sections 2, 5, 6).

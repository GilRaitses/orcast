# WS-TRIPS research synthesis

Grounded in the repo at HEAD on 2026-06-27. Every claim cites a file/line or a
provider field already finalized in `../20260627_console-journey-trips/CONNECTIONS_RESEARCH.md`.
This wave is read-only; no code or config was written.

## 0. What already exists (the foundation this builds on)

- Trip hierarchy types + branch enum: `web/lib/trips/model.ts` (W1 Agent F port of
  `js/agentic/trip-hierarchy-model.js`). `JourneyBranch = 'visiting' | 'here-now' |
  'kayak' | 'curious'` (`model.ts:23`, `JOURNEY_BRANCHES` `model.ts:26`).
- Deterministic surface planner: `src/aws_backend/casting/planner.py`
  `draft_ui_intent()` — keyword rules, no LLM tool picking (`planner.py:28-118`).
- Turn shape + route: `src/aws_backend/routers/interactions.py` `POST
  /api/interactions/plan` (`interactions.py:154`), returns `ui_intent` + executed
  `prepare`. The browser renders `ui_intent.panels` via
  `web/app/components/ActiveSurfaceHost.tsx` `renderPanel()` (`ActiveSurfaceHost.tsx:117`).
- Panel + skill allow-lists: `src/aws_backend/casting/panel_registry.json`,
  `src/aws_backend/casting/skills_manifest.json`, and the planner agent seed
  `src/aws_backend/casting/seeds/surface-planner-v1.json` (`allowed_panels`,
  `skills`).
- DONE W2 clients: `src/aws_backend/sources/wsf.py` (ferries) and
  `src/aws_backend/sources/wsdot_traffic.py` (road traffic + the appendable
  history log).
- Tide/current model surface: `modeling/tide_harmonic.py` (`HarmonicTide`) and
  `modeling/tide_phase.py` (`TidalPhase`, `HarmonicTidalPhase`).
- Camera Director (kayak camera): `web/lib/scene/camera/director.ts`
  `createCameraDirector` exposes `descendTo`, `orbit(center, radius, speed, {altitudeMeters})`.

NOT yet present (greenfield for WS-TRIPS, confirmed by glob):
`src/aws_backend/casting/trips/`, `modeling/traffic/`,
`src/aws_backend/sources/flights.py`, `src/aws_backend/sources/seaplane.py`,
`web/app/components/console/KayakPanel.tsx`,
`web/app/components/console/SidequestPanel.tsx`.

## 1. Branch design (orienting question -> branch -> panels)

The orienting question routes a visitor into one of four `JourneyBranch` values
(`model.ts:15-26`). Each branch selects a skill plan + a panel set. The planner
already filters panels against the agent allow-list and the registry
(`planner.py:101-107`, `panels.py:24-42`), so each new branch panel must be
registered (see DISCOVERY_MAP section "panel registration seam").

| Branch | Intent | Skill plan (proposed) | Panels emitted | Camera |
|--------|--------|-----------------------|----------------|--------|
| `visiting` | Compare places / plan a trip to the Salish Sea (broad) | `fetch_hotspots`, `fetch_gates`, connections | `map_viewport` (archipelago bounds), `compare_places` (per-place forecast + connection summary), `connections_plan`, `explore_trace` | high establishing orbit over the archipelago |
| `here-now` | Already in the area, local-area planning (focused) | `fetch_hotspots`, `fetch_provenance`, `fetch_gates`, connections | `map_viewport` (tight bounds), `local_area` (nearby viewing zones + today's remaining sailings), `connections_plan`, `provenance_pin` | `descendTo` the local area |
| `kayak` | Paddle-focused, short-range, water-hugging | `fetch_hotspots`, `fetch_environmental` | `kayak_plan` (launch points, tide/current windows, short-range zones, safety), `map_viewport` | `descendTo` low altitude then `orbit` at small radius (water-hugging) |
| `curious` | Sidequests / exploratory, not committed to a trip | `fetch_live_hydrophones`, `fetch_verified_sightings`, `fetch_provenance` | `sidequests` (hydrophone listen, replay a sighting, explain a cell score) + inline auth chip, `hydrophone_signal`, `provenance_pin` | free / ambient |

Notes:
- `visiting` and `here-now` are the two branches that consume the connections
  planner (W3 dispatch Agent E). `visiting` answers the broad "which place, can I
  get there"; `here-now` answers "what is reachable from where I am today".
- `kayak` does NOT call connections (no ferry/flight leg); it calls the tide model.
- `curious` ends each sidequest by inviting the user into the trip platform (the
  auth chip), per W3 dispatch Agent D.
- The forecast panels stay on the hotspot heuristic and its `effective_confidence`
  gate (`ActiveSurfaceHost.tsx:27-63` GatesSummaryPanel reads `effective_confidence`);
  no ML is promoted (B.9).

## 2. Connection-feasibility reasoning

"Make your sailing / flight." Given an intent (depart X at time T, reach the
islands or return for a flight), combine measured + modeled + published legs into
one plan with a per-leg honesty label, a composite label, and a freshness stamp.

### Inputs and the function each plays

1. WSF schedule — `wsf.schedule(route_id, date)` (`wsf.py:348`). Candidate
   sailings for the date/route; `departing_time` / `arriving_time` per terminal
   combo, plus `annotation_indexes -> annotations` for "reservations required /
   tidal cancellation" notes. Label published/measured.
2. WSF sailing space — `wsf.sailing_space(terminal_id)` (`wsf.py:360`). Per
   departure + arrival terminal, `drive_up_space_count` / `reservable_space_count`
   (suppressed to `None` when the `display_*` flag is false; `wsf.py:185-204`).
   This is the headline trip signal ("will the 6:30 to Friday Harbor have drive-up
   room"). Label measured, ~5 s freshness.
3. WSF vessel locations — `wsf.vessel_locations()` (`wsf.py:326`). Live position +
   `eta` and `eta_basis` (the honesty source for the ETA; `wsf.py:163-165`). Label
   measured, ~5 s freshness.
4. WSDOT realtime road — `wsdot_traffic.travel_times()` (`wsdot_traffic.py:222`)
   and `corridor_routes()` / `corridor_route_ids()` (`wsdot_traffic.py:251,282`).
   `current_time` vs `average_time` for the southern I-5 legs now. Label measured.
5. Modeled future-departure ETA — `modeling/traffic/corridor.py` `predict_eta(depart_dt)`
   (to build). For a future departure the southern legs are predicted, and the
   northern Arlington -> Anacortes leg is always modeled. Label modeled.
6. Flights — `src/aws_backend/sources/flights.py` (to build, contract at
   `CONNECTIONS_RESEARCH.md:232-241`): `skylink_board('SEA')` (SeaTac board,
   published/measured), `opensky_states(bbox)` (live positions, measured, via the
   off-AWS proxy `OPENSKY_PROXY_URL`), and `seaplane_schedule()` from
   `src/aws_backend/sources/seaplane.py` (published static table, no network).

### Composite honesty label

Each leg keeps its own label. The plan's composite label is the WEAKEST label on
the path actually used, in the order measured > published > modeled > heuristic.
So:
- "The 6:30 Anacortes -> Friday Harbor sailing shows N drive-up spaces" is measured
  with a freshness stamp (`CONNECTIONS_RESEARCH.md:263`).
- "Leaving SeaTac at 3 pm Friday, expect about 2 h 05 m +/- 30 m to Anacortes" is
  modeled overall: the southern legs lean on measured `current_time` only when the
  departure is roughly now, and the Arlington -> Anacortes leg is always modeled
  (`CONNECTIONS_RESEARCH.md:266-268`).
- Seaplane times are published, not live (`CONNECTIONS_RESEARCH.md:269`).
The freshness stamp is the youngest `time_updated` / `timestamp` across the
measured sources used.

### The measured-coverage gap on the northern leg (honest absence)

WSDOT TravelTimes coverage on I-5 ENDS near Arlington (~MP 208). There is NO
TravelTimes route for Arlington -> Mount Vernon -> Burlington (~MP 230) and SR 20
west to Anacortes (`CONNECTIONS_RESEARCH.md:126-132`). `wsdot_traffic.py` enforces
this in code: `CORRIDOR_ROUTE_NAMES` stops at `Everett-Arlington`
(`wsdot_traffic.py:67-73`) and `corridor_routes()` surfaces only routes the feed
returns (`wsdot_traffic.py:251-279`); a test asserts the northern leg is never
implied (`test_wsdot_traffic.py:197-207`). So the connections planner must label
the final ~40 miles modeled, never measured, and treat any `TrafficFlow`
congestion that far north as best-effort heuristic, not a duration.

## 3. Corridor ETA model approach (`modeling/traffic/corridor.py`, to build)

Goal: `predict_eta(depart_dt) -> {eta, interval, basis}` for the SeaTac -> Anacortes
corridor, fit on the now-accruing history.

### Data

The history log is live and gitignored: `data/external/traffic_corridor/seatac_anacortes.jsonl`
(`wsdot_traffic.py:79-87`, `history_path()` `wsdot_traffic.py:300`). Each row is
one travel-time reading appended by `append_history()` (`wsdot_traffic.py:305-323`)
with `travel_time_id`, `name`, `current_time`, `average_time`, `time_updated`, and
an added UTC `logged_at` (so rows are time-ordered).

### Model

- Per measured segment (`travel_time_id`), fit a time-of-day x day-of-week model
  on `current_time`. A simple, defensible form: bucket by hour-of-day (or coarser
  3-hour bins) crossed with weekday vs weekend, taking the bucket mean and the
  empirical residual spread. This beats a flat mean when the corridor has a
  commute profile, which is the W3 acceptance bar (`W3_DISPATCH.md:28`).
- Corridor total for a future departure = sum of southern measured-segment
  predictions (propagated forward in time as the vehicle moves north) + a MODELED
  estimate for the unmeasured Arlington -> Anacortes leg (free-flow distance /
  speed, optionally uplifted by `TrafficFlow` congestion where a station exists,
  labeled heuristic).
- `interval`: a prediction interval from the per-bucket residual quantiles (e.g.
  empirical 10th/90th), or a normal approximation mean +/- 1.96 sigma per bucket,
  summed across legs.
- `basis`: one of `measured_current` (departure ~ now and the live feed is up),
  `modeled_history` (enough history rows in the relevant buckets), or
  `modeled_synthetic_bootstrap` (history thin).

### Synthetic-bootstrap fallback (thin history)

When a bucket has too few rows (threshold to be set, e.g. < 8), fall back to a
synthetic baseline: bootstrap from `average_time` plus a plausible hour-of-day
congestion multiplier distribution, producing an ETA + interval clearly labeled
`modeled_synthetic_bootstrap` (`CONNECTIONS_RESEARCH.md:134-146`, W3 dispatch
Agent B). It is never presented as measured. The northern leg is modeled in every
basis (there is no measured option for it).

### Validation

pytest on a recorded history fixture; the bucketed model beats a flat-mean
baseline on held-out days (`W3_DISPATCH.md:23-29`). No live calls in CI.

## 4. Kayak tide / current windows (reuse the existing surface)

The existing tide/current model surface in the repo is `modeling/tide_harmonic.py`
+ `modeling/tide_phase.py`. Reuse it; do not invent a new one.

- `HarmonicTide` (`tide_harmonic.py:31`) fits a fixed astronomical constituent
  basis (M2/S2/N2/K1/O1 + mean) by least squares and exposes `predict()`,
  `phase()` (M2-derived tidal phase in [0,1)), and `reconstruction_r2`.
- `TidalPhase` (`tide_phase.py:27`) maps timestamps to a tidal phase anchored at
  flood-current onset (upward zero-crossing of signed current velocity
  `Velocity_Major`; falls back to rising water-level mean-crossing).
- `HarmonicTidalPhase` (`tide_phase.py:96`) fits the constituents from `{t, value}`
  current records and predicts phase for ANY timestamp; `from_records()` returns
  `None` when there are too few samples (`min_samples=24`), so the caller falls
  back to onset-based `TidalPhase` (`tide_phase.py:123-155`). It is a drop-in
  (same `phase` / `phases` / `value_at` / `onsets` interface).

How the kayak windows derive from it:
- Slack windows sit near tidal phase ~0 (flood onset) and ~0.5 (the ebb turn);
  strong-current windows sit mid-flood / mid-ebb. The harmonic predictor gives the
  signed current proxy at any time, so the panel can mark "good paddle window"
  (low current near slack) vs "avoid" (peak current) for a launch point's day.
- Honesty label: this is a HARMONIC PREDICTOR, not observed current measurements
  (`tide_harmonic.py:1-6` docstring). So kayak windows are MODELED. Where NOAA
  current observations exist (`Velocity_Major`, fed e.g. from
  `src/aws_backend/sources/noaa.py`), the fit is anchored to measured onsets; with
  too few samples it is harmonic-only. Label modeled either way; never claim
  measured current.

Cross-language seam: the tide model is Python (`modeling/`) and `KayakPanel.tsx`
is the browser. So the panel cannot import the model directly; it needs the
windows delivered as panel `props` (assembled server-side) or via a small backend
endpoint. See DISCOVERY_MAP section "kayak tide seam" — this is a decision for the
operator because no HTTP route exposes tide windows today.

Camera for kayak: `director.ts` `descendTo(lowAltitude)` then
`orbit(center, smallRadius, speed, {altitudeMeters})` (`director.ts:265,347`). The
no-dunk clamp (`director.ts:146-157`) keeps the low water-hugging orbit above the
wave crests automatically.

## 5. The lazy-rollup foot-gun (carried into implementation)

`web/lib/trips/model.ts` recomputes `totalCost`, `overallProbability`, and
`confidence` ONLY inside `addDay()` and `addDayTrip()` (which call
`updateTripMetadata` / `updateDayMetadata`, `model.ts:527,562`). `addStop()`,
`addActivity()`, and `addViewingZone()` do NOT trigger a rollup
(`model.ts:567-676`). So a trip whose stops/activities/zones were added after the
last `addDay`/`addDayTrip` will serve STALE `totalCost` / `overallProbability`
(zero or last-computed). Anyone assembling a Trip to feed a panel MUST call
`updateTripMetadata(trip)` (and `updateDayMetadata` per day) immediately before
serializing. This is carried as an explicit implementation note for the visiting /
here-now / kayak producers and the phase-B editor.

## Research gate

Met. Concrete techniques named (bucketed time-of-day x day-of-week corridor model
with empirical prediction interval and a labeled synthetic-bootstrap fallback;
harmonic-tide reuse for kayak windows; composite weakest-label honesty), and the
concrete in-repo sources the implementation will use are all cited above.

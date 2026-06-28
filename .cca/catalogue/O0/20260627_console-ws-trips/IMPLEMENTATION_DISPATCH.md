# WS-TRIPS implementation dispatch — PROPOSED

Status: PROPOSED. Held for the program orchestrator to gate. Discipline (charter
sections 3-4, locked B.8/B.10): one file one owner; `planner.py` and the
`ActiveSurfaceHost.tsx` panel registry have a single phase-B editor; no dev server
during phase A; validate with type-check / pytest on fixtures; a real planner turn
read only at acceptance; NO live external calls in CI; producers commit / deploy /
promote nothing. Depends on WS-INTENT landing the live surface before phase B.

## Sequencing

- Phase A (parallel producers, no convergence files): A Connections Planner,
  A2 Flight + Seaplane Source, B Corridor Traffic Model, C Kayak Panel,
  D Sidequests + Auth Chip.
- Phase B (single editor): E Trips Planner Branch wires the orienting question +
  per-branch panels into `planner.py` and registers panels across the host +
  registry + seed + labels. Runs after phase A is green.

Hard ordering: A2 lands before A is validated end-to-end (A imports flights /
seaplane). B is independent of A. E runs last and after WS-INTENT.

---

## Agent A — Connections Planner (phase A)

OWNS: `src/aws_backend/casting/trips/__init__.py`,
`src/aws_backend/casting/trips/connections.py`.

TASK: Build "make your sailing / flight" reasoning. `plan_connection(intent)`
combines WSF schedule + sailing space + live vessel ETA + WSDOT realtime corridor
+ the modeled future-departure ETA + the flight board into one structured plan
with a per-leg honesty label, a composite label (weakest of measured > published >
modeled > heuristic), and a freshness stamp from the youngest measured source.
Consume the W2 clients (`sources/wsf.py`, `sources/wsdot_traffic.py`), the
corridor model (`modeling/traffic/corridor.py`, Agent B), and the flight/seaplane
adapters (`sources/flights.py` + `sources/seaplane.py`, Agent A2). Treat empty
adapter output as "unknown", never "zero". Surface the northern Arlington ->
Anacortes leg as modeled, never measured.

DELIVERABLES: `connections.py` exporting `plan_connection(intent)`.

VALIDATION: pytest on fixtures answering "depart SeaTac 3 pm Friday, catch the
6:30 Anacortes sailing?" returning a labeled feasibility + interval. Mock all
adapters; no live calls. Assert the composite label is modeled when the plan uses
a future corridor ETA, and that the northern leg is never labeled measured.

COLLISION-AVOIDANCE: own ONLY the `trips/` package files. Do not touch planner.py,
the host, the registry, the seed, or the W2 clients.

RETURN: diff + pytest output.

## Agent A2 — Flight + Seaplane Source (phase A)

OWNS: `src/aws_backend/sources/flights.py`, `src/aws_backend/sources/seaplane.py`.

TASK: Implement the adapter contracts finalized at `CONNECTIONS_RESEARCH.md:232-247`.
`flights.py`: `opensky_states(bbox)` (measured live positions, fetched through the
off-AWS proxy `OPENSKY_PROXY_URL`; never call OpenSky directly from AWS),
`skylink_board(airport_iata, direction)` (published/measured SeaTac board,
cache-friendly), `aviationstack_flights(...)` (published fallback), `flight_status(...)`.
`seaplane.py`: `seaplane_schedule(route, day)` reading a curated published static
table with a stamped source date (no network). All read helpers degrade
gracefully (empty / None) when creds are absent, mirroring `wsf.py` / `wsdot_traffic.py`.

DELIVERABLES: `flights.py` + `seaplane.py` with the contract signatures.

VALIDATION: pytest on recorded/sanitized fixtures (OpenSky positional array parse
by index; SkyLink board fields; seaplane static rows). Assert graceful empty
return when env creds are unset, and that no secret leaks into a log string. No
live calls.

COLLISION-AVOIDANCE: own ONLY these two source files.

RETURN: diff + pytest output.

## Agent B — Corridor Traffic Model (phase A)

OWNS: `modeling/traffic/__init__.py`, `modeling/traffic/corridor.py`.

TASK: Fit a time-of-day x day-of-week model on the WSDOT travel-time history log
(`data/external/traffic_corridor/seatac_anacortes.jsonl`, via
`wsdot_traffic.history_path()`) per measured segment, and predict a future-departure
corridor ETA with a prediction interval. `predict_eta(depart_dt) -> {eta, interval,
basis}` where basis is `measured_current` / `modeled_history` /
`modeled_synthetic_bootstrap`. Sum the southern measured-segment predictions and
add a MODELED free-flow estimate for the unmeasured Arlington -> Anacortes leg.
When a bucket is thin, fall back to a synthetic-bootstrap baseline clearly labeled
`modeled_synthetic_bootstrap`, never presented as measured.

DELIVERABLES: `corridor.py` exporting `predict_eta(depart_dt)`.

VALIDATION: pytest on a recorded history fixture; the bucketed model beats a
flat-mean baseline on held-out days (report the held-out skill number). Assert the
thin-history path returns the synthetic-bootstrap basis label and the northern leg
is always modeled.

COLLISION-AVOIDANCE: own ONLY `modeling/traffic/`. Read `wsdot_traffic.history_path()`;
do not edit `wsdot_traffic.py`.

RETURN: diff + pytest output + the held-out skill number.

## Agent C — Kayak Panel (phase A)

OWNS: `web/app/components/console/KayakPanel.tsx`.

TASK: A console panel for the kayak branch: launch points, tide / current windows
(reuse the existing `modeling/tide_harmonic.py` / `tide_phase.py` surface; windows
arrive as panel props per the recommended server-side option, DISCOVERY_MAP
section 6), short-range viewing zones, and safety framing. Label tide/current
windows MODELED (harmonic predictor, not observed currents). Camera stays low and
water-hugging (the branch calls `director.descendTo` + `orbit` at a small radius;
the panel does not own the camera).

DELIVERABLES: `KayakPanel.tsx` rendering from a sample kayak-branch panel-props
shape.

VALIDATION: `cd web && npm run build` type-check; render from a sample kayak panel
props fixture; read the rendered screenshot to confirm windows + safety framing +
the modeled label. No dev server during phase A beyond a local render check.

COLLISION-AVOIDANCE: do NOT edit `ActiveSurfaceHost.tsx` (Agent E registers panels)
or `planner.py`.

RETURN: diff + inspected screenshot.

## Agent D — Sidequests + Auth Chip (phase A)

OWNS: `web/app/components/console/SidequestPanel.tsx` (+ the inline confirm chip).

TASK: Curiosity-branch pairing prompts (listen to a hydrophone, replay a recent
sighting, explain a cell score) that each end by inviting the user into the trip
platform. Plus a single inline confirm chip that authorizes a charter / wave from
within the chat slot without leaving the scene. Reuse `ui/GatedAction.tsx` for the
anonymous-first gating pattern (ghosted button + sign-in tooltip).

DELIVERABLES: `SidequestPanel.tsx` + the confirm chip.

VALIDATION: type-check; render sidequests; the chip emits an auth action on the
turn. Read the rendered screenshot.

COLLISION-AVOIDANCE: do NOT edit `ActiveSurfaceHost.tsx` or `planner.py`.

RETURN: diff + inspected screenshot.

## Agent E — Trips Planner Branch (phase B; SINGLE editor)

OWNS (serialized, single editor): `src/aws_backend/casting/planner.py`,
`web/app/components/ActiveSurfaceHost.tsx`,
`src/aws_backend/casting/panel_registry.json`,
`src/aws_backend/casting/seeds/surface-planner-v1.json`,
`src/aws_backend/casting/skills_manifest.json` (only if a new skill is added),
`web/lib/uiIntent.ts`.

TASK: Add the orienting question (visiting / here-now / kayak / curious) to
`draft_ui_intent` via an explicit branch signal on the turn (a `focus.branch` /
`surface_state` field), branching the skill plan + panels: compare-places (broad),
local-area (focused), kayak, sidequest (per RESEARCH_SYNTHESIS section 1). Wire
`connections.plan_connection` into the visiting / here-now branches and attach the
plan to the `connections_plan` panel props with its honesty labels + freshness
stamp. Register every new panel id across the registry, the seed `allowed_panels`,
the `uiIntent` labels, and `ActiveSurfaceHost.renderPanel` (mounting `KayakPanel`
/ `SidequestPanel`). Before serializing any Trip object to a panel, call
`updateTripMetadata` / `updateDayMetadata` (the lazy-rollup foot-gun,
RESEARCH_SYNTHESIS section 5). Keep the forecast on the hotspot heuristic; promote
no ML.

DELIVERABLES: edits to the files above.

VALIDATION: a real `POST /api/interactions/plan` turn for each of the four
branches returns a coherent panel set; the visiting branch returns a connections
plan with per-leg + composite honesty labels and a freshness stamp. Read the four
responses. Backend pytest stays on fixtures; the live planner turn is an
acceptance-time read, not a CI live call.

COLLISION-AVOIDANCE: you are the ONLY editor of `planner.py` and the panel
registry; run after phase A is green and after WS-INTENT has landed the live
surface. Do not edit any phase-A producer file.

RETURN: diff + the four branch responses you inspected.

## Open decisions for the operator (gate before fan-out)

1. Ownership of the registry/seed/label co-edits (panel_registry.json,
   surface-planner-v1.json, skills_manifest.json, uiIntent.ts). Proposed: all to
   Agent E to preserve one-file-one-owner. Confirm or split into a registrar agent.
2. Kayak tide delivery: server-side props (recommended, no new route) vs a new
   tide-window endpoint (new router owner). Proposed: server-side props.
3. Connections as panel props vs a new skill: if a NEW skill is added to
   `skills_manifest.json`, set its tier (T0/T1 to keep the anonymous-public route
   working; T2/T3 would gate it to keyed reviewers only). Proposed: ride panel
   props, no new skill, so no manifest edit.
4. Flight/seaplane sources (`flights.py`, `seaplane.py`) were not in the original
   W3 edit list. Proposed: split into Agent A2 so Agent A stays a single owner.
   Confirm the OpenSky off-AWS proxy (`OPENSKY_PROXY_URL`) and the SkyLink /
   AviationStack free-tier keys are acceptable, or scope flights to seaplane +
   board-only for launch.

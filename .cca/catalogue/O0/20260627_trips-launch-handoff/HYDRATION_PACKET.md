# Hydration packet, Console Journey + Trips launch orchestrator

Ordered read list for the incoming thread. Read in order; do NOT read the chat transcript linearly.
Paths are repo-relative to `/Users/gilraitses/orcast`.

## 1. Governance / canon (read first)

- `.cca/catalogue/O0/20260627_trips-launch-handoff/HANDOFF_CHARTER.md` (this rotation's authority doc:
  §B locked decisions, §D the launch instruction, §H the ack)
- `.cca/catalogue/O0/20260627_console-journey-trips/DECISION_RECORD.md` (items 1-3 CONFIRMED; 4-8 need
  operator GO before W1)

## 2. The program this thread launches (read before dispatching)

- `.cca/catalogue/O0/20260627_console-journey-trips/WAVESET_CHARTER.md` (waves W1/W2/W3, roles, gates,
  collision-avoidance, return contract)
- `.cca/catalogue/O0/20260627_console-journey-trips/VISUAL_PROGRAM_CHARTER.md` (the search affordance +
  East Sound fog/descend/ferry-route/orbit choreography + the CameraDirector API)
- `.cca/catalogue/O0/20260627_console-journey-trips/CONNECTIONS_RESEARCH.md` (open transit sources:
  WSF, WSDOT, OpenSky, SkyLink, seaplane, gazetteer + honesty labels + adapter contracts)
- `.cca/catalogue/O0/20260627_console-journey-trips/wave_shape.yml` (machine shape: waves, agents,
  beats, sources, operator_gates)
- `.cca/catalogue/O0/20260627_console-journey-trips/W1_DISPATCH.md` (the six producer prompts to
  dispatch FIRST)
- `.cca/catalogue/O0/20260627_console-journey-trips/W2_DISPATCH.md`,
  `W3_DISPATCH.md` (later waves; read for sequencing, dispatch after their gates)

## 3. The live code surface the program extends (reads to ground the dispatch)

- `web/app/page.tsx` -> `web/app/components/AdaptiveExplore.tsx` (the console shell: scene + chat slot)
- `web/app/components/scene/SalishScene.tsx` (the r3f scene; `OrbitControls`, focus marker, `handlePick`;
  the W2 convergence file)
- `web/app/components/ActiveSurfaceHost.tsx` (panel slot renderer; the text-only `map_viewport` case to
  make camera-driving)
- `web/lib/adaptiveConsole.ts` (turn driver; `runAdaptiveTurn` -> `/api/be/api/interactions/plan`;
  `PUBLIC_PLANNER_SPEC`)
- `web/lib/uiIntent.ts`, `web/lib/sceneIntent.ts` (panel schema + scene-click intent types)
- `web/app/(sandbox)/tiles3d/TilesSandboxScene.tsx` (the bounding-sphere fit math to reuse for camera
  framing)
- `src/aws_backend/casting/planner.py` (deterministic keyword planner; the W3 convergence file),
  `src/aws_backend/casting/skills_manifest.json`, `src/aws_backend/routers/interactions.py`
- `js/agentic/trip-hierarchy-model.js` (the trip schema to port in W1)

## 4. Connections data (W2/W3 clients build against these)

- WSF API docs: vessels (`/ferries/api/vessels/...`), terminals
  (`/ferries/api/terminals/.../terminalsailingspace`), schedule (`/ferries/api/schedule/...`).
- WSDOT Traveler API: TravelTimes + TrafficFlow REST.svc. Free access code by email (operator
  provides; store in `.env` as `WSDOT_ACCESS_CODE`).
- All exact endpoints + the fields the planner needs are in `CONNECTIONS_RESEARCH.md`.

## 5. Conventions / lineage (how this program plugs in)

- `.cca/catalogue/O0/20260627_demo-waveset/` (the capture pipeline W-CAPTURE hands beats to;
  `family: DEMO`, beats with `route` + `spec` + `surface_components`)
- `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/WAVESET_CHARTER.md` (the build-waveset pattern
  this charter mirrors: parallel producers + integrator phase)
- `docs/devpost/casting/ORCHESTRATOR_NARRATOR_FRAMEWORK.md` (the orchestrator/narrator contract the
  chat slot honors)

## 6. Repo map (orientation)

- `web/` Next.js console (the surface this program extends; one-file-one-owner per wave).
- `src/aws_backend/` FastAPI backend (planner, casting, sources, interactions). New connections
  clients go under `src/aws_backend/sources/`; the trips planner branch under `casting/`.
- `modeling/` offline models (the corridor traffic model lands under `modeling/traffic/`).
- `.cca/catalogue/O0/` waveset homes (this program: `20260627_console-journey-trips/`; this handoff:
  `20260627_trips-launch-handoff/`). The repo has large untracked demo/figure/model trees -- never
  `git add -A`.

## 7. Sibling lane (awareness only, NOT this thread's job)

- `.cca/catalogue/O0/20260627_open-science-integration/` (OS1 effort/detectability): extraction done,
  measurement defect (offset tails), needs a robustness pass. Stays with the originating orchestrator
  unless the operator reassigns. Do not touch unless asked.

# Console Journey + Trips: waveset charter

## 0. How to use this template

This charter governs a build program on the live 3D console. It mirrors the terrain-bathymetry-twin
build pattern: parallel producers under one-file-one-owner in early waves, then an integrator wave,
then the journey wave. Read `DECISION_RECORD.md` first, then `wave_shape.yml` for the machine shape,
then the per-wave dispatches. The orchestrator (O0) launches one wave at a time and synthesizes into
`STEP_LOG.md` after each.

## 1. Decision record

See `DECISION_RECORD.md`. Do not launch a wave whose decisions are not CONFIRMED.

## 2. Waveset execution model (keep verbatim)

- One file, one owner, per wave. The owner is the only agent that edits that file in that wave.
- A single convergence file per wave (the file that wires producers together) has a single editor,
  and that editor runs in a later phase of the wave, after producers land.
- No dev server runs during a parallel wave. Validation is type-check only
  (`cd web && npm run build` or `npx tsc --noEmit`).
- Sub-agents do not deploy, promote, or commit. They return a diff summary and validation output.
- Large artifacts (capture video, tiles) go to object storage. Secrets go to `.env` / deploy config.
- Honesty label travels with every served surface: measured vs modeled vs published vs heuristic.

## 3. The waves

### Wave W1: foundation primitives (parallel producers)

De-risk the hard, independent pieces. Six owners, no shared files.

| Role | Owns | Deliverable |
|------|------|-------------|
| Camera Director | `web/lib/scene/camera/` (new) | `flyTo`, `descendTo(altitude)`, `followPath(points)`, `orbit(center, radius, speed)`, easing; pure module driven by a ref handle, no React coupling |
| Search Affordance | `web/app/components/scene/SearchAffordance.tsx` (new) + its CSS block | Frosted circular magnifier button (upper-left, over the viewer); hover expands a search field; collapses on icon click or idle timeout; emits `onSearch(query)` |
| Geocode / Gazetteer | `web/lib/geo/gazetteer.ts` (new) + data file | Curated Salish-Sea places (name -> {lat, lng, bounds, kind}); resolver `resolvePlace(query)`; optional Photon client behind a flag |
| Atmosphere Transition | `web/lib/scene/atmosphere/transition.ts` (new) | `rollInFog(durationMs)` / descent lighting tween, extending the existing realism rig without owning it |
| Connections Recon | `CONNECTIONS_RESEARCH.md` (this dir) | Source screen + honesty labels + exact endpoints for WSF, WSDOT, OpenSky, SkyLink, seaplane; adapter contracts (no network code yet) |
| Trips Schema | `web/lib/trips/model.ts` (new) | TypeScript port of `js/agentic/trip-hierarchy-model.js` (Trip -> Days -> Stops -> ViewingZones) + branch enum (visiting / here-now / kayak / curious) |

Gate W1: every module type-checks in isolation; the East Sound camera path runs in a sandbox route
(`web/app/(sandbox)/journey/`) with no orchestrator wiring; recon doc lists confirmed endpoints.

### Wave W2: the intent loop (integrator + connections clients)

| Role | Owns | Deliverable |
|------|------|-------------|
| Viewport Bridge | `web/app/components/scene/SalishScene.tsx` (convergence; single editor, phase B) | Make the `map_viewport` ui_intent drive the Camera Director (fly/descend/orbit) instead of dropping a marker; expose a camera ref |
| Intent Transducer | `web/lib/intent/transducer.ts` (new) + `web/lib/adaptiveConsole.ts` (phase A) | Sample camera target / altitude / dwell / current orbit subject; enrich each planner turn's `focus` / `viewport`; throttle |
| Fly-through Choreography | `web/app/components/scene/SearchAffordance` wiring + journey controller (new) | Search -> geocode -> fog roll-in -> descend to ~50 ft -> follow ferry route to Orcas -> large orbit around East Sound |
| WSF Client | `src/aws_backend/sources/wsf.py` (new) | Real-time vessel locations, schedule by route/date, terminal sailing space; access code from env |
| WSDOT Traffic Client | `src/aws_backend/sources/wsdot_traffic.py` (new) | Travel Times + Traffic Flow; plus an appendable history logger for the corridor model |

Gate W2: searching a gazetteer place flies the live console camera through the choreography; a
planner turn that returns `map_viewport` moves the camera; WSF/WSDOT clients return live JSON in a
unit test against recorded fixtures (no live calls in CI).

### Wave W3: the Trips journey (orchestrator-side)

| Role | Owns | Deliverable |
|------|------|-------------|
| Trips Planner Branch | `src/aws_backend/casting/planner.py` (convergence; single editor) + skills | Branch on the orienting answer; emit panels per branch (compare-places / local-area / kayak / sidequest) |
| Connections Planner | `src/aws_backend/casting/trips/connections.py` (new) | "Make your sailing / flight" reasoning: WSF schedule + sailing space + WSDOT ETA (real-time and modeled future) + flight board; honesty-labeled |
| Corridor Traffic Model | `modeling/traffic/corridor.py` (new) | Time-of-day / day-of-week model fit on the self-collected WSDOT travel-time log for SeaTac <-> Anacortes; predict future-departure ETA with an interval |
| Kayak Branch | trip panels + `web/app/components/console/` slot (new) | Launch points, tide / current windows, short-range viewing zones, safety framing; camera hugs water |
| Sidequests + Auth Chip | `web/app/components/console/` slot (new) | Curiosity pairing prompts; a single inline confirm chip that authorizes a charter / wave without leaving the scene |

Gate W3: each branch returns a coherent panel set from a real planner turn; the connections planner
answers a concrete "depart SeaTac 3pm Friday, catch the 6:30 Anacortes sailing?" with a labeled
confidence; no new ML promoted.

### Capture (hands off to the demo waveset)

The East Sound fly-through and one Trips branch become new B-side beats in
`.cca/catalogue/O0/20260627_demo-waveset/` (new Playwright specs under `web/e2e/beats/`). This wave
is capture-only and does not modify console code.

## 4. Per-agent prompt skeleton (copy-paste)

```
## Agent <X> — <role> (owns <path>)
YOUR TASK: <one paragraph>
DELIVERABLES: <files + exported symbols>
VALIDATION: <type-check command + the specific check that proves it works>
COLLISION-AVOIDANCE: you own ONLY <path>. Do not edit <convergence file> (that is <phase B owner>).
RETURN: diff summary + validation output. Do not deploy/commit/promote.
```

## 5. Collision-avoidance rules (do not relax)

- `SalishScene.tsx` and `planner.py` are convergence files: one editor each, in the integration phase
  of their wave, never touched by producers.
- The Camera Director is a pure module with a ref handle so the Viewport Bridge can wire it without
  two agents editing the scene.
- New panels are new files registered in `ActiveSurfaceHost` by the convergence editor only.
- Connections clients (`src/aws_backend/sources/`) are independent files, one per provider.

## 6. Gates and return contract

- Per-wave gate above must pass before the next wave launches.
- Honesty gate: no served surface may imply a measured forecast or a guaranteed connection; labels
  required (measured / modeled / published / heuristic).
- Return per agent: changed files, exported symbols, type-check output, and the one concrete check
  from its VALIDATION line. No screenshots claimed without reading the rendered output.

## 7. Open questions to confirm before launching

- Decision record items 4-8 (geocoding, traffic source, flight source, surface, no-promotion):
  confirm the proposed defaults or override.
- WSDOT / WSF access code: operator registers the email and drops the code in deploy config before W2.
- Whether the corridor traffic history log starts collecting now (it needs lead time to be useful),
  or the demo uses a short synthetic-but-labeled history until real history accrues.

# Handoff charter, Console Journey + Trips launch orchestrator

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `9a00e15`. The
`20260627_console-journey-trips/` waveset home is NEW and UNCOMMITTED as of this rotation. This
charters a fresh thread whose job is to LAUNCH and MANAGE the Console Journey + Trips program, which is
CHARTERED and dispatch-ready. Hydrate from files, not from the chat transcript linearly.

## A. Purpose

Build a continuous intent loop on the live 3D console (`web/` Next.js + react-three-fiber) where
camera motion, a place-search affordance, and the orchestrator chat slot transduce user intent into
served forecasts and a real Trips planner grounded in open transit data (ferries, road traffic,
flights). The new thread:
1. Gets operator confirmation on the open DECISION_RECORD items (4-8) and a WSDOT access code.
2. Launches Wave W1 (six parallel producer subagents) per `W1_DISPATCH.md`, manages to its gate.
3. Sequences W2 (intent loop + connections clients) and W3 (the Trips journey), then hands capture
   beats to the existing demo waveset.

Nothing in this program promotes forecast confidence. The map forecast stays the hotspot heuristic
with its existing honesty gate; Trips connections are labeled measured / modeled / published.

## B. Decisions that are LOCKED, do not reopen

Restate these in the §H ack.

1. **Surface.** Extend the live home console (`/` -> `web/app/components/AdaptiveExplore.tsx` ->
   `SceneHost` -> `web/app/components/scene/SalishScene.tsx`, r3f + three + 3d-tiles-renderer). Do NOT
   introduce a new route or a new 3D engine. The `/explore` page is the older 2D guide, not this.
2. **The dead seam to make live.** The orchestrator already emits a `map_viewport` ui_intent, but
   `ActiveSurfaceHost` renders it as text only ("Camera focused on ...") and it does NOT move the
   camera. Camera today is `OrbitControls` only; focus drops a marker. Making `map_viewport` drive a
   real Camera Director is the spine of the program (W2 Viewport Bridge).
3. **Scope.** Full 3-wave program (camera + search + atmosphere, the intent loop, the Trips branches).
   CONFIRMED by operator.
4. **Trips depth.** Real multi-step planner: port the `js/agentic/trip-hierarchy-model.js` schema
   (Trip -> Days -> Stops -> ViewingZones) into typed TS + the live backend. Not a scripted shell.
   CONFIRMED.
5. **Connections grounding (open-first, no Google needed).** Ferries = WSDOT WSF API (open, free
   access code; vessel locations, schedule, sailing space, wait times) = MEASURED. Road traffic =
   WSDOT Traveler API (open, free; travel times + flow) = MEASURED realtime; future-departure ETA is
   MODELED from a self-collected history log (the API has NO history). Flights = OpenSky (open live
   positions, may block AWS IPs, fetch via off-AWS proxy) + SkyLink/AviationStack (freemium boards) +
   Kenmore Air static seaplane schedule (PUBLISHED). Geocoding = curated Salish gazetteer (offline,
   deterministic) + self-hosted Photon typeahead (Apache-2.0). Commercial predictive-traffic API
   (Google/HERE/TomTom) is an optional fallback only, NOT the default. See `CONNECTIONS_RESEARCH.md`.
6. **Honesty labels.** Every served surface carries measured / modeled / published / heuristic. No
   surface may imply a measured forecast or a guaranteed connection.
7. **Motion is the architecture.** The resting camera state is a slow continuous orbit around the last
   focus, not a static frame. `CameraDirector.getState()` (target/altitude/dwell/subject) is the
   implicit-intent feed the transducer reads; do not "optimize away" the orbit.
8. **Execution discipline.** One file, one owner, per wave. Convergence files have a single editor in
   a later phase: `web/app/components/scene/SalishScene.tsx` (W2), `src/aws_backend/casting/planner.py`
   (W3). No dev server during a parallel wave; validate with type-check (`cd web && npm run build` /
   `npx tsc --noEmit`; pytest on fixtures for backend clients, no live calls in CI).
9. **No promotion.** This program promotes no ML model. The hotspot-heuristic forecast and its
   `effective_confidence` honesty gate are unchanged.
10. **Write policy.** No deploy, no commit, no promotion by sub-agents; each returns a diff summary +
    validation output only. Secrets (WSDOT access code) live in `.env` / deploy config, never
    committed. Large media (capture video, tiles) go to object storage. Surgical staging only; never
    `git add -A` (the repo has heavy untracked dirs). Operator commits.

## C. Registry snapshot (what is authored, in the waveset home)

Home: `.cca/catalogue/O0/20260627_console-journey-trips/`

| File | Status |
|------|--------|
| `README.md` | authored |
| `DECISION_RECORD.md` | authored (items 1-3 CONFIRMED; 4-8 proposed defaults awaiting GO) |
| `WAVESET_CHARTER.md` | authored (waves, roles, gates, return contract) |
| `VISUAL_PROGRAM_CHARTER.md` | authored (search affordance + East Sound fly-through choreography) |
| `wave_shape.yml` | authored (machine shape: waves, agents, beats, sources) |
| `CONNECTIONS_RESEARCH.md` | authored (open transit source screen + endpoints + honesty labels) |
| `W1_DISPATCH.md` | authored (6 producer prompts) |
| `W2_DISPATCH.md` | authored (5 prompts: bridge, transducer, choreography, WSF, WSDOT) |
| `W3_DISPATCH.md` | authored (5 prompts: planner branch, connections, corridor model, kayak, sidequests) |
| `STEP_LOG.md` | authored |

## D. Primer, open items

Operator's verbatim rotation instruction: *"orchrestator rotate, = i will hand off to a new thread. it
should hydrate up to your step now and take over the Trips."*

So the new thread's first action after the §H ack is NOT to dispatch blindly: it is to confirm the
open DECISION_RECORD items (4-8) and obtain the WSDOT access code from the operator, then LAUNCH W1's
six producers per `W1_DISPATCH.md`. W1 producers do not need the access code; W2's WSF/WSDOT clients
do. The corridor traffic history log (item: start now vs labeled synthetic bootstrap) needs an early
decision because real history needs lead time to accrue.

## E. Dispatch table

| Lane | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| W1 camera-director | subagent | `W1_DISPATCH.md` A; `VISUAL_PROGRAM_CHARTER.md`; sandbox `tiles3d` fit math | `web/lib/scene/camera/` flyTo/descendTo/followPath/orbit + East Sound sandbox path | chartered |
| W1 search-affordance | subagent | `W1_DISPATCH.md` B | frosted magnifier button + hover-expand + idle-collapse | chartered |
| W1 geocode-gazetteer | subagent | `W1_DISPATCH.md` C | curated Salish gazetteer + resolvePlace + optional Photon | chartered |
| W1 atmosphere-transition | subagent | `W1_DISPATCH.md` D | rollInFog + descent lighting tween | chartered |
| W1 connections-recon | subagent | `W1_DISPATCH.md` E; `CONNECTIONS_RESEARCH.md` | confirmed endpoints + adapter contracts | chartered (doc seeded) |
| W1 trips-schema | subagent | `W1_DISPATCH.md` F; `js/agentic/trip-hierarchy-model.js` | typed TS trip model + branch enum | chartered |
| W2 intent loop + clients | subagents | `W2_DISPATCH.md` | live camera flies on search/turn; WSF/WSDOT fixture tests pass | blocked-on-W1 |
| W3 trips journey | subagents | `W3_DISPATCH.md` | each branch returns coherent panels; connections plan labeled | blocked-on-W2 |
| W-CAPTURE | operator-gated | demo waveset | Playwright beats for fly-through + a Trips branch | blocked-on-W3 |

## F. Open gate / metric state (one line)

Trips program is PRE-LAUNCH (no code yet); forecast `effective_confidence` stays 0.0 / hotspot
heuristic, unchanged by this program.

Sibling lane awareness (NOT this thread's job): the OS1 open-science effort/detectability experiment
(`.cca/catalogue/O0/20260627_open-science-integration/`) has its OrcaSound daily-ambient extraction
complete (orcasound_lab, 391 days) and a measurement harness, but the detectability offset has
unphysical tails (uncapped R_max + 4-segment/day noise + max-over-bands) that blow up the CV mean even
though the median fold skill rose. OS1 needs a robustness pass before any claim; it is a separate lane
and is left with the originating orchestrator unless the operator reassigns it.

## G. Pending uncommitted local state

The entire `20260627_console-journey-trips/` waveset home AND this `20260627_trips-launch-handoff/`
home are NEW and UNCOMMITTED (untracked) at `9a00e15`. No console/backend code has been written yet
(the dispatches create it on launch). OS1 artifacts under `data/external/os1_ambient/` and
`data/external/osf_6ctjq/` are gitignored and local-only. No commit without an explicit operator ask.

## H. Return contract (ack on first response)

Before acting, the new thread returns:
- Hydration confirmed + the list of files read.
- The locked items (§B) restated in your own words, especially: extend-the-live-console-not-a-new-
  engine (B.1), the dead `map_viewport` seam to make live (B.2), full scope + real trips planner
  (B.3/B.4), the open-first connections sources + their measured/modeled/published labels (B.5/B.6),
  motion-as-intent (B.7), one-file-one-owner + convergence files + no-dev-server (B.8), no-promotion
  (B.9), and agents-commit/deploy-nothing (B.10).
- State in one line (program pre-launch; forecast confidence unchanged at 0.0).
- The launch plan: confirm DECISION_RECORD 4-8 + get the WSDOT code, THEN dispatch the six W1
  producers; W2 and W3 follow their gates.
- One risk still needing attention (e.g. the convergence-file editors in W2/W3 must run after their
  phase-A producers; OpenSky may block AWS IPs; corridor history needs lead time).

## I. Transcript / provenance pointer

Originating session:
`~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/1ec5be7f-9e23-43dd-9d24-0cb2c64a1926/1ec5be7f-9e23-43dd-9d24-0cb2c64a1926.jsonl`.
Search by keyword (console-journey-trips, map_viewport, CameraDirector, East Sound, WSF, WSDOT,
gazetteer, Trips, OS1), do NOT read linearly. Grounding recon that produced the code facts above:
frontend/viewer recon (agent `870e249d-db17-462d-bd62-0353b9ce0fe3`) and orchestrator/charter recon
(agent `3f27db39-247e-4db7-b842-d831171c1dee`). Program home:
`.cca/catalogue/O0/20260627_console-journey-trips/`.

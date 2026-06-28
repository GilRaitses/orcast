# W1 dispatch: foundation primitives

Status: pending operator GO. Discipline: one file one owner; no dev server; validate with type-check
(`cd web && npm run build` for web modules, `python -c "import ..."` / pytest for backend). No deploy,
no commit, no promotion. Return a diff summary + validation output only.

Shared context (every agent reads first):
- Console is `/` -> `web/app/components/AdaptiveExplore.tsx` -> `SceneHost` -> `web/app/components/scene/SalishScene.tsx` (react-three-fiber + three + 3d-tiles-renderer).
- Camera today is OrbitControls only; focus drops a marker. Sandbox fit math is in `web/app/(sandbox)/tiles3d/TilesSandboxScene.tsx`.
- Charter: `WAVESET_CHARTER.md`; camera spec: `VISUAL_PROGRAM_CHARTER.md`; sources: `CONNECTIONS_RESEARCH.md`.

## Agent A — Camera Director (owns web/lib/scene/camera/)
YOUR TASK: Build a pure camera-animation module exposing `flyTo`, `descendTo(altitude)`,
`followPath(points)`, `orbit(center, radius, speed)`, `stop`, `getState`, with easing. Driven by a ref
handle so the scene can attach a three.js camera + controls without React coupling. Reuse the sandbox
bounding-sphere math for framing.
DELIVERABLES: `web/lib/scene/camera/director.ts` (+ types). Exports `createCameraDirector(handle)`.
VALIDATION: type-check; a sandbox route `web/app/(sandbox)/journey/page.tsx` that runs the East Sound
path (descend -> follow -> orbit) over the live tileset. Read the rendered frame to confirm motion.
COLLISION-AVOIDANCE: own ONLY `web/lib/scene/camera/` and the sandbox journey route. Do not edit `SalishScene.tsx`.
RETURN: diff + type-check output + one sandbox screenshot you actually inspected.

## Agent B — Search Affordance (owns web/app/components/scene/SearchAffordance.tsx)
YOUR TASK: Frosted semi-transparent circular magnifier button pinned upper-left over the viewer; on
hover a matching search field slides out over the scene; collapses on icon click or after an idle
timeout. Overlay only, no layout shift. Emits `onSearch(query)`.
DELIVERABLES: the component + a scoped CSS block (own file or a clearly-owned section).
VALIDATION: type-check; mount in the sandbox journey route; confirm expand-on-hover and idle-collapse.
COLLISION-AVOIDANCE: own ONLY this component + its CSS. Do not wire it into `SalishScene` (that is W2).
RETURN: diff + type-check + an inspected screenshot of expanded and collapsed states.

## Agent C — Geocode / Gazetteer (owns web/lib/geo/gazetteer.ts)
YOUR TASK: Curated Salish-Sea gazetteer (name -> {lat, lng, bounds, kind}) for ~40 places (East Sound,
Friday Harbor, Orcas, Lopez, Anacortes, Roche Harbor, Deer Harbor, etc.). `resolvePlace(query)` with
fuzzy match. Optional Photon client behind a flag (`PHOTON_URL`).
DELIVERABLES: `web/lib/geo/gazetteer.ts` + data. Exports `resolvePlace`.
VALIDATION: type-check; unit test resolving "east sound" / "friday harbor" to correct bounds.
COLLISION-AVOIDANCE: own ONLY `web/lib/geo/`.
RETURN: diff + test output.

## Agent D — Atmosphere Transition (owns web/lib/scene/atmosphere/transition.ts)
YOUR TASK: `rollInFog(durationMs)` and a descent lighting tween that work WITH the existing realism rig
(`web/app/components/scene/realism/atmosphere.ts`) without owning it. Pure functions returning a tween
handle.
DELIVERABLES: `web/lib/scene/atmosphere/transition.ts`. Exports `rollInFog`, `descentLighting`.
VALIDATION: type-check; exercised in the sandbox journey route alongside the Camera Director.
COLLISION-AVOIDANCE: do not edit `realism/` files; only read their public surface.
RETURN: diff + type-check + an inspected before/after fog screenshot.

## Agent E — Connections Recon (owns CONNECTIONS_RESEARCH.md)
YOUR TASK: Confirm and finalize the source screen already drafted in `CONNECTIONS_RESEARCH.md`: verify
each endpoint, document the exact response fields the planner needs (sailing space counts, travel-time
route ids for the SeaTac<->Anacortes corridor, flight board fields), and write the adapter contracts.
No network code. Note any provider that blocks AWS IPs.
DELIVERABLES: finalized `CONNECTIONS_RESEARCH.md` with confirmed fields + adapter signatures.
VALIDATION: every endpoint cited with the field list the W2 clients will parse.
COLLISION-AVOIDANCE: own ONLY this doc.
RETURN: doc diff summary.

## Agent F — Trips Schema (owns web/lib/trips/model.ts)
YOUR TASK: Port `js/agentic/trip-hierarchy-model.js` (Trip -> Days -> DayTrips -> Stops -> Activities ->
ViewingZones) to typed TS, plus a `JourneyBranch` enum (visiting / here-now / kayak / curious).
DELIVERABLES: `web/lib/trips/model.ts`.
VALIDATION: type-check; a constructed sample trip validates against the types.
COLLISION-AVOIDANCE: own ONLY `web/lib/trips/`.
RETURN: diff + type-check.

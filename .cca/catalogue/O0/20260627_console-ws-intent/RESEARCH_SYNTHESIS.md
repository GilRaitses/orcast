# WS-INTENT research synthesis

Grounded in the live code on the repo at read time. Every claim below cites the file
and the lines or symbols it rests on. The goal is to explain exactly how a
`map_viewport` ui_intent is emitted today, why it is text-only, and the concrete
techniques the implementation will use to make it drive the live camera.

## 1. How a `map_viewport` ui_intent is emitted today

The public planner spec declares `map_viewport` as an allowed panel. See
`web/lib/adaptiveConsole.ts` `PUBLIC_PLANNER_SPEC.policy.allowed_panels`, which lists
`map_viewport` first, and the instruction text that says to include `map_viewport`
when a map pin or hydrophone is selected. So the server planner can return a
`ui_intent` whose `panels` array contains an entry shaped like
`{ id: "map_viewport", surface, viewport?: { lat, lng, zoom } }`. The panel and
viewport fields are typed in `web/lib/uiIntent.ts` `UiIntentPanel`.

A turn is run by `runAdaptiveTurn(sessionId, ctx)` in `web/lib/adaptiveConsole.ts`.
It posts `message`, `agent: PUBLIC_PLANNER_SPEC`, the request `viewport`, and the
request `focus` to `/api/be/api/interactions/plan` and returns the `PlanResponse`,
which carries `ui_intent`, `prepare`, and `reply`. The client-side helper
`intentToTurn(intent)` only seeds the turn message, request viewport, and focus from
a scene click. It does not move any camera.

The live console shell is `web/app/components/AdaptiveExplore.tsx`. Its `runTurn`
calls `runAdaptiveTurn`, stores the response with `setPlan(resp)`, and then sets
`focus` from the REQUEST context, `if (ctx.viewport) setFocus({ lat, lng })`. The
response `ui_intent` is handed to `ActiveSurfaceHost` for rendering.

## 2. Why it is text-only

Three independent reasons, all in the live path.

First, the panel renders as text. In `web/app/components/ActiveSurfaceHost.tsx`
`renderPanel`, the `case "map_viewport"` returns a `<p className="muted">` that reads
`Camera focused on {lat}, {lng}`. There is no camera call and no map. That paragraph
is the entire live response to a `map_viewport` panel.

Second, the live console never extracts the returned viewport for the scene.
`web/lib/uiIntent.ts` exports `mapViewportFromIntent(intent)`, which pulls a
`MapViewport` from the `map_viewport` panel or from `focus.cell`. It is consumed only
by `web/app/components/ExploreGuidePanel.tsx` (a separate reviewer surface that syncs
a 2D map viewport at line 193). The live 3D console in `AdaptiveExplore.tsx` never
calls it, so the planner's returned viewport is dropped. `AdaptiveExplore` only ever
reflects the REQUEST `ctx.viewport`, not the planner's chosen place.

Third, the live scene has no camera controller attached. In
`web/app/components/scene/SalishScene.tsx` the `focus` prop only renders a
`FocusMarker`, a red sphere raycast onto the tile surface (`focus && <FocusMarker />`
in `TwinScene`). The `OrbitControls` element is static, `target={[0, 0, 0]}`, and the
`Canvas` camera is a fixed initial pose `position: [0, 80, 120]`. Nothing moves the
camera in response to `focus` or to any ui_intent. The Camera Director exists and is
proven, but only in the sandbox route, never mounted in `SalishScene`.

Net, `map_viewport` is dead in the live console because the panel is rendered as a
paragraph, the returned viewport is never read by the live shell, and the scene has
no controller to receive a viewport even if it were read.

## 3. The proven Camera Director, and how to attach it without a second editor

The W1 Camera Director is `web/lib/scene/camera/`. `createCameraDirector(handle)` in
`director.ts` returns a pure three.js controller with `flyTo`, `descendTo`,
`followPath`, `orbit`, `stop`, `getState`, `update(deltaSeconds)`, and
`isAnimating`. It holds no React state and runs no loop of its own. It reads a
mutable `CameraDirectorHandle` (`types.ts`) every frame, with fields `camera`,
`controls`, `bounds`, `sceneDepth`, `group`, `worldUnitsPerMeter`, `fitRadius`, and
`getSurfaceY`. Geo to world mapping reuses `projectToScene` and `unprojectFromScene`
from `web/lib/sceneIntent.ts` verbatim, so the camera frame cannot drift from the
scene frame. A hard no-dunk altitude clamp (`enforceAltitudeClamp`) lifts the eye to
the higher of a 40 m metric clearance and a 0.5 unit wave headroom on every tween
frame, orbit frame, and move start.

The attach pattern is already demonstrated in
`web/app/(sandbox)/journey/JourneyScene.tsx` `DirectorRig`. It is the template for
the live bridge.

- Create the director once, `if (!directorRef.current) directorRef.current = createCameraDirector(handleRef.current)`.
- Hold a shared `handleRef` whose initial value carries `bounds`, `sceneDepth`, and
  nulls for the live attachments.
- Grab `scene`, `camera` via `useThree`, a `controlsRef` on the `<OrbitControls>`,
  and the `tiles.group`.
- Each frame, refresh `handle.camera`, `handle.controls`, `handle.group`, and
  `handle.getSurfaceY` from the live objects, then call `directorRef.current.update(delta)`.
- On `useTilesLayer.onFit`, set `handle.fitRadius` and a fit-accurate
  `handle.worldUnitsPerMeter = sphere.radius / geoRadiusMeters(bounds)`, and widen
  `camera.near` and `camera.far` from the fit radius so altitude framing does not clip.

Because all of this lives inside one inner component owned by the Viewport Bridge,
there is a single editor of the camera wiring. The director and the journey
controller stay pure modules built by phase-A producers. The bridge only mounts and
wires them, satisfying the convergence single-editor rule.

## 4. r3f imperative camera-control patterns to reuse

- Read the live camera with `useThree((s) => s.camera)`. Never drive the camera
  through React state in the per-frame loop. The director writes `camera.position`
  and the look-at directly.
- Use drei `OrbitControls` with `makeDefault` so the tiles layer culls against the
  same camera the director drives. `JourneyScene` sets `makeDefault` on its controls.
- Steer the look-at through the controls. `director.pushLookAt` copies the look-at
  into `controls.target` and calls `controls.update()` when controls are present,
  else falls back to `camera.lookAt`.
- Hand the camera to the director during a scripted journey by setting
  `controlsRef.current.enabled = false`, and re-enable it when the journey settles so
  the user keeps manual orbit. `JourneyScene` disables controls before the journey and
  the director takes over.
- Mount order matters. The water surface runs a per-frame depth pre-pass at priority
  0 before r3f's auto-render (`Water2Rig.useFrame` in both `SalishScene.tsx` and
  `JourneyScene.tsx`). The director must position the camera BEFORE that pre-pass and
  the auto-render, so the director rig must be mounted ahead of `Water2Rig`.
  `JourneyScene` documents this, DirectorRig first so it positions the camera before
  Water2Rig's depth pre-pass and the auto-render this frame.
- Set `camera.near` and `camera.far` from the fitted bounding sphere on first fit, as
  `JourneyScene.onFit` does, so high establishing shots and low cruising shots both
  stay in the depth range.

## 5. Throttling getState sampling into each planner turn (B.7)

`director.getState()` returns `{ target: { lat, lng } | null, altitude, subject, isOrbiting }`
(`director.ts` `getState`, `types.ts` `CameraState`). It is cheap, one unproject plus
a divide, but it must not be read per frame for planning, and the planner turn must
read a recent snapshot rather than the live value mid-tween.

The technique. The intent transducer keeps the active director reachable and a
throttled snapshot of its state. The sandbox already shows the throttle shape in
`JourneyScene.StateHud`, a `window.setInterval(..., 250)` that polls
`directorRef.current.getState()`. The transducer generalizes this into a small,
React-free module.

- A registry, `setActiveDirector(d)` and a clear on unmount, so the transducer can
  reach the director without React coupling. The Viewport Bridge registers the live
  director when it mounts.
- A sampler that records the latest `CameraState` on a throttle, leading plus
  trailing, around 200 to 300 ms, so a burst of frames produces at most a few reads.
- `enrichTurnContext(base)` that merges the latest sampled `target`, `altitude`, and
  `subject` into the turn's `viewport` and `focus`. When the camera is focused or
  orbiting a subject, the enriched turn carries that place so the planner knows where
  the camera is dwelling. When nothing is attached, it returns the base unchanged.

This keeps planning decoupled from the render loop and feeds the orchestrator the
implicit camera intent without spamming turns.

## 6. Factoring runPlaceJourney as a reusable controller

The sandbox `JourneyScene` `DirectorRig` effect already contains the exact beat as an
async sequence over the W1 modules. The controller lifts that sequence into a pure
function in `web/lib/journey/controller.ts`, parameterized by place, per the W2
dispatch signature `runPlaceJourney(place, director, atmosphere)`.

The beat, read from the sandbox effect.

1. Roll fog in as a soft mask over the opening cut, `rollInFog(1400, fog, { far: baseFar * 0.5 })`.
2. `director.flyTo(establish, { durationMs, subject, easing })` to a wide high pass.
3. Roll fog back out, `rollInFog(3200, fog, { far: baseFar })`, and optionally ease
   the lighting toward the descent look with `descentLighting(...)` over the realism
   lights.
4. `director.descendTo(cruisingAltM, { ... })`.
5. `director.followPath(routeAlt, { durationMs, subject, lookAhead, easing })`.
6. `orbit = director.orbit(center, radius, speed, { subject, altitudeMeters })` as the
   resting state.

Factoring notes.

- Inputs. A `place` from the gazetteer (`web/lib/geo/gazetteer.ts` `Place` with
  `lat`, `lng`, `bounds`, `kind`), a `director`, and an atmosphere context. The
  atmosphere context should be the fog target plus an optional push sink for tweens,
  mirroring `JourneyScene`'s `push(t)` into a per-frame `transitionsRef` list that the
  rig advances. The lights handle is optional, see the risk in section 8.
- Route derivation. The sandbox uses a hard-coded East Sound ferry polyline. For an
  arbitrary searched place the controller should derive a short approach polyline that
  ends at the place center, for example from an offset bearing into `place.bounds`, and
  orbit the center. A curated route can still be used for known corridors. Any derived
  or curated waypoints are approximate lane points, not a surveyed track, and must be
  labeled as such.
- Framing from bounds. Establishing altitude and orbit radius should scale from
  `place.bounds` and the director `fitRadius` so a tight harbor and a wide island both
  frame well. `flyTo` already accepts an `altitudeMeters` and frames from it.
- Cancellation. Return a handle that stops the active move, the orbit, and any pushed
  tweens, so a second search supersedes the first cleanly. The sandbox effect already
  models this with `cancelled`, `transitionsRef.forEach(cancel)`, `orbit.stop()`, and
  `director.stop()` in its cleanup.
- Degradation. Guard the fog like the sandbox does,
  `scene.fog instanceof THREE.Fog ? scene.fog : null`, so the journey still runs if a
  later visual waveset changes the atmosphere.

The live realism rig has fog and background ON by default. `applyRealism` in
`web/app/components/scene/realism/applyRealism.ts` defaults `fog` and `background` to
true, and `SalishScene`'s `RealismRig` does not turn them off, so `scene.fog` is a
`THREE.Fog` and the fog mask has a valid target in the live scene.

## 7. The search affordance

`web/app/components/scene/SearchAffordance.tsx` is a finished W1 overlay. It is an
absolutely positioned frosted magnifier with `pointer-events: none` on the root and
`auto` only on the shell, so it floats over the canvas without reflowing it. It calls
`onSearch(query)` on submit. The bridge mounts it as a sibling overlay over the
canvas and wires `onSearch` to resolve the query through the gazetteer and run the
journey on the live director.

Place resolution is offline and synchronous. `resolvePlace(query)` in
`web/lib/geo/gazetteer.ts` returns a curated `Place` or null, tolerant of partials and
small typos, and never touches the network unless `PHOTON_URL` is set. A resolved
`Place.bounds` is structurally a `HeightmapBounds`, so it feeds `projectToScene`
directly and the director frame consumes it without conversion.

`SearchAffordance.tsx` also exports a throwaway `__SearchAffordanceStory` for the W1
gate. The bridge imports only the default `SearchAffordance` and never wires the
story. The story export is dead and should not be referenced live.

## 8. Risks and open questions surfaced by research

- The planner-returned `map_viewport` reaches the live camera only if the live shell
  reads it. The cleanest reuse is to feed `mapViewportFromIntent(resp.ui_intent)` into
  the existing `focus` prop in `AdaptiveExplore.tsx`, then let the bridge turn a
  `focus` change into a journey. That is a small additive edit to
  `AdaptiveExplore.tsx`, which the program charter did not name as an owned file. This
  needs an ownership decision at the gate. See `DISCOVERY_MAP.md` section on ownership.
- `ActiveSurfaceHost.tsx` is WS-TRIPS only for its panel registry, so WS-INTENT must
  not drive the camera from inside that file. The camera move must be driven from the
  shell `focus` pipeline and the bridge, not from the panel renderer.
- Driving `descentLighting` needs the realism handle lights, which `SalishScene`'s
  `RealismRig` does not currently expose. Exposing it touches the rig mount that
  SCENIC will own next. To avoid that collision in the first bridge pass, run the
  atmosphere as fog-only through `scene.fog`, which needs no handle, and defer the
  lighting dim. Flag the lighting enhancement for SCENIC.
- The no-dunk clamp assumes a wave amplitude near 0.18 to 0.32 units
  (`MIN_WAVE_HEADROOM_UNITS = 0.5` in `director.ts`). If WS-BATHY later raises water
  amplitude, the headroom should be revisited. Carry this as a note to BATHY.

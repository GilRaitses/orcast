# WS-INTENT discovery map

Grounds the research in this codebase. Lists the exact integration seams, the one
file one owner table for everything created or edited, and the honesty and collision
notes. No unowned convergence-file edits are proposed.

## 1. Integration seams (exact locations)

### Seam A, the `map_viewport` case in `ActiveSurfaceHost`
`web/app/components/ActiveSurfaceHost.tsx` `renderPanel`, `case "map_viewport"`
returns a muted `<p>` reading `Camera focused on {lat}, {lng}`. This is the dead seam
that proves the panel is text-only. WS-INTENT does NOT edit this file. The panel
registry in `ActiveSurfaceHost.tsx` is WS-TRIPS only per the program charter. The
camera move is driven from the shell `focus` pipeline instead, so this paragraph can
stay as a textual confirmation while the camera moves through the bridge.

### Seam B, the camera-ref attach point in `SalishScene`
`web/app/components/scene/SalishScene.tsx` `TwinScene` is where the rigs, tiles,
beacons, focus marker, and the static `<OrbitControls target={[0,0,0]}>` mount. The
bridge inserts a director rig inner component here that holds the `handleRef`, the
`controlsRef` on `OrbitControls`, and refreshes the handle each frame, modeled on
`JourneyScene.DirectorRig`. It must mount ahead of `Water2Rig` so the camera is
positioned before the water depth pre-pass. The `focus` prop, currently consumed only
by `FocusMarker`, also triggers `runPlaceJourney` on the director.

### Seam C, the turn-context builder in `adaptiveConsole` (additive only)
`web/lib/adaptiveConsole.ts` `runAdaptiveTurn(sessionId, ctx)` builds the request
`body` from `ctx`. The additive edit calls `enrichTurnContext(ctx)` from the
transducer before building `body`, so each planner turn carries the sampled camera
focus and viewport. The change is additive, it only augments `ctx` and adds one
import, and it leaves the existing fields and the public planner spec untouched.

### Seam D, the `SearchAffordance` mount point
`web/app/components/scene/SearchAffordance.tsx` default export is mounted as an
absolutely positioned overlay over the canvas, inside `SalishScene`. Because
`SalishScene` currently returns a bare `<Canvas>`, the bridge wraps it in a
`position: relative` container and mounts `SearchAffordance` as a sibling so the
overlay sits over the scene. `onSearch` resolves the query with `resolvePlace` and
runs the journey on the live director.

### Seam E, the `JourneyScene` composition to lift into the live scene
`web/app/(sandbox)/journey/JourneyScene.tsx` `DirectorRig` holds the proven attach
pattern and the choreography sequence. The pattern is lifted into the bridge inner
component, and the async beat sequence is lifted into `web/lib/journey/controller.ts`
as `runPlaceJourney`. The sandbox file itself is not edited; it stays as the reference
and a manual visual harness.

### Seam F, the shell read of the planner-returned viewport
`web/app/components/AdaptiveExplore.tsx` `runTurn` sets `focus` from the REQUEST
`ctx.viewport`. To make a planner-initiated `map_viewport` move the camera, the shell
must additionally read `mapViewportFromIntent(resp.ui_intent)` from
`web/lib/uiIntent.ts` and set `focus` to it after `setPlan(resp)`. This is the seam
that closes the planner-to-camera loop. Ownership is flagged in section 3.

## 2. One file one owner table

Owners are the proposed phase-A producers and the single phase-B convergence editor.
CREATE files are new, owned solely by their producer. EDIT files name the editor and
the additive nature of the change.

| Action | File | Owner | Phase | Integration seam |
| --- | --- | --- | --- | --- |
| CREATE | `web/lib/intent/transducer.ts` | Producer A, Intent Transducer | A | Director registry plus throttled sampler plus `enrichTurnContext(base)`. Registered by the bridge, consumed by `adaptiveConsole.runAdaptiveTurn`. |
| CREATE | `web/lib/journey/controller.ts` | Producer B, Fly-through Controller | A | `runPlaceJourney(place, director, atmosphere)` composing director plus atmosphere transitions plus gazetteer place. Composed inside the bridge. |
| EDIT, additive | `web/lib/adaptiveConsole.ts` | Producer A, Intent Transducer | A | Seam C. Call `enrichTurnContext(ctx)` in `runAdaptiveTurn` before building the body. One import, additive only. |
| EDIT, convergence single editor | `web/app/components/scene/SalishScene.tsx` | Producer E, Viewport Bridge | B | Seams B and D and E. Attach director to camera and OrbitControls via the handle ref, make `focus` and search drive `runPlaceJourney`, mount `SearchAffordance`, keep `FocusMarker` as a secondary cue, register the director with the transducer. |
| EDIT, additive, ownership to confirm | `web/app/components/AdaptiveExplore.tsx` | Producer E, Viewport Bridge | B | Seam F. After `setPlan(resp)`, read `mapViewportFromIntent(resp.ui_intent)` and set `focus` so a planner-returned `map_viewport` reaches the camera. Additive, reuses an existing helper. |

Files read but NOT edited by WS-INTENT, listed so the boundary is explicit.

| File | Why it is read only here |
| --- | --- |
| `web/app/components/ActiveSurfaceHost.tsx` | Panel registry is WS-TRIPS only. The `map_viewport` text stays. |
| `web/lib/scene/camera/` director, types, index, easing | W1, done. Composed, never edited. |
| `web/lib/scene/atmosphere/transition.ts` | W1, done. Composed by the controller. |
| `web/lib/geo/gazetteer.ts` | W1, done. `resolvePlace` consumed by the bridge. |
| `web/lib/uiIntent.ts` | `mapViewportFromIntent` reused as is. |
| `web/app/components/scene/SearchAffordance.tsx` | W1, done. Default export mounted, story export ignored. See honesty note. |
| `web/app/(sandbox)/journey/JourneyScene.tsx` | Reference harness. Pattern and beat lifted, file untouched. |
| `web/app/components/scene/SceneHost.tsx` | Passes `onIntent` and `focus` through unchanged. No edit needed. |

## 3. Ownership decision needed at the gate

The program charter named these WS-INTENT components, the intent transducer with an
additive `adaptiveConsole.ts` edit, the fly-through controller, the Viewport Bridge on
`SalishScene.tsx`, and search-affordance wiring. It did not name
`AdaptiveExplore.tsx`. Closing the planner-to-camera loop for a planner-initiated
`map_viewport` requires the small additive edit in Seam F there, because the live
shell otherwise reflects only the request viewport, never the planner's chosen place.

Recommendation. Claim `AdaptiveExplore.tsx` as a WS-INTENT additive edit, since
WS-INTENT is the spine and owns the console intent loop. The edit reuses the existing
`mapViewportFromIntent` helper and the existing `focus` prop pipeline, so it does not
touch the panel registry and does not collide with WS-TRIPS. The program orchestrator
should confirm this ownership before phase B.

If the operator declines the `AdaptiveExplore.tsx` edit, the search-driven journey and
the scene-click focus journey still land, but a purely planner-initiated
`map_viewport` with a new place will not move the camera, only update the text panel.
That is a reduced acceptance, and it should be recorded as such.

## 4. Honesty and collision notes

- `SalishScene` rig mount is shared. The rig section, `RealismRig`, `Water2Rig`, and
  the tiles `primitive`, is touched next by WS-SCENIC, the rig mount, and then
  WS-BATHY, the water and substrate mount, in the calendar order INTENT first. The
  Viewport Bridge must touch only camera, controls, search, and focus wiring and must
  leave the realism and water rig mount stable, so the later visual wavesets can add
  their pure modules without merge pain. Do not refactor the rig section.
- Atmosphere drive scope. To avoid touching the shared rig in this waveset, the first
  bridge pass runs the journey atmosphere as fog-only through `scene.fog`, which needs
  no realism handle. The lighting dim through `descentLighting` is deferred and flagged
  for WS-SCENIC, since exposing the realism lights handle would touch the rig mount
  SCENIC owns next.
- Mount order. The director rig must run its per-frame update before `Water2Rig`'s
  priority-0 depth pre-pass and the auto-render, so it must be mounted ahead of
  `Water2Rig`, exactly as `JourneyScene` documents. This is a wiring constraint, not a
  rig change.
- No-dunk headroom. The clamp assumes water amplitude near 0.18 to 0.32 units. If
  WS-BATHY raises amplitude, the `MIN_WAVE_HEADROOM_UNITS` headroom should be revisited.
  Carry this to BATHY.
- Honesty labels travel with the served surface. Approach and ferry waypoints are
  approximate lane points, not a surveyed track. The pinned midday sun is a fixed
  instant, not a live clock. Fog is an atmosphere effect, labeled as such, also used as
  a soft cut mask. The depth field is modeled CUDEM, not measured. The search
  affordance and any camera confirmation copy must not imply surveyed routes or live
  time of day.
- Throwaway export. `SearchAffordance.tsx` exports `__SearchAffordanceStory`, a W1 dev
  throwaway. The bridge imports only the default and never wires the story. The story
  export stays dead. Stripping it from `SearchAffordance.tsx` is out of WS-INTENT
  scope, since that file is W1 and not in the owned edit list. Note it for the W1 owner
  to remove later if desired.

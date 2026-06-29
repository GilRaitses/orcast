# WIRING note for WS-INTENT, from SLICE-INTEGRATE (SEAM 3)

This note records how the homepage B-side slice reuses the WS-INTENT camera
director, and the two follow-ups the slice leaves for the WS-INTENT owner. It is
additive context. It changes no WS-INTENT file.

## What the slice does today

`SalishScene.tsx` `SliceRig` drives the station point of view through the SAME
`CameraDirector` that `IntentDirectorRig` already owns, reached via the shared
`intentRefs`. On a station select the slice:

- cancels any in-flight `journeyRef` and stops the resting `orbitRef`, then
  clears both refs, so the resting orbit and a place journey do not fight the
  station fly-in,
- calls `runStationPOV("hydrophone", ...)` against that existing director for a
  dive-to-rig move,
- never calls `createCameraDirector`, so there is no second director, and never
  advances `director.update` in its own frame loop. `IntentDirectorRig` stays
  the sole per-frame owner of `director.update`.

Teardown stops the station POV handle on station change or unmount.

## Follow-ups for WS-INTENT

1. Station-select opt-out. The slice suspends the resting orbit imperatively by
   stopping the refs. A first-class WS-INTENT hook that suspends and later
   re-arms the resting orbit around a station selection would make the
   suspend-and-restore explicit instead of ad hoc, and would let WS-INTENT own
   when the resting orbit resumes after a station is dismissed.

2. True underwater point of view. The director enforces a no-dunk altitude clamp
   in `director.ts`, so the dive-to-rig frames the station from just above the
   translucent surface rather than fully submerged. A WS-INTENT opt-out that
   allows an eye position below the water plane for an explicit station POV would
   let the slice frame the rig from underwater. Until then the above-surface
   framing is the honest default.

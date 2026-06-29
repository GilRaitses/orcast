# WIRING-hydrophone

Owner: BST build lane (BSW slice). Scope: `web/lib/scene/hydrophone/`,
`web/public/hydrophone/` (except `slice/`, the real clip), and the
`web/app/(sandbox)/station/` self-verification route.

Built on `three` plus WebAudio only. No new npm dependency. Imports the Camera
Director and `sceneIntent` as read-only convergence files and never edits them.

## Modules

- `makeHydrophoneRig.ts` `makeHydrophoneRig(opts?)` returns
  `{ root: THREE.Group; dispose() }`. A MODELED, low-poly (~150 tris)
  representative cabled shore hydrophone: seabed anchor frame plus four legs and
  a brace, a capped element housing, a thin cable rising to the surface, and a
  high-visibility surface float. The root carries an honesty marker:
  `root.userData.honesty = "modeled"` and
  `root.userData.label = "hydrophone equipment (modeled)"`. Geometry is built in
  metres scaled by `worldUnitsPerMeter`; the root local origin is the seabed, so
  the cable length equals `|seabedDepthM|` and the float sits at the water plane
  once the root is placed on the seabed.

- `placement.ts` `stationSeabedPose(lat, lng, bounds, sceneDepth, opts)` returns
  scene-space `[x, y, z]`. Horizontal XZ reuses `projectToScene` verbatim.
  Vertical precedence: modeled substrate field (`sampleSubstrate`, negative
  metres, converted with `worldUnitsPerMeter`), then an optional downward
  `getSurfaceY(x,z)` raycast probe, then a fixed modeled fallback depth
  (default -18 m for Orcasound Lab). Y is NEVER clamped to the surface.
  `resolveSeabedDepthM(...)` exposes the metric depth for the camera POV.

- `StationPlayer.ts` framework-agnostic WebAudio class bound to the one real
  clip. Constructor `{ audioUrl, streamUrl?, attribution }`. Methods `load()`,
  `play()`, `pause()`, `seek(t)`, `getCurrentTime()`, `getDuration()`,
  `setPlaybackRate(r)`, `dispose()`, plus `getAudioBuffer()` which exposes the
  decoded `AudioBuffer` for the spectrogram lane to analyse the SAME real
  samples. Audio is MEASURED; on a fetch or decode failure it sets an error
  state (`getStatus()` / `getError()`) and never synthesises a waveform. The UI
  must display the `attribution` string.

- `stationCamera.ts` `runStationPOV(pov, station, director, ctx)` where
  `pov` is `"hydrophone" | "topdown"` and `station` is
  `{ lat, lng, seabedDepthM }`. Drives ONLY the director API
  (`flyTo` / `orbit`), never `camera.position`. Hydrophone POV flies to
  `altitudeMeters = seabedDepthM + 1.5` (eye just above the node, looking toward
  the surface). Top-down flies to `altitudeMeters = 180`, then optionally starts
  a slow `orbit` (`ctx.orbit`, `ctx.orbitSpeed` default 0.03; pass speed 0 for a
  static deterministic overview). Returns `{ pov, stop() }`.

- `index.ts` barrel for the above.

## POV / director wiring

The scene creates the director with `createCameraDirector(handle)` where
`handle = { camera, controls: null, bounds, sceneDepth, group: null,
worldUnitsPerMeter, fitRadius: null, getSurfaceY: null }`. The camera is
attached onto the mutable handle each frame, and `director.update(dt)` is called
in `useFrame`. Switching POV calls `runStationPOV`, which calls `director.stop()`
then the appropriate `flyTo` / `orbit`. For a deterministic headless frame the
scene calls `director.update(10)` once to settle the eased move; the live view
animates over the default durations.

The sandbox uses `worldUnitsPerMeter = 1` (1 m = 1 scene unit) so the rig and
its true-depth seabed placement read clearly. At integrate time the live
Salish, fit-accurate `worldUnitsPerMeter` is used instead and the rig scales to
true geographic size.

## Stream binding

`StationPlayer` decodes the archived clip at
`/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` and carries the live-listen
URL `https://live.orcasound.net/listen/orcasound-lab` as `streamUrl` (surfaced
by the UI, not decoded). Attribution shown by the UI:
`Audio: Orcasound (CC BY-NC-SA 4.0)`.

## Mount slots left for the integrator

The `/station` route leaves two clearly-commented seams and never imports the
other lanes, so it compiles standalone:

- 3D reenactment orcas: an empty `<group name="bsw-reenactment-mount-slot">`
  anchored at the station, for `web/lib/scene/reenactment/`.
- Spectrogram HUD overlay: a commented DOM slot, for `web/lib/scene/hud/`. The
  spectrogram lane reads the SAME decoded `AudioBuffer` via
  `window.__STATION_PLAYER.getAudioBuffer()` (the scene publishes the player
  instance once loaded).

## How the integrator mounts this into SalishScene later

Place the rig with `stationSeabedPose` using the live `worldUnitsPerMeter` and
the modeled `substrate` field (and/or the tiles `getSurfaceY` probe) instead of
the fixed fallback, add `makeHydrophoneRig(...).root` to the tiles group, bind a
`StationPlayer` to the same clip, and call `runStationPOV` against the existing
SalishScene director on a hydrophone scene intent. The honesty caption
`measured: audio · modeled: equipment mesh` should accompany the mount.

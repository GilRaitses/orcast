# Visual program charter: search affordance + cinematic camera

The camera program that makes the console feel alive and keeps intent continuous. It is one coherent
module set (Camera Director + Search Affordance + Atmosphere Transition) choreographed into named
beats. The resting state is motion, not a static frame, so the chat slot always has a "what are they
dwelling on" signal.

## The affordance

- A soft, semi-transparent circular button with a magnifying glass, frosted-glass styling, pinned to
  the upper-left corner of the 3D viewer, floating over the scene (not in a toolbar).
- On hover, a search field slides out of the button (same frosted styling), positioned over the
  viewer. It accepts a place query.
- It collapses when the icon is clicked again, or after an idle timeout with no interaction.
- No layout shift: it is an overlay above the canvas, never reflows the scene.

## The East Sound beat (reference choreography)

Trigger: user searches "East Sound" (or any gazetteer place).

1. Resolve query -> {lat, lng, bounds} via the gazetteer (Photon fallback if enabled).
2. Atmosphere: `rollInFog(durationMs)` begins, acting as a soft transition mask over the cut.
3. Descent: `descendTo(~50 ft above sea level)` eased, so the camera drops toward the water.
4. Route: `followPath(ferryRoute)` flies the camera along the Anacortes -> Orcas ferry route toward
   the island, fog clearing as it arrives.
5. Settle: `orbit(eastSoundCenter, radius, slowSpeed)` begins a large continuous orbit around East
   Sound and stays there as the resting state.

## Camera Director API (W1 deliverable)

```
flyTo(target: LatLngAlt, opts: { durationMs, easing }): Promise<void>
descendTo(altitudeMeters: number, opts): Promise<void>
followPath(points: LatLngAlt[], opts): Promise<void>
orbit(center: LatLng, radius: number, speed: number): OrbitHandle   // continuous; stop() to end
stop(): void
getState(): { target, altitude, subject, isOrbiting }               // read by the intent transducer
```

Implementation notes:
- Pure three.js / r3f-frame driven; no React state in the hot loop. Exposed via a ref handle so the
  Viewport Bridge (W2) wires it from `SalishScene` without a second editor.
- Reuse the sandbox bounding-sphere fit math (`web/app/(sandbox)/tiles3d/TilesSandboxScene.tsx`) for
  framing radius.
- Coordinate transform via the existing `worldPointToLatLng` / scene origin used in `SalishScene`.

## Why motion is the architecture

`getState()` is the implicit-intent feed. While orbiting East Sound, the transducer reports subject =
East Sound, low altitude, rising dwell. The orchestrator can then proactively offer the local-area
Trips branch without the user typing. The orbit is not decoration; it is the signal source.

## Honesty

The fly-through is cinematic but the scene is the real CUDEM tileset and real sea level (Y=0). Fog is
an atmosphere effect, labeled as such. No invented bathymetry or place data.

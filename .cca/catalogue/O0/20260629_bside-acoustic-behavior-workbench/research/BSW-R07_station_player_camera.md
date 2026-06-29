# BSW-R07 - Station player + camera POV

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 52dc0c16; written by the BSW sub-orchestrator.

## Summary

- Hydrophone station selection is already wired end-to-end through scene intent: `SalishScene` emits `{ type: "hydrophone", id, name, lat, lng, streamUrl }` on beacon click; `AdaptiveExplore` turns that into a planner turn and a `hydrophone_signal` panel but **drops `streamUrl`** from panel props.
- Surface beacons use `projectToScene` + downward tile raycast (`surfaceYAt`) clamped to `y >= 0` (water surface). The **equipment model must use a different vertical seam**: same X/Z projection, seabed Y from modeled `depth_m * worldUnitsPerMeter` (as `BathyRig` does), labeled modeled via `attachModeledLabel`.
- Camera motion must go exclusively through `createCameraDirector` APIs (`flyTo`, `descendTo`, `followPath`, `orbit`) on the live `IntentDirectorRig` handle. No direct `camera.position` or OrbitControls bypass during POV transitions. **Charter text says `moveTo`; the verified API name is `flyTo`.**
- LGC Part A glass tokens are **unbuilt** in `web/app/globals.css` (grep confirms zero `--glass-*`). POV-selection UI should use a minimal local glass surface with **blur=0 over canvas**, referencing manifest/TOKEN_HANDOFF token names as CSS custom properties until LGC-W4 lands.
- `web/lib/scene/hydrophone/` does not exist yet (BST-BUILD net-new). Recommended default: **parametric low-poly Three.js rig** (~150-400 tris, instanced if multi-station preview). External mesh only after license verification; best documented candidate is **TOSSIT hydrophone mooring CAD** (Open Hardware License, Zenodo), requiring CAD->glb conversion.
- `streamUrl` (`https://live.orcasound.net/listen/{slug}`) should flow into the station player; archived playback audio comes from Orcasound open S3 (CC BY-NC-SA 4.0), not invented streams.

## In-repo findings (cited)

### Scene intent and hydrophone catalog

```7:14:web/lib/sceneIntent.ts
  | {
      type: "hydrophone";
      id: string | number | null;
      name?: string | null;
      lat: number;
      lng: number;
      streamUrl?: string | null;
    };
```

```42:55:src/aws_backend/sources/orcasound.py
            hydrophones.append(
                {
                    "id": record.get("id"),
                    "name": record.get("name"),
                    ...
                    "streamUrl": f"https://live.orcasound.net/listen/{record.get('slug')}" if record.get("slug") else None,
                    "source": "Orcasound",
                    "imageUrl": record.get("image_url"),
                }
            )
```

```1083:1091:web/app/components/scene/SalishScene.tsx
        onSelect={(n) =>
          onIntent({
            type: "hydrophone",
            id: n.id ?? null,
            name: n.name,
            lat: n.latitude,
            lng: n.longitude,
            streamUrl: n.streamUrl,
          })
        }
```

### projectToScene, bounds, sea level, scale

```57:76:web/lib/sceneIntent.ts
export const SCENE_WIDTH = 120;
export function sceneDepth(bounds: HeightmapBounds): number { ... }
export function projectToScene(lat, lng, bounds, depth): [number, number] {
  const x = ((lng - bounds.min_lng) / (bounds.max_lng - bounds.min_lng) - 0.5) * SCENE_WIDTH;
  const z = -(((lat - bounds.min_lat) / (bounds.max_lat - bounds.min_lat)) - 0.5) * depth;
  return [x, z];
}
```

```110:128:web/app/components/scene/SalishScene.tsx
const TILESET_BOUNDS: HeightmapBounds = { min_lat: 48.4, max_lat: 48.7, min_lng: -123.25, max_lng: -122.75 };
const SCENE_DEPTH = sceneDepth(TILESET_BOUNDS);
const SEA_LEVEL_Y = 0;
```

`worldUnitsPerMeter` set once tile fit known (`SalishScene.tsx:602-607`). Vertical: `Y = depth_m * worldUnitsPerMeter`, `depth_m` negative below sea level (`BathyRig`/`sampleSubstrate`).

### Markers
`BuoyMarker` (`web/lib/scene/markers/buoyMarker.tsx`): pure geometry, ~2.2 units tall, caller owns position. `HydrophoneBeacon`/`SurfaceBeacons` inline in `SalishScene.tsx`:

```435:446:web/app/components/scene/SalishScene.tsx
      const [x, z] = projectToScene(node.latitude, node.longitude, TILESET_BOUNDS, SCENE_DEPTH);
      const y = surfaceYAt(tiles.group, x, z);
      return { node, key, position: [x, Math.max(y ?? 0, 0), z] as [number, number, number] };
```

`surfaceYAt` raycasts downward (`SalishScene.tsx:192-203`). Beacon labels use legacy `.scene-beacon-label` CSS (not LGC glass).

### Camera director and journey wiring

| Method | Role |
|--------|------|
| `flyTo(target: LatLngAlt, opts?)` | ease camera to frame a geo point; optional `altitudeMeters` (negative = underwater) |
| `descendTo(altitudeMeters, opts?)` | drop camera toward cruise altitude |
| `followPath(points, opts?)` | path fly with look-ahead |
| `orbit(center, radius, speed, opts?)` | continuous orbit until `OrbitHandle.stop()` |

`IntentDirectorRig` (`SalishScene.tsx:500-641`) creates director once via `createCameraDirector(handleRef.current)`, registers `setActiveDirector(director)`, per-frame fills handle refs + `director.update(delta)`. `runPlace` -> `runPlaceJourney(place, director, atmosphere)`; user grab stops director/journey/orbit; resting default `director.orbit(SCENE_CENTER, ..., RESTING_ORBIT_ALT_M)`. `runPlaceJourney` (`controller.ts:228-297`): flyTo establish -> descendTo cruise (~230 m) -> followPath -> orbit (~820 m). Hydrophone click currently triggers `runPlace(placeFromFocus(...))` (place journey, not station-specific underwater framing).

### AdaptiveExplore: streamUrl dropped

```237:244:web/app/components/AdaptiveExplore.tsx
        intent.type === "hydrophone"
          ? { id: "hydrophone_signal", surface: "sidebar", priority: 0,
              props: { station: intent.name ?? null, lat: intent.lat, lng: intent.lng } }
```

### LGC token state (UNBUILT)
`globals.css` `:root` holds only base palette - **no `--glass-*`, `--text-ink`, `.glass-surface`, `.scene-label`**. `TOKEN_HANDOFF.md` pins cross-lane token names LGC-W4 must land; `W0_FINDINGS.md:46-66` confirms absence; `LIQUID_GLASS_CONSOLE_MANIFEST.md:57-81` is authority. M3 hard rule: **blur=0 + fill/scrim only** for surfaces over the r3f canvas. BST charter: minimal local glass surface aligned to names; do not block on LGC-W4.

## Equipment-model options (parametric three vs external mesh) with licenses + cost

### Option A - Parametric Three.js rig (recommended default, standin-free)
`web/lib/scene/hydrophone/makeEquipmentRig()` from primitives: seabed frame (box/4-leg), hydrophone housing (cylinder + cap), cable (thin cylinder seabed->`SEA_LEVEL_Y`), surface float (reuse `BuoyMarker` or sphere). License: in-repo, no external dep. Honesty: `attachModeledLabel(rig, "hydrophone-equipment")` - representative Orcasound-style cabled node, not a scan. Cost ~0.5-1.5 eng-days; ~150-400 tris; single visible rig at selected station. **This is the fallback - ships regardless of external mesh outcome.**

### Option B - TOSSIT hydrophone mooring CAD (external, license-clear, conversion required)

| Field | Value |
|-------|-------|
| Source | TOSSIT PAM mooring hardware design files |
| URL | https://doi.org/10.5281/zenodo.5632099 |
| License | **Open Hardware License (OHL)** (PMC9058817 Table 1); article CC BY 4.0 |

Caveats: CAD/STL/STEP, not glTF - needs CAD->glb pipeline, decimation, scale/orientation fit. Represents a research PAM mooring, not Orcasound's RPi shore station; honest if labeled modeled. Cost ~2-4 eng-days + OHL compliance review via O0. Risk: OHL != CC0; O0 must confirm OHL satisfies "permissive" gate. No surface buoy in TOSSIT frame - parametric float still needed.

### Option C - Sketchfab oceanographic models (NOT recommended without per-model verification)
Candidates exist (e.g. "Buoy mooring with chains") but individual license pages not verified in this read-only pass; do not ship until O0 verifies the specific page. Default remains Option A.

### Option D - NOAA / WHOI diagrams (2D reference only, not 3D meshes)
NOAA AUH mooring diagram, PMEL HARU pages - useful for parametric design fidelity, not direct import.

## Placement plan (station lat/lng -> seabed via projectToScene + raycast)

For selected station `{lat, lng}`:
1. **Horizontal:** `[x, z] = projectToScene(lat, lng, TILESET_BOUNDS, SCENE_DEPTH)`.
2. **Depth sample:** `depth_m = sampleSubstrate(field, lat, lng)` (modeled CUDEM, negative below sea level).
3. **Vertical:** `y = depth_m * worldUnitsPerMeter` (identical to `BathyRig`). Gate on `fitRadius != null`.
4. **Rig root:** `<group position={[x, y, z]}>` with `attachModeledLabel(group, "hydrophone-equipment")`.
5. **Cable to surface:** vertical segment rig Y -> `SEA_LEVEL_Y`; surface buoy at `[x, SEA_LEVEL_Y, z]` or retain existing `HydrophoneBeacon`.

Raycast role: cross-check against streamed tile geometry; prefer substrate depth for honesty consistency. For land/nearshore stations (positive depth_m), suppress submerged rig. Equipment rig must **not** reuse `Math.max(y??0, 0)` (would float at surface, violating "on the seabed"). Proposed module: `web/lib/scene/hydrophone/placement.ts` exporting `stationSeabedPose(...)`.

## Camera POV-selection design (hydrophone POV + top-down via director.ts; LGC-token alignment)

**Architecture constraint: director-only.** All POV switches call the live `CameraDirector` with `controls.enabled=false` during scripted moves. Do not set `camera.position` directly or re-enable OrbitControls mid-transition.

**Proposed `runStationPOV(pov, station, director, handle)`** (new pure fn in `web/lib/scene/hydrophone/stationCamera.ts`), mirroring `runPlaceJourney`:

| POV | Director sequence | Parameters |
|-----|-------------------|------------|
| **hydrophone** | cancel prior orbit/journey -> `flyTo` | `{lat, lng, altitudeMeters: depth_m + 1.5}` (eye ~1.5 m above seabed); `durationMs ~2500`; look-at default surface point. If insufficient upward pitch, follow with `descendTo(depth_m + 0.5)` or extend director with explicit look-at (O0 decision). |
| **top-down** | cancel -> `flyTo` -> optional slow `orbit` | `{lat, lng, altitudeMeters: 120-250}` (above `MIN_ALT_ABOVE_SURFACE_METERS=40`); then `orbit({lat,lng}, radius: max(8, fitRadius*0.08), speed: 0.03, {altitudeMeters: 180})` |

Wire from UI: expose `runStationPOVRef` alongside `runPlaceRef` on `IntentBridgeRefs`. Station POV should supersede generic focus journey for BST acceptance.

**LGC-token alignment:** minimal local glass chip (Html overlay or fixed DOM sibling over canvas). CSS custom props mirror manifest Part A names: `--glass-tint-cool`, `--glass-opacity-hud/floor`, `--glass-scrim`, `--glass-scrim-alpha`, `--glass-hairline`, ink `--text-ink/-muted-ink/-accent-ink`. **M3 compliance: `blur:0`, no `backdrop-filter` over canvas; fill + scrim gradient only.** UI: two-segment control `Hydrophone POV | Top-down`; active uses `--accent-ink`. **Collision lock:** POV chip CSS in a BST-owned class (e.g. `.bsw-pov-chip`) in a new scoped stylesheet/module; do **not** edit LGC-owned `.glass-surface` region in `globals.css` until O0 serializes.

## streamUrl binding plan (the currently-dropped streamUrl)

| Stage | streamUrl |
|-------|-----------|
| API / `HydrophoneNode` | Present |
| `SceneIntent` emit | Present |
| `AdaptiveExplore` panel props | **Absent** |
| `HydrophoneSignalPanel` | Not consumed |
| Audio playback in `web/` | **None** |

Plan: (1) thread `streamUrl`/`stationId` through `AdaptiveExplore.onIntent` extra panel props; (2) extend `HydrophoneSignalProps`; (3) new BST-owned `StationPlayer` (live link opens Orcasound listen page labeled "live listen (Orcasound)"; archived playback resolves FLAC/HLS from Orcasound open S3 via `live_orcasound_feeds.json` + R01; WebAudio for playback; spectrogram = BSH, classification = BAM); (4) honesty labels (audio measured + attribution; mesh modeled); (5) no invented streams - if `streamUrl` null + no archive resolved, show station metadata only.

## Recommendations with cost + standin-free fallback

| Item | Recommendation | Cost | Standin-free fallback |
|------|----------------|------|------------------------|
| Equipment mesh | Parametric Three.js rig in `web/lib/scene/hydrophone/` | S (~1 day) | Same (primary) |
| External mesh | TOSSIT Zenodo CAD only if O0 confirms OHL; else skip | M (~3 days incl. conversion) | Parametric rig |
| Seabed placement | `projectToScene` + `sampleSubstrate` x `worldUnitsPerMeter`; raycast validate | S (hours) | substrate-only Y if raycast misses |
| POV control | `runStationPOV` -> director `flyTo`/`orbit`; new ref on IntentBridge | M (~1-2 days) | fixed hydrophone POV only |
| LGC glass POV chip | local CSS using manifest token names; blur=0 | S (~0.5 day) | plain `--surface-2` chip until tokens land |
| streamUrl | pass through panel props; player binds listen URL + S3 archive | M (~2 days w/ WebAudio) | listen link only (no scrub until BSH) |
| Compute | one rig instance, low-poly, no extra pass | S | n/a |
| Convergence | BST-INTEGRATE serializes `SalishScene.tsx`/`AdaptiveExplore.tsx`/`globals.css` via O0 | coordination | sandbox-first at `web/app/(sandbox)/station/` |

Implementer note: use `flyTo`, not `moveTo` (charter/PROGRAM typo). License gate: Orcasound archive CC BY-NC-SA 4.0 (NC) - O0 must confirm demo use satisfies NC.

## Open questions for O0

1. LGC token drop timing: BST uses local fallback CSS with manifest var names until LGC-W4, vs waiting for `:root` tokens?
2. POV chip class ownership: can BST add `.bsw-pov-chip` to `globals.css`, or CSS-module-only to avoid LGC-W4 collision?
3. TOSSIT OHL: does Open Hardware License satisfy BST "CC0/CC-BY/permissive" gate for demo mesh?
4. Hydrophone POV look-at: is `flyTo` with negative `altitudeMeters` + default surface look-at sufficient, or extend director with explicit `lookAtAltitudeMeters`/`pitchUp`?
5. Station journey vs place journey: on hydrophone select, replace `runPlace(placeFromFocus)` entirely, or run place journey then auto-switch to hydrophone POV?
6. Orcasound NC audio: confirm CC BY-NC-SA archived clips acceptable for B-side demo; identify one licensed slice station/time (R01 scope).
7. Multi-station preview: all rigs at low LOD instanced, or only selected station rig?
8. Surface beacon coexistence: hide surface `BuoyMarker` when underwater rig visible, or show both (marker + cable)?

## Sources

### In-repo (verified at 240570e)
`web/app/components/scene/SalishScene.tsx`, `web/lib/sceneIntent.ts`, `web/lib/scene/camera/director.ts`, `web/lib/scene/camera/types.ts`, `web/lib/journey/controller.ts`, `web/lib/intent/transducer.ts`, `web/lib/scene/markers/buoyMarker.tsx`, `web/lib/scene/substrate/sampleSubstrate.ts`, `web/lib/scene/bathy/honesty/attach.ts`, `web/app/components/AdaptiveExplore.tsx`, `web/app/components/console/HydrophoneSignalPanel.tsx`, `web/app/components/ActiveSurfaceHost.tsx`, `web/app/globals.css`, `src/aws_backend/sources/orcasound.py`, `.cca/catalogue/O0/20260628_liquid-glass-console/{TOKEN_HANDOFF.md,W0_FINDINGS.md}`, `LIQUID_GLASS_CONSOLE_MANIFEST.md`, `.cca/.../BSW-STATION_CHARTER.md`, `PROGRAM.md`, `docs/ml/ORCA_ML_INTEGRATION.md`

### External

| Resource | URL | License |
|----------|-----|---------|
| TOSSIT hardware CAD | https://doi.org/10.5281/zenodo.5632099 | Open Hardware License; article CC BY 4.0 |
| TOSSIT paper (PMC) | https://pmc.ncbi.nlm.nih.gov/articles/PMC9058817/ | CC BY 4.0 |
| NOAA AUH mooring diagram | https://archive.oceanexplorer.noaa.gov/explorations/03fire/logs/feb22/media/hydrophone.html | Public domain (US Gov); 2D only |
| PMEL HARU mooring | https://pmel.noaa.gov/acoustics/haru_system.html | US Gov docs |
| Orcasound listen (streamUrl target) | https://live.orcasound.net/listen/{slug} | Site terms; audio CC BY-NC-SA 4.0 |
| Orcasound open audio S3 | `s3://audio-orcasound-net/` | CC BY-NC-SA 4.0 |

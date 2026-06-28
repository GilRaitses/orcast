# Visual deficiency register, /journey sandbox

Tracks every visual element of the East Sound journey fly-through, its status
before and after this remediation pass, the module that provides it, the fix
applied, and the screenshot that verifies it.

Status values are missing, provisioned, or present. Present means the source
module is composed into the journey scene and confirmed by inspecting the
captured beat frame. All elements below were missing before this pass, when the
journey scene mounted only three flat basic lights, a bare tileset, and a flat
gradient background.

## Honesty note

The scene is the real full-extent CUDEM tileset rendered at real sea level, scene
Y equals 0. The ocean is the depth-driven water2 surface whose alpha and color
follow the water-column thickness read from the opaque scene depth, so shallows
reveal terrain and only deep channels read as solid blue. Fog is an atmosphere
effect from the realism rig, labeled as such, used here also as a soft cut mask.
No invented bathymetry and no invented place data. Ferry waypoints are
approximate lane points, not a surveyed track. The pinned sun instant is a fixed
midday so the terrain is lit, not a live clock.

## Register

| Element | Status | Source module | Fix | Verified |
| --- | --- | --- | --- | --- |
| Sky / atmosphere background | present | realism applyRealism, skyColor | RealismRig composed into the journey scene, background true so scene.background is the elevation-driven sky color | gate_establishing.png |
| Fog roll-in | present | realism makeFog, atmosphere/transition rollInFog | rollInFog thickens fog as a soft mask over the opening cut, then a second rollInFog clears it back to base far during the descent | gate_establishing.png, gate_descent.png |
| Ocean water | present | water2 makeWater2 | Water2Rig composed with the per-frame depth pre-pass run before the auto-render, water hidden during the pre-pass, amplitude lowered to 0.18 for a calmer open-water read. Shoreline foam reveals the shallows and deep channels read solid blue in every beat | gate_establishing.png, gate_follow.png, gate_orbit.png |
| Terrain lighting and materials | present | realism applyRealism, makeSun | Pinned midday sun plus ambient and hemisphere lights from the realism rig replace the three flat basic lights. CUDEM islands read with lit relief and material color | gate_establishing.png, gate_follow.png |
| Horizon / background coherence | present | realism skyColor, makeFog | Sky color and fog color share the sun-elevation tint so the horizon reads as sea haze rather than a flat gradient | gate_orbit.png |
| Sun | present | realism makeSun | makeSun pinned to SCENE_TIME drives both the realism directional light and the water2 sun direction and glitter | gate_establishing.png |
| Camera altitude clamp, no dunk | present | camera director enforceAltitudeClamp | Additive hard clamp lifts the eye to the higher of a 40 m metric clearance and a 0.5 unit wave headroom above the surface or water plane, applied on every tween frame, orbit frame, and move start. Captured altitudes were 2527 m, 235 m, 237 m, 820 m, never below the surface | gate_descent.png, gate_follow.png |
| Establishing shot | present | camera director flyTo | Wide high pass over the San Juans at about 2500 m, 4.5 s eased, islands and water in frame | gate_establishing.png |
| Descent pacing | present | camera director descendTo | Eased drop to a 230 m cruising altitude over 4.5 s, islands held on the horizon, never below the clamp | gate_descent.png |
| Follow look-at framing | present | camera director followPath | Anacortes to Orcas route over 17 s, altitudes easing 240 m to 182 m so the look-ahead sits slightly below the eye, a forward-and-down gaze toward the destination | gate_follow.png |
| Orbit framing | present | camera director orbit | Slow orbit around East Sound at 820 m framing the sound, the surrounding islands, and the water as the resting state | gate_orbit.png |

## Director acceptance gate, 2026-06-27, convergence verify

I ran the live gate against the converged SalishScene (WS-INTENT + WS-SCENIC +
WS-BATHY mounts) on a clean dev server, port 3020. I drove the home route with
Playwright, settled the 3D scene, captured the resting state, drove an East
Sound place search through the SearchAffordance overlay, and sampled the
fly, descend, follow, and settle beats. I read every PNG. I also rendered the
five trip panels through the real ActiveSurfaceHost routing in a throwaway
harness and captured them. Screenshots live in `acceptance_screenshots/`.

Verdict, the five original operator complaints plus the two known seams.

| Item | Verdict | Evidence | Screenshot |
| --- | --- | --- | --- |
| 1. Sky box missing sky | PASS | Preetham sky dome owns the background and renders a pale marine-haze sky in every frame, no black or flat-gradient box | gate_rest.png, gate_zoom_rest_canvas.png |
| 2. Missing fog | PASS | Tuned realism fog reads as sea haze, the distant horizon ring dissolves into it instead of cutting a hard edge | gate_zoom_rest_canvas.png, gate_search_04_16000ms.png |
| 3. Missing water | PASS | Depth-driven water2 surface fills the basin, shallows reveal terrain and deep channels read solid blue, shoreline foam present | gate_rest.png, gate_search_03_11000ms.png |
| 4. Land missing materials, barren island | PASS | Terrain stylist tint plus the pinned-midday realism sun give the CUDEM islands lit, vegetated relief, not bare tan | gate_rest.png, gate_zoom_rest_canvas.png |
| 5. Journey POV strange, fast, dunks into water | PASS | The search-driven fly, descend, follow, and settle orbit hold the eye above the water in all six sampled beats, no dunk, eased pacing | gate_search_00_1500ms.png through gate_search_05_22000ms.png |
| Seam A. WS-BATHY depth-to-Y, shoreline seam | PASS | The submerged depth tint reads under the depth-driven water with no misaligned colored band at the shoreline, shoreline foam transitions are clean | gate_zoom_rest_canvas.png, gate_search_03_11000ms.png |
| Seam B. Sky dome background, horizon coherence | PASS | No black or non-sky horizon. The bright horizon line is the water Fresnel reflecting the pale sky at grazing angle, and the ring plus fog read coherently as haze | gate_zoom_rest_canvas.png, gate_search_05_22000ms.png |
| Trip panels render with honesty labels | PASS | connections_plan, kayak_plan, sidequests, compare_places, local_area all render through ActiveSurfaceHost. KAYAK shows the MODELED badge and harmonic basis, SIDEQUESTS shows measured, published, and modeled honesty badges and the anonymous-public tier | gate_trips_panels.png |

No FAIL required remediation, so I made no edits to the scene files. Type-check
after the gate, `cd web && npx tsc --noEmit`, exit 0.

Remediation-wave note, low priority. At very low grazing altitude during the
settle orbit there are faint white specks near the horizon line, sun glitter on
the water plus a few distant horizon-ring high points. Cosmetic only, it does not
read as a seam. Logged for a later polish wave, not a gate blocker.

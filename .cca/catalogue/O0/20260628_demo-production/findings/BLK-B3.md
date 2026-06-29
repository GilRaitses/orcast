# BLK-B3, modeled terrain and bathymetry 3D twin (sandbox)

Verdict: CLEARED for the built sandbox scene (with needs-build scoping note).
Advances to CAM scoped to the sandbox twin + existing East Sound choreography.

Prereqs: SET-twin READY.

## Moving parts

1. Twin sandbox renders — CLEARED. `/journey` 200; the 3D terrain twin paints
   (canvas 641x564). Frame `set_journey.png`. Files:
   `web/app/(sandbox)/journey/page.tsx`, `JourneyHost`, `JourneyScene`.
2. Land meets the waterline (W2.6) — CLEARED. The frame shows dark land masses
   meeting the water with shoreline foam at the waterline. Files:
   `web/lib/scene/water2/depthWater.ts` (W2.6 datum), `SalishScene`.
3. Choreographed pan is non-random — CLEARED. The W1 Camera Director HUD reads
   "Camera Director (W1) East Sound journey · subject: Anacortes to Orcas ferry ·
   altitude 276 m · target 48.5634, -122.8861 · orbiting: no" — a scripted, non-random
   camera path. File: `web/lib/scene/camera/director.ts`.
4. Tight resting framing (W-PERFUX-BUILD) — partially observable; the resting frame
   is horizon-level and close on East Sound. Acceptable for the sandbox scene.

## Needs-build scoping note (numbered)

1. Per `../BEAT_SET.md` B3, two parts of the full Show are direction, not built: a
   choreographed pan across *labeled* places (post W-CAM labels) and a *deployed*
   (non-sandbox) twin route. No place labels were observed in the `/journey` frame,
   and the twin is sandbox-only (route group `(sandbox)`, `robots: noindex`). CAM must
   scope the capture to what is built (the sandbox twin scene + the existing East
   Sound camera-director choreography), and the honesty caption must say
   research-sandbox / modeled, not a labeled tour or a shipped route.

## Honesty caption

Presentable. "modeled, not measured; a research-sandbox surface, not a shipped
route." Lock 4 holds.

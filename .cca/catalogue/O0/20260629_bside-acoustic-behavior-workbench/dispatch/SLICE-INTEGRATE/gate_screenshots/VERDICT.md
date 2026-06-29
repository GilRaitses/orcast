# SI-ACCEPT verdict, homepage B-side slice baseline

Verdict: **PASS** (one minor layout defect found and fixed during the gate, then re-verified).

## Capture channel

Real GPU on the sanctioned isolated host, not SwiftShader.

- Host: `aimez-gpu-capture` EC2 `i-0e66ac03c729ebe02`, us-east-1, g4dn.xlarge (Tesla T4).
  It was stopped; I started it for the gate and it is still running. See the cost note at the end.
- Driver path: `infra/render_host/render.sh` over SSM + S3, `ORCAST_GL=gpu`.
- Renderer string reported by every frame: `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`.
- Homepage route is `/` (`web/app/page.tsx` to `AdaptiveExplore` to `SceneHost` to `SalishScene`).

A headless render cannot click a 3D hydrophone beacon, so I added a deterministic,
inert-by-default capture hook to `SalishScene.tsx` (`?station=<lat>,<lng>[,<name>]`)
that pre-selects a station exactly as a beacon click would. It mirrors the
`/workbench` `readParams` deterministic-framing convention and is absent in normal use.

## Frames (in gate_screenshots/)

1. `01_homepage_first_paint_no_slice.png` route `/`
2. `02_homepage_slice_PREFIX_legend_collision.png` route `/?station=48.5583362,-123.1735774,Orcasound%20Lab` BEFORE the fix
3. `03_homepage_slice_after_legend_fix.png` same route AFTER the fix (the canonical baseline frame)
4. `04_workbench_establish_orca_corroboration.png` route `/workbench?t=61.5` (reenactment-orca corroboration)

## Read-examination findings, per the O0 checklist

1. Slice mounts only on station-select, nothing on first paint. CONFIRMED.
   Frame 1 (no station param) shows the live twin with zero slice DOM, no spectrogram
   HUD, no estimate chip, no legend, no reenactment. Frame 3 (station param) shows the
   full slice. The lazy STFT/WebAudio bake fires only after the select (SEAM 6 held).

2. Twin environment intact, SEAM 1 held. CONFIRMED.
   Both slice frames keep the live sky dome and the WFX depth-driven water behind and
   around the slice. The scene does NOT swap to the workbench underwater background or
   fog. Compare frame 3 (homepage, live twin sky + water) against frame 4 (`/workbench`,
   which legitimately writes its own underwater tint). The homepage slice writes no
   scene global, so the twin atmosphere survives the mount.

3. Camera dives to the rig via the existing director, no double-director artifact.
   CONFIRMED. Frame 1 rests in the wide establishing frame. Frame 3 has eased to a low
   station point of view just above the water surface, framing the gold surface float and
   the mooring tether. The frame is clean with no doubled or fighting camera (no jitter,
   no split transform). This is the single `IntentDirectorRig` director driven by
   `runStationPOV`, per SEAM 3.

4. Reenactment orcas lit by the WFX env. CONFIRMED with a framing caveat.
   Frame 3 reports `orcas shown: 1 · presence-gated`, so one animal is spawned and the
   presence-gated driver is live (the HUD playhead reads `t = 75.21 s / 180.0 s`, so the
   WebAudio clock is advancing on the host). The animal itself is not crisply resolved at
   the low dive-to-rig point of view because the modeled body is at the readable
   visibility scale and a dark countershaded animal reads small against dark water from
   just above the surface. Frame 4 frames the SAME BRE pool and clip in the water column
   and shows the orca rendered crisply and correctly countershaded and lit (bright white
   belly, dark dorsal, eye and saddle patches), which corroborates that the homepage
   `orcas shown: 1` is a real lit animal, not an empty count.

5. Every honesty label present and legible. CONFIRMED after the fix.
   Estimate chip, frame 3: `estimated: SRKW call present (confidence 69%)`,
   `orcas shown: 1 · presence-gated`, the count-basis line
   `Model estimate is presence only. Count is not claimed by the classifier. Showing 1 from presence.`,
   `Audio: Orcasound (CC BY-NC-SA 4.0)`, and the `Live-listen: orcasound-lab` link.
   Legend, frame 3: `Orcasound Lab (48.5583, -123.1736)`, the measured and modeled
   lines, and the representativeness label
   `Kinematics are representative SRKW DTAG motion, not the recorded animal.`

## Defect found and fixed during the gate

Frame 2 shows the top-left legend (`bsw-legend` at `top:12px left:12px`) colliding with
the WS-INTENT search affordance icon (`osa-root` at `top:14px`, a 44px control that the
`/workbench` route does not have). The collision clipped the first word of two lines, so
`Orcasound` read as `ound` and `measured` read as `ured`. The labels were present but not
fully legible. I moved `.bsw-legend` down to `top:64px` in `web/app/globals.css` to clear
the affordance while staying well above the bottom spectrogram HUD. Frame 3 re-renders the
same route and shows both words fully legible with no overlap. This is a global CSS change
inside my owned convergence file only.

## Frame-time

No frame-time numbers were captured. `render_route.mjs` is a single-frame screenshot tool
and does not measure frame time, and the frame-time A/B gates belong to BSH and BRE ACCEPT
per `SEQUENCING.md`, kept serial on this host. No visual water regression was observed
between the no-slice frame and the slice frames, so the slice does not appear to disturb
the WFX water surface.

## Commit gate

Nothing was committed or pushed. Paused at the operator commit gate.

## Cost note

The T4 host `i-0e66ac03c729ebe02` is left running so the breadth INTEGRATE ACCEPT chain can
reuse it without a cold start. If that chain is deferred, stop it with
`aws ec2 stop-instances --region us-east-1 --instance-ids i-0e66ac03c729ebe02`.

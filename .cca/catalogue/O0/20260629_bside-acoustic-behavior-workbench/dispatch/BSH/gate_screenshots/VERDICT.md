# BSH-ACCEPT verdict, spectrogram HUD + interpretive ocean layer

Verdict: **PASS** (no caveat). The dB colormap legend occlusion was fixed per O0's ruling by
re-anchoring the legend as an inset INSIDE the spectrogram canvas, and re-verified on the real
T4. Axis ticks, dB legend, ocean chip + honesty detail, no-water-regression, and the frame-time
A/B all pass.

## Legend fix applied (O0-approved, presentational, BSH-owned)

Per O0's ruling, the dB colormap legend is now an absolute inset overlay anchored INSIDE the
spectrogram canvas bounds, so it can never be occluded by the console panel at any viewport.
Files (BSH-owned 2D-canvas/HUD only; `SalishScene.tsx` NOT touched):

- `web/lib/scene/hud/spectro/SpectroHud.ts`: wrapped the display canvas in a `position:relative`
  `canvasWrap` sized exactly to the canvas, so it is the containing block for the legend; the
  legend is `position:absolute` at `top:6px / left:30px`. The TOP-LEFT corner is deliberate: the
  console always sits to the RIGHT of the scene, so a left-anchored inset can never slide under it
  at any viewport. `left:30px` clears the on-canvas frequency-axis labels (drawn at x=3).
- `web/lib/scene/hud/spectro/legend.ts`: added a translucent backing
  (`rgba(8,30,48,0.62)` + padding + radius) and `pointer-events:none` so the dB labels read over
  the colormap and the legend never intercepts the scrub pointer. Legend content/colors unchanged.

`cd web && npx tsc --noEmit` = 0 after the change.

## Capture channel

Real GPU on the sanctioned host, not SwiftShader.

- Host: `aimez-gpu-capture` EC2 `i-0e66ac03c729ebe02`, us-east-1 (Tesla T4).
- Driver: `infra/render_host/render.sh` over SSM + S3, `ORCAST_GL=gpu`.
- Renderer string on every frame: `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`.

## Frames (in this folder)

1. `bsh_01_hud_clipbound.png` route `/?station=...,Orcasound%20Lab` (HUD, ocean OFF, 1280x800)
   — RE-CAPTURED after the legend fix. dB legend now inset top-left, fully visible.
2. `bsh_02_ocean_on.png` route `/?station=...,Orcasound%20Lab&ocean=1` (ocean chip + frame-time A)
   — RE-CAPTURED after the legend fix.
3. `bsh_03_ocean_off.png` route `/?station=...,Orcasound%20Lab` (first-pass baseline + frame-time B).
4. `bsh_04_hud_wideviewport_legendcheck.png` first-pass 1700x900 viewport legend diagnostic
   (kept for the pre-fix overflow evidence; superseded by the fixed `bsh_01`).

## Frame-time A/B (ocean ON vs OFF), serial on the isolated host

Measured by the harness rAF sampler I added to `render_route.mjs` (180 frames, ~3 s),
run strictly serially (one GL context at a time):

| Run | mean ms | median ms | p95 ms | p99 ms | max ms | fps |
|---|---|---|---|---|---|---|
| ocean OFF (nMax baseline) | 16.67 | 16.7 | 16.8 | 16.8 | 16.8 | 60 |
| ocean ON | 16.67 | 16.7 | 16.7 | 16.8 | 16.8 | 60 |

Reading: both runs sit on the 60 fps / 16.67 ms vsync cap, so the interpretive ocean layer
adds NO measurable frame-time regression. HONEST CAVEAT: the rAF interval is vsync-capped at
60 Hz, so this confirms the layer stays UNDER the 60 fps budget on the T4 but cannot resolve
headroom below the cap. The T4 is a server-class GPU, so per the RUNBOOK this is an
upper-bound sanity check, not the binding 30 fps-laptop client-tier number.

## Read-examination findings

1. Axis ticks legible. CONFIRMED. Frequency ticks (20k/15k/10k/5k) on the left and time ticks
   (0s..160s) along the bottom are crisp, with the playhead and `t = 75.12 s / 180.0 s` readout
   and the `pause / 1.0x / 0.5x / 0.25x` controls. The spectrogram is the magma colormap over
   the real measured Orcasound Lab audio.

2. dB colormap legend. **FIXED — now fully visible (PASS).** After the O0-approved re-anchor, the
   legend renders as an inset at the TOP-LEFT inside the spectrogram canvas on the 1280px demo
   viewport. Read-examined the re-captured `bsh_01` at high zoom: the vertical magma color bar, the
   rotated `power (dB)` caption, and ALL FIVE dB tick labels (`7 dB`, `-13 dB`, `-33 dB`, `-53 dB`,
   `-73 dB`) are crisp and fully on-canvas over the translucent backing. The console panel sits well
   to the right and does not touch the legend. The frequency-axis labels (`20k/15k/10k/5k`) remain
   visible immediately to the legend's left (the `left:30px` offset clears them). Confirmed
   identical legend visibility on the ocean-ON frame (`bsh_02`). Root cause of the original defect
   (the 760px canvas right edge butting the console) is now moot: the inset is anchored away from
   the console on the left.

3. Interpretive ocean chip + honesty detail. CONFIRMED. With `?ocean=1` the chip reads
   `interpretive · stratified ocean mixing` and the detail line reads "Salish Sea temperature and
   salinity structure comes from cited oceanographic profiles and models. The moving layers are a
   stylized view of water-mass mixing. This is not a measured depiction of how an orca senses its
   surroundings." The toggle reads `interpretive ocean layer · on`. (This detail copy is the
   reworded line from the cross-lane crash fix; see below.)

4. WFX water not regressed. CONFIRMED. The water surface, terrain, sky, and station float are
   pixel-consistent between ocean-OFF (frame 3) and ocean-ON (frame 2), and match the no-slice
   baseline. The interpretive strata are additive and transparent, so from the above-surface
   dive-in POV the layer is subtle (by design, default-off, honest not dramatic); it does not
   replace or disturb the WFX surface.

## errorCount note

`errorCount` is 4 on the HUD/ocean-off frames and 6 on ocean-on. All are backend `500`s from the
same-origin proxy because the host dev server has no `ORCAST_API_BASE`. The 2 extra on ocean-on are
consistent with the stratification-profile fetch failing over to the in-repo analytic Salish
halocline profile (`stratification.ts`). No fatal errors; `canvas: true` on every frame.

## Cross-lane crash fix (label-only) applied here

Before this gate the homepage crashed for ALL lanes: `interpretiveOceanLayer.ts` runs a module-load
`assertNoForbiddenClaim` over its own labels, and `INTERPRETIVE_OCEAN_DETAIL` contained the forbidden
bigram "biosonar perception" inside a negation ("...not measured orca biosonar perception."). The
naive `.includes()` guard tripped on the negated phrase and threw at import, crashing `SceneHost`
(`canvas: false`, 10x pageerror, 500). I reworded only the copy to "...not a measured depiction of
how an orca senses its surroundings." (BSH-owned `web/lib/scene/ocean/interpretiveOceanLayer.ts`),
which keeps the exact meaning, leaves the guard logic intact, and lets the scene mount. Observation
for O0 (not changed): the guard's substring matcher will flag any future negated mention of a
forbidden phrase too.

## Commit gate

Nothing committed or pushed.

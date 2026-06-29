# BSW-SLICE-ACCEPT, GPU-host accept of /workbench

Host: aimez-gpu-capture EC2 `i-0e66ac03c729ebe02`, g4dn.xlarge.
Channel: `infra/render_host/render.sh` over SSM, frames out via S3.
Renderer (all frames): `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`.
errorCount (all frames): 0. canvas present (all frames): true. GL mode: gpu.

The route is the promoted /workbench (not the /slice sandbox). Each frame was
pulled to this folder and Read-examined. Verdicts are observation-driven, not
asserted.

| Frame | Route | Read-examined verdict |
|-------|-------|-----------------------|
| 01_establish.png | `/workbench` | ACCEPT. Establishing 3/4 column shot. Nav shows "Workbench" active. Seabed rig float and tether read up the water column; the SRKW reenactment orca is visible above the rig (presence-positive default t=61.5). Estimate chip reads "estimated: SRKW call present (confidence 75%)", presence-only wording, no count or pod or type claim. "orcas spawned: 1 . presence-gated". CC BY-NC-SA 4.0 attribution and live-listen link present. Honesty legend shows measured and modeled lines plus the amber representativeness label. STFT HUD painted, caption "measured", playhead near 61 s. |
| 02_hydrophone.png | `/workbench?view=hydrophone` | ACCEPT. Camera Director hydrophone POV. The modeled equipment rig (float plus instrument body and cable) reads in the foreground near the seabed; the orca reads behind it. "hydrophone" segment active. All honesty overlays intact. Distinct framing from establish, confirms the POV switch drives the Camera Director. |
| 03_topdown.png | `/workbench?view=topdown` | ACCEPT with note. Camera Director top-down station overview, "topdown" segment active. Rig and orca read as small shapes from altitude. Honesty overlays intact. Note: the subject reads small at this default top-down altitude; a tighter top-down would frame the orca better for the cut, but the POV itself is correct and error-free. |
| 04_scrub_t120.png | `/workbench?t=120` | ACCEPT. Legend reads "t = 2:00 . ready"; the spectrogram playhead moved to the 120 s tick; the estimate chip now reads "(confidence 99%)". Proves the single BSH clock authority drives the HUD playhead and the BAM confidence together (75% at t=61.5 to 99% at t=120, matching the classification window). Orca present and presence-gated. Honesty overlays intact. |
| 05_absence_t5.png | `/workbench?t=5` | ACCEPT, strongest honesty beat. Legend reads "t = 0:05"; playhead at far left. The estimate chip reads "estimated: no SRKW call in this window", an honest per-window negative. The reenactment orca is correctly hidden (only the rig float remains), confirming the presence gate suppresses the reenactment when the model estimates absence. No fabrication. |

## Honesty-label audit (all frames)

- measured / modeled / interpretive: the legend shows "measured: audio .
  spectrogram . SRKW DTAG motion" and "modeled: equipment mesh . acoustic
  inference . 3D placement". The interpretive ocean layer is off by default in
  this slice (SIGN_OFF decision 7), so no interpretive chip is expected or shown.
- estimate plus confidence chip, presence-only wording: confirmed. The chip says
  "estimated: SRKW call present (confidence X)" or "estimated: no SRKW call in
  this window". It never states a whale count, pod, individual ID, ecotype, or
  call type. No overclaim wording observed.
- representativeness label: the amber line "Kinematics are representative SRKW
  DTAG motion, not the recorded animal." is present on every frame.
- attribution: "Audio: Orcasound (CC BY-NC-SA 4.0)" present on every frame.

## Residuals flagged

1. Top-down altitude frames the subject small (frame 03). Camera-only, not an
   error; a tighter top-down is a follow-on framing nicety, not a gate blocker.
2. "orcas spawned: 1" persists on the absence frame (05) while the chip reads
   "no SRKW call in this window" and the orca is hidden. This is accurate: the
   spawn count is clip-level presence-only (one orca allocated for a clip whose
   overall estimate is positive) and per-window presence governs visibility. It
   reads correctly but a viewer could find the two numbers adjacent. Wording is
   honest; flagged for O0 awareness, no change made.

No convergence file was touched to produce these frames.

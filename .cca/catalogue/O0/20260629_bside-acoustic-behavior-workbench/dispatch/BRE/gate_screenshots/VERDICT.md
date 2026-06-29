# BRE-ACCEPT verdict, presence-gated multi-orca reenactment

Verdict: **PASS**. Orca-body rendering corroborated via `/workbench` (the homepage POVs are
above-water and do not frame the water column), all count-basis + capability-demo labels are
honest, and the frame-time A/B shows no regression at nMax=3.

## Capture channel

Real GPU on the sanctioned host, not SwiftShader.

- Host: `aimez-gpu-capture` EC2 `i-0e66ac03c729ebe02`, us-east-1 (Tesla T4).
- Driver: `infra/render_host/render.sh` over SSM + S3, `ORCAST_GL=gpu`.
- Renderer string on every frame: `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`.

## Frames (in this folder)

1. `bre_01_presence_gated_1orca.png` route `/?station=...,Orcasound%20Lab` (default presence-gated).
2. `bre_02_bsw_demo_3orcas.png` route `/?station=...,Orcasound%20Lab&bsw_demo=3` (capability demo).
3. `bre_03_topdown_3orcas.png` route `/?station=...&bsw_demo=3&view=topdown` (topdown POV).
4. `bre_04_workbench_orca_corroboration.png` route `/workbench?t=61.5` (orca-body corroboration).

## Frame-time A/B (nMax-1 vs nMax-3), serial on the isolated host

Harness rAF sampler (180 frames, ~3 s), run strictly serially:

| Run | mean ms | median ms | p95 ms | p99 ms | max ms | fps |
|---|---|---|---|---|---|---|
| nMax = 1 (presence default) | 16.67 | 16.7 | 16.7 | 16.8 | 16.8 | 60 |
| nMax = 3 (bsw_demo=3) | 16.67 | 16.7 | 16.7 | 16.8 | 16.8 | 60 |

Reading: 3 orcas add NO measurable frame-time regression; both runs sit on the 60 fps / 16.67 ms
vsync cap. Same HONEST CAVEAT as BSH: the rAF interval is vsync-capped, so this confirms nMax=3
stays UNDER the 60 fps budget on the T4 (a server-class GPU, upper-bound check), not the binding
30 fps-laptop client-tier number.

## Read-examination findings

1. Presence-gated default count. CONFIRMED. Frame 1 chip reads `orcas shown: 1 · presence-gated`
   and `Model estimate is presence only. Count is not claimed by the classifier. Showing 1 from
   presence.` with `DTAG-segment behaviors · Traveling`.

2. Capability-demo chip. CONFIRMED and honest. Frame 2 (`bsw_demo=3`) chip reads `orcas shown: 3 ·
   presence-gated` and `Capability demo. 3 orcas is not a model estimate. The classifier resolves
   presence only, not count.` This matches the required "not a model estimate ... presence only, not
   count". Behaviors expand to `DTAG-segment behaviors · Traveling · Surface_Active · Side_rolls`,
   one real SRKW DTAG ethogram segment per orca.

3. Motion is the real SRKW DTAG driver. CONFIRMED. The behavior labels are the DTAG-segment ethogram
   (Traveling / Surface_Active / Side_rolls), and the legend states `measured: ... SRKW DTAG motion`.
   The corroboration frame shows the body swimming on that motion.

4. Orcas lit by the WFX env with crisp countershading. CONFIRMED BY CORROBORATION.
   The homepage capture hooks (dive-in `Hydrophone POV` and `Top-down`) are both ABOVE-water vantages
   looking across the surface, so the reenactment animals, which swim in the water column below the
   surface, are not framed in frames 1-3 (the SLICE-INTEGRATE ACCEPT hit the same limitation). Frame 4
   (`/workbench?t=61.5`) frames the SAME BRE pool / rig / motion stack in the water column and shows
   the orca rendered crisply: bright white belly, dark dorsal, eye and saddle patches, well lit by the
   WFX env. Per-orca rendering is identical to the multi-orca demo, so this corroborates the homepage
   `orcas shown: 3` are real lit animals, not an empty count. (Same corroboration path O0 accepted at
   SLICE-INTEGRATE.)

5. Representativeness label. CONFIRMED present. The legend carries `Kinematics are representative
   SRKW DTAG motion, not the recorded animal.` on both the homepage and workbench frames; it applies
   to every spawned orca. Honest note: it is one legend line, not separately rendered per animal; the
   per-orca representativeness binding is at the data layer (spawnFromClassification), which a frame
   cannot show.

## Bonus corroboration for BSH

Frame 4 shows the spectrogram dB colormap legend FULLY visible on `/workbench` (color bar + `7 dB`
... `-73 dB` ticks + `power (dB)` caption). This confirms the BSH legend renders correctly and is
only OCCLUDED on the homepage by the console column, supporting the BSH recommended fix.

## Defects

None in the BRE scope. No fix applied.

## Commit gate

Nothing committed or pushed.

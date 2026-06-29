# BSW-REENACTMENT charter (scrub-synced multi-orca reenactment + camera POV)

- Lane code: **BRE** (under family BSW)
- Owner: O0 dispatches; a background sub-orchestrator runs the gated build waves.
- Type: research-first (grounded by BSW-RESEARCH R04/R05/R08/R13); build/integrate/accept gated.
- `repo_state_verified_against`: origin/main `240570e961913fb610c2765a4ef77cace3f216f1`.
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`. Umbrella: `PROGRAM.md`.

## Intent (operator)
When you scrub through or slow down the sound you see the reenactment in the 3D world model with the
orcas; their dive behavior is classified from the existing DTAG sets, which give good references for
the kinematics to program the 3D orcas with. The acoustic classification (how many / what type)
drives which orcas appear.

## Grounding (verified seams)
- Real orca motion already lands in the twin: `web/lib/scene/orca/` (`OrcaController`, `rig/OrcaRig.ts`,
  `motion/biologging.ts` `driveOrca`/`track.sample(t)`), driven by the REAL SRKW driver
  `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` (7-channel float32:
  `t,yaw,pitch,roll,depth,fluke_phase,fluke_amplitude`). Mounted in `SalishScene.tsx` as `OrcaRig`.
- Multi-orca pattern (from exploration): duplicate the `OrcaRig` mount with a distinct anchor
  (`projectToScene` at a station/encounter lat/lng) + distinct motion URL; shared `env` +
  `worldUnitsPerMeter`. Sandbox: `web/app/(sandbox)/orca/OrcaSandboxScene.tsx`.
- Camera: `web/lib/scene/camera/director.ts` (moveTo/descendTo/followPath/orbit) - reuse for POV.
- The scrub timeline authority is BSH's spectrogram playhead; classification source is BAM
  (acoustic, who/what) + the kinematic ethogram (DTAG, how it moves).
- Real DTAG kinematics: SRKW driver (above) + the humpback h5 derived products (dives/phases/
  stroke-glide/behavior taxonomy) at the operator's whale-behavior repo - humpback is
  contrast/reference only, never drives an orca.

## Locked decisions (do NOT reopen)
- **No fabricated trajectory or scripted swim.** Orca motion is real DTAG telemetry (the SRKW
  driver) optionally augmented by a behavior-mapped motion clip derived from REAL classified DTAG
  segments (R04). Placement/orientation/depth/fluke stay data-driven; only bounded secondary motion
  (existing `web/lib/scene/orca/physics/`) is layered, tracking the data within tolerance.
- **Acoustic classification drives WHICH orcas appear** (count/type from BAM, scoped to what the
  model really supports); **kinematic classification drives HOW they move** (behavior -> motion
  clip). The two are wired but never conflated, and never invented.
- **Scrub/slow-down is time-synced to BSH's playhead.** Slowing the audio slows the reenactment;
  scrubbing seeks both. `track.sample(t)` already interpolates; respect it.
- **Camera POV** reuses BST's POV-selection object + `director.ts`: watch the encounter from the
  hydrophone POV or top-down; the camera never bypasses the director's surface/altitude clamps.
- **Compute-neutral:** N orcas join the existing opaque depth pre-pass (no third full render);
  instance/share geometry+material; LOD by distance. Costed against 60fps/30fps in R13.

## Wave structure
- **BRE-BUILD** (gated, net-new): `web/lib/scene/reenactment/` (timeline driver: audio playhead ->
  scene time; multi-orca spawn from a classification record) + `web/lib/scene/orca/motion/clips/`
  (behavior -> motion-clip mapping from real DTAG segments); sandbox-verified on the GPU host.
- **BRE-INTEGRATE** (gated, single editor): land the reenactment + POV into `SalishScene.tsx`;
  serialize vs LGC/CVP/WFX/ORCA/3D-TWIN.
- **BRE-ACCEPT** (gated): Read-examined frames + a short scrub clip - orcas spawn per the real
  classification, move on real DTAG kinematics, follow the scrub playhead, viewable from both POVs.

## Acceptance criteria (hard, checkable)
- Scrubbing/slowing the audio scrubs/slows the orca reenactment (synced to BSH playhead).
- The number/type of orcas reflects BAM's real classification of the slice clip.
- Motion is real DTAG-driven (no scripted loop); both camera POVs work; frame budget held.

## Escalation
Answers to O0. Any pressure to fabricate motion/counts, multi-orca perf risk, classification-source
ambiguity, convergence collisions, or any gated step: pause and return to O0.

## Return contract
Net-new file list + WIRING; the timeline-sync + classification-record contracts; GPU-host gate
frames + a scrub clip; perf numbers; open questions for O0.

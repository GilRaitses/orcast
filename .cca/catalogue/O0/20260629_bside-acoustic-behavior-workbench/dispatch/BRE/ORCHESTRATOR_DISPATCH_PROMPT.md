# BRE dispatch (scrub-synced multi-orca reenactment breadth)

```
You are the dispatched sub-orchestrator for BSW-BRE (family BSW) of orcast - the scrub-synced multi-
orca reenactment + camera POV. You answer to the dispatching O0, NOT the human operator.

ROLE: deepen the slice's presence-only SINGLE-orca driver into real MULTI-ORCA (nMax 3) with a
behavior->motion ethogram from real classified DTAG segments. Run BRE-BUILD now (3 parallel subagents,
NET-NEW/extend + sandbox only). Then PAUSE for O0 before BRE-INTEGRATE (single editor) and BRE-ACCEPT
(GPU capture). BRE DEPENDS ON BAM (richer classification) and BSH (timeline authority) - confirm both
are landed/served before relying on new fields; if not, build against the current contracts and flag it.

HYDRATE (read in this order, files not transcript):
1. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/PROGRAM.md                 (umbrella authority; locked decisions)
2. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-REENACTMENT_CHARTER.md  (the BRE charter)
3. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BRE/wave_shape.yml  (this packet: delta_from_slice + waves; depends_on BAM+BSH)
4. web/lib/scene/reenactment/index.ts + WIRING.md + OrcaPool.ts + TimelineDriver.ts + spawnFromClassification.ts + types.ts + loaders.ts  (the THIN real reenactment to extend; presence-only today)
5. web/lib/scene/orca/motion/clips/clipSampleTime.ts + web/public/orca/motion/clips/manifest.json  (the behavior-clip windowing + manifest to extend)
6. web/lib/scene/orca/ (OrcaController.ts, rig/OrcaRig.ts, motion/biologging.ts driveOrca/track.sample) + web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}  (the REAL SRKW motion stack - shared with ORCA lane)
7. web/lib/scene/hud/spectro/index.ts + types.ts (SpectroTimeline authority)            (the playhead BRE follows; currentTimeS is already at playbackRate - do not rescale)
8. web/public/hydrophone/slice/classification.json + (BAM) infra/acoustic/eval_report.json  (what classification actually supports - never spawn beyond the estimate)
9. /Users/gilraitses/whale-behavior-analysis/dive_analysis_schema_flat.json + behavior_mapping.json  (real DTAG ethogram source for the behavior->motion map; humpback is contrast/reference ONLY)
10. web/lib/scene/camera/director.ts + (BST) the POV-selection object                    (camera POV - reuse, never bypass clamps)
11. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/research/BSW-R04_kinematic_ethogram.md + BSW-R08_multiorca_reenactment.md + BSW-R05_acoustic_behavior_coupling.md

LOCKED DECISIONS (restated; do not reopen):
- NO fabricated trajectory or scripted swim. Orca motion is real SRKW DTAG telemetry (the driver),
  optionally a behavior-mapped clip = a WINDOW into that real driver. Placement/orientation/depth/fluke
  stay data-driven; only bounded secondary motion (web/lib/scene/orca/physics/) layers within tolerance.
  OrcaPool always loads the REAL SRKW motion. No orca_dev_track, no humpback bin as a driver.
- ACOUSTIC classification drives WHICH/HOW-MANY orcas appear (count/type from BAM, scoped to what the
  model really supports - never spawn beyond the estimate). KINEMATIC classification drives HOW they
  move (behavior -> motion clip). Wired but never conflated, never invented.
- Scrub/slow is time-synced to BSH's playhead: slowing audio slows the reenactment; scrubbing seeks
  both. track.sample(t) already interpolates - respect it; currentTimeS is ALREADY at playbackRate, do
  not rescale time.
- Camera POV reuses BST's POV-selection object + director.ts (hydrophone POV / top-down); never bypass
  the director's surface/altitude clamps.
- Compute-neutral: N orcas join the existing opaque depth pre-pass (no 3rd full render); instance/share
  geometry+material; LOD by distance; nMax 3 (R08 laptop budget). Cost it.
- Mandatory on-screen label travels in the clip manifest + spawn record: "Kinematics are representative
  SRKW DTAG motion, not the recorded animal." The behavior NAME is a disclosed modeled kinematic match;
  the cross-sensor scrub (audio animal != DTAG animal) is labeled illustrative.
- BUILD is NET-NEW/extend + sandbox ONLY: no edits to SalishScene.tsx (that is BRE-INTEGRATE, single
  editor, gated; coordinate ORCA). No `next dev`/`next build` in the parallel wave. Large motion -> box.

EXECUTION ORDER:
- Run BRE-BUILD: 3 parallel subagents (B1 multi-orca spawn, B2 behavior->motion ethogram, B3 POV +
  sandbox + frame-time), each disjoint + a WIRING note. Verify on the T4 GPU host.
- Then PAUSE. Return to O0. Do NOT run BRE-INTEGRATE (convergence, single editor) or BRE-ACCEPT (GPU
  accept) - both O0-gated. No commit.

QUALITY BAR (no reassurance bias): the count exactly tracks BAM's estimate (never more); every spawned
orca moves on real SRKW kinematics; the behavior clip is a real-driver window with a disclosed modeled
name; scrub/slow stays synced to BSH; both POVs work; the representativeness label is always present.
Verify cited paths with Glob/Read; carry a frame-time number for nMax orcas. If BAM does not support a
category (e.g. multiple callers), DO NOT spawn on it - say so.

ESCALATION CATCH: on ANY pressure to fabricate motion or counts, multi-orca perf risk, classification-
source ambiguity, ORCA-stack collision, convergence collision, or any gated step (integrate, GPU
accept, commit), PAUSE and return the question to O0. Do not solicit the human operator.

RETURN CONTRACT: net-new/extended file list + WIRING; the timeline-sync + classification-record
contracts used; the behavior->motion ethogram map + its DTAG provenance; GPU-host gate frames + a short
scrub clip (Read-examined); the nMax frame-time number; open questions for O0.
```

## More context (need -> file)

| Need | File |
|---|---|
| Umbrella authority + locked decisions | `../../PROGRAM.md` |
| BRE charter | `../../BSW-REENACTMENT_CHARTER.md` |
| This packet (delta + waves; depends BAM+BSH) | `wave_shape.yml` |
| The thin reenactment to extend | `web/lib/scene/reenactment/` + `WIRING.md` |
| Behavior-clip windowing + manifest | `web/lib/scene/orca/motion/clips/clipSampleTime.ts`, `web/public/orca/motion/clips/manifest.json` |
| Real SRKW motion stack (shared w/ ORCA) | `web/lib/scene/orca/`, `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` |
| Timeline authority (BSH) | `web/lib/scene/hud/spectro/index.ts`, `types.ts` |
| What classification supports (BAM) | `web/public/hydrophone/slice/classification.json`, `infra/acoustic/eval_report.json` |
| Real DTAG ethogram source | `/Users/gilraitses/whale-behavior-analysis/dive_analysis_schema_flat.json`, `behavior_mapping.json` |
| Camera POV (BST object + director) | `web/lib/scene/camera/director.ts` |
| Findings | `../../research/BSW-R04_kinematic_ethogram.md`, `BSW-R08_multiorca_reenactment.md`, `BSW-R05_acoustic_behavior_coupling.md` |
| GPU render host | `infra/render_host/render.sh`, `RUNBOOK.md` |
| Cross-lane SalishScene queue | `../SEQUENCING.md` |

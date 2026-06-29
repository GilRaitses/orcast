# BSW B-side demo beat set (acoustic plus behavior workbench)

Remodel of the demo-production director chain
(`.cca/catalogue/O0/20260628_demo-production/PROGRAM.md`) for the B-side slice on
the /workbench route. The role model, the four-stage chain BLK then CAM then SCR,
and the binary screen-test rubric are kept; the beats, the framing, and the
honesty locks are the workbench slice's.

This pass ran the chain in one sub-orchestrator thread on the GPU host rather
than dispatching parallel First ADs, because the surface is one route and five
deterministic framings. Each beat carries Say / Show / Evidence / Honesty plus
its BLK / CAM / SCR status. Capture is per-beat PNG on the Tesla T4 host via
`infra/render_host/render.sh`. Frames live in `demo/` and `gate_screenshots/`.

Arc: arrive at the Orcasound Lab station, see the equipment underwater, play the
real clip with its spectrogram, scrub the spectrogram to drive the clock, read
the presence estimate, then watch the presence-gated SRKW reenactment from the
hydrophone POV and top-down.

Capture settings: viewport 1280x800, GL=gpu (real T4 WebGL), 18 to 20 s settle so
the async reenactment pool spawns before the frame. One PNG per beat, deterministic
via a single query param (`view` or `t`).

---

## BSW-B1, arrive at the Orcasound Lab station

- Say: "This is the Orcasound Lab hydrophone in Haro Strait. The instrument sits
  on the seabed and listens, and the workbench rebuilds that station in three
  dimensions."
- Show: `/workbench` establishing column shot. The seabed rig float and tether
  read up the water column, with the reenactment orca above the rig.
- Evidence: `demo/beat1_arrive_establish.png` (route `/workbench`).
- Honesty: the legend names measured and modeled; the rig is modeled equipment,
  the audio and DTAG motion are measured. Representativeness label present.
- BLK: CLEARED. Establishing framing reads the seabed to surface column.
- CAM: CAPTURE OK. T4, errorCount 0.
- SCR: APPROVED. R1 to R5 pass; locks hold.

## BSW-B2, the equipment underwater

- Say: "From the hydrophone's point of view you see the modeled rig on the bottom,
  placed at the station's real coordinates."
- Show: `/workbench?view=hydrophone`. The Camera Director flies to the hydrophone
  POV; the rig float, instrument body, and cable read in the foreground.
- Evidence: `demo/beat2_equipment_hydrophone.png` (route `/workbench?view=hydrophone`).
- Honesty: equipment is modeled, placed by real seabed projection at the station
  coordinates. No measured-CAD claim.
- BLK: CLEARED. POV switch drives the Camera Director, framing distinct from B1.
- CAM: CAPTURE OK. T4, errorCount 0.
- SCR: APPROVED. R1 to R5 pass; locks hold.

## BSW-B3, play the real clip and its spectrogram

- Say: "The workbench plays the real archived Orcasound recording and bakes its
  spectrogram in the browser. Early in this clip the model estimates no call, and
  it says so."
- Show: `/workbench?t=5`. The STFT HUD is painted with the measured caption, the
  playhead sits at the far left, and the estimate chip reads no call in this
  window. The reenactment orca is correctly hidden by the presence gate.
- Evidence: `demo/beat3_clip_spectro_absence_t5.png` (route `/workbench?t=5`).
- Honesty: the spectrogram is measured STFT of real audio. The negative estimate
  is shown honestly, and the gate hides the reenactment when the model estimates
  absence, so nothing is fabricated.
- BLK: CLEARED. HUD paints, playhead and negative chip read.
- CAM: CAPTURE OK. T4, errorCount 0.
- SCR: APPROVED. R1 to R5 pass; the honest negative is the point of the beat.

## BSW-B4, scrub the spectrogram to drive the clock

- Say: "Scrub the spectrogram and the whole scene follows, because one clip and
  one clock drive the spectrogram, the estimate, and the reenactment together."
- Show: scrub from t=5 to t=61.5 to t=120. The playhead moves and the orca
  appears once the model estimates presence.
- Evidence: `demo/beat3_clip_spectro_absence_t5.png` then
  `demo/beat4_scrub_t61_present.png` then `demo/beat5_scrub_t120_conf99.png`.
- Honesty: the playhead position is the real clip time; the reenactment follows
  the same authority, it does not run on its own clock.
- BLK: CLEARED. Three timepoints read as a consistent arc.
- CAM: CAPTURE OK across all three. T4, errorCount 0.
- SCR: APPROVED. R1 to R5 pass; locks hold.

## BSW-B5, the presence estimate chip

- Say: "The chip reports the model's estimate and its confidence for the window
  under the playhead. It is presence, present or not present, with a confidence,
  not a count and not an identity."
- Show: the chip across the scrub. No call at t=5, present at 75 percent at
  t=61.5, present at 99 percent at t=120.
- Evidence: the chip state in `demo/beat3_clip_spectro_absence_t5.png` (no call),
  `demo/beat4_scrub_t61_present.png` (75 percent), and
  `demo/beat5_scrub_t120_conf99.png` (99 percent). Confidences match the BAM
  classification windows.
- Honesty: estimate plus confidence wording only. No whale count, pod, individual
  ID, ecotype, or call type. The held-out eval and its confounds live in the
  classification JSON.
- BLK: CLEARED. Chip wording and confidence track the playhead.
- CAM: CAPTURE OK. T4, errorCount 0.
- SCR: APPROVED. R3 honesty caption holds; the real confidence numbers are shown.

## BSW-B6, the presence-gated SRKW reenactment

- Say: "When the model estimates a call, the workbench spawns a reenactment driven
  by real SRKW tag motion, shown from the hydrophone POV and from above. The
  motion is representative tag data, not the animal that was recorded."
- Show: `/workbench?view=hydrophone` and `/workbench?view=topdown` while presence
  is positive. The orca moves on the measured DTAG driver.
- Evidence: `demo/beat6_reenactment_hydrophone.png` (route
  `/workbench?view=hydrophone`) and `demo/beat6_reenactment_topdown.png` (route
  `/workbench?view=topdown`).
- Honesty: motion is measured SRKW DTAG telemetry; the acoustic estimate only
  picks whether and how many orcas spawn, it never drives the trajectory. The
  representativeness label is mandatory and present on every frame.
- BLK: CLEARED. Both POVs read the reenactment with the rig.
- CAM: CAPTURE OK. T4, errorCount 0. Top-down note carried from GATE_ACCEPT
  (subject reads small at the default top-down altitude).
- SCR: APPROVED with the top-down framing note; locks hold.

---

## Stage rollup

| Beat | BLK | CAM | SCR | Frame |
|------|-----|-----|-----|-------|
| B1 arrive | CLEARED | CAPTURE OK | APPROVED | beat1_arrive_establish.png |
| B2 equipment | CLEARED | CAPTURE OK | APPROVED | beat2_equipment_hydrophone.png |
| B3 clip plus spectrogram | CLEARED | CAPTURE OK | APPROVED | beat3_clip_spectro_absence_t5.png |
| B4 scrub clock | CLEARED | CAPTURE OK | APPROVED | beat3, beat4, beat5 |
| B5 presence chip | CLEARED | CAPTURE OK | APPROVED | beat3, beat4, beat5 |
| B6 reenactment | CLEARED | CAPTURE OK | APPROVED (note) | beat6_reenactment_hydrophone.png, beat6_reenactment_topdown.png |

## Honesty locks confirmed on every captured beat

1. No whale count or type claim. The chip is presence plus confidence only.
2. The reenactment trajectory is never driven by the acoustic estimate; presence
   only gates spawn and visibility.
3. The representativeness label is visible on every frame.
4. measured and modeled are named on every frame; the interpretive ocean layer is
   off in this slice by design.
5. The CC BY-NC-SA 4.0 attribution is present on every frame.

## Heavy capture pointer

This pass captured per-beat PNG frames, which are light enough to keep in the
catalogue. Short per-beat video clips and the assembled narrated cut are a
follow-on on the box, not produced here. The deterministic recipe to capture any
beat as a frame on the T4 host is:

```
infra/render_host/render.sh --no-sync "/workbench?view=hydrophone" 20000
infra/render_host/render.sh --no-sync "/workbench?t=120" 20000
```

Video assembly would use `~/.cursor/skills/demo-video-assembly/SKILL.md` against
silent per-beat screen recordings produced on the box. Any heavy mp4 stays on the
box or S3, gitignored, with a pointer here, per SIGN_OFF decision 13.

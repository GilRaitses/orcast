# Demo render handoff (DRENDER lane)

Family DRENDER. Runs ONLY over `scr/APPROVED_TAKES.md`. The render is an operator gate: no
render starts without operator green light. Replaces the old A-side cut and the blocked
B-side `DEMO` render as the canonical submission video.

## Inputs

- `scr/APPROVED_TAKES.md`: the signed manifest (take path + caption + locks confirmed per
  approved beat). Nothing else may enter the render.
- `NARRATION.md`: the locked narration block (XTTS), one line per approved beat.
- The captured silent beat clips in `docs/devpost/figures/_demo-run/beats/` (from CAM).
- A music bed for ducking.

## Lane (per the pax render pipeline and `~/.cursor/skills/demo-video-assembly/SKILL.md`)

1. W-STORY (already locked here): the shot list is `BEAT_SET.md`; the narration is
   `NARRATION.md`; the captions are the honesty captions confirmed at SCR.
2. W-VOICE: render the narration with the orcast XTTS clone. Wire the `NARRATION.md` block
   into `tools/testing/tts_narrate.py` (or `tts_clone.py`) keyed to the approved beats.
   This edit happens at render time, gated, so the live pipeline is not changed before
   approval.
3. W-CAPTURE: already done in CAM (silent per-beat clips + gif loops).
4. W-ASSEMBLE: mux the approved silent beats with the narration over a ducked music bed
   (narration ducks the bed), per `demo-video-assembly`. Also export the gif-only,
   no-audio gallery set from the same recordings.

## Gates (run, not asserted)

- `v-beat` (`tools/waves/gates/v-beat-check.sh`): each approved beat clip present and
  well-formed.
- `v-stitch` (`tools/waves/gates/v-stitch.sh`): the stitched timeline matches the approved
  manifest order with no extra or missing beat.
- `v-render`: the final mux integrity (`tools/waves/gates/v-render.sh` / `vx-render.sh`).

## Output

- The new canonical submission video at `docs/devpost/figures/_demo-run/demo-final.webm`
  (and the cloned-voice variant), plus the gif gallery.
- On the operator render gate and a clean v-beat / v-stitch / v-render, the video is the
  canonical submission cut; update `docs/devpost/SUBMISSION.md` and the checklist video row
  on commit.

## Hard limits

- No render before `APPROVED_TAKES.md` is signed. No beat in the render that is not on the
  manifest. No narration line for a beat that was cut at SCR.
- Render start and commit are operator gates.

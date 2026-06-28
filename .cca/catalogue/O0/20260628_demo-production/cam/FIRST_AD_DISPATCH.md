# Stage 2, CAM, First-AD dispatch

Director of DCAM: dispatch one First AD per CLEARED live beat, sharded so capture stays
serial per host. Do not run all captures concurrently on one machine; timing-sensitive
capture is serial (see `~/.cursor/skills/pax-demo-capture/SKILL.md`).

## Hydration (in order)

1. `../PROGRAM.md` (honesty locks, capture settings, discipline).
2. `WAVESET_CHARTER.md` (capture settings, method, naming).
3. `../BEAT_SET.md` (your beat's Show + Honesty caption).
4. `../blk/BLK-ROLLUP.md` (confirm your beat is CLEARED).
5. The existing `web/e2e/beats/*.spec.ts` for the capture harness pattern.

## Mandate

- Author/update `web/e2e/beats/twoside-<beat>.spec.ts` to drive the cleared Show in order
  at viewport 1280x900 with `DEMO_RECORD=1`, one clip per beat.
- Record the beat (silent), export the gif loop from the same recording.
- Test the capture by Reading the captured frames: full Show in frame and in order, crop
  room for the honesty caption, clean timing, no mid-take error, take matches Show step for
  step, the real honesty figure legible.
- Write `findings/CAM-<beat>.md`: CAPTURE OK / RESHOOT, take path, the frames you
  Read-examined, and any defect.

## Hard limits

- Capture only your beat. Do not approve (that is SCR). Do not edit product code beyond the
  beat's test spec.
- Media never goes to git. Specs may be committed only on the operator gate.
- A capture is never OK from the recording command alone; you must Read the frames.

## Escalation catch

If the take cannot reach CAPTURE OK from a Read-examined frame, return RESHOOT with the
defect and the return target (CAM, or BLK if a moving part regressed). Do not pass a
flawed take, do not block on the human, do not stage or mock.

## Return

Return CAPTURE OK / RESHOOT, the take path, and the Read-examined frame evidence. The
Director assembles `CAM-ROLLUP.md`.

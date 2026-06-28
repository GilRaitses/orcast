# Stage 2, CAM (camera test), waveset charter

Family DCAM. Parent: `../PROGRAM.md`. Beats: `../BEAT_SET.md`. Enters per beat only after
that beat is CLEARED in `../blk/BLK-ROLLUP.md`.

## Intent

Capture what BLK cleared, then test the capture itself. One First AD per cleared beat.
Capture is timing-sensitive and serial per host; shard by beat to disjoint
subagents/background processes per `~/.cursor/skills/pax-demo-capture/SKILL.md`. Do not
fire a multi-minute Playwright run as a blocking call in the director's own session.

## Capture settings (orcast)

- Viewport 1280x900, `DEMO_RECORD=1`, one silent clip per beat, gif loop exported from the
  same recording.
- New Playwright specs live in `web/e2e/beats/` named for the two-sided-loop beats
  (`twoside-a1-home.spec.ts` ... `twoside-b3-twin.spec.ts`), authored here in CAM, one per
  live beat, driving the cleared Show step for step.
- Media goes to the capture output location (`docs/devpost/figures/_demo-run/beats/` and
  object storage), never committed to git.

## Method (per First AD)

1. Author or update the beat's `web/e2e/beats/twoside-<beat>.spec.ts` to drive the cleared
   Show in order at the capture settings.
2. Record the beat (silent screen capture, one clip).
3. Test the capture by Reading the captured frames and confirming against what is on
   screen: full Show visible in frame and in order; crop lines up with room for the
   honesty caption; clean timing, no dead air; no mid-take runtime error or stall; the
   take matches the Show step for step; the real honesty figure is legible.
4. Write `findings/CAM-<beat>.md`: CAPTURE OK / RESHOOT, the take path, and the
   Read-examined frame observations.

Visual verification is binding: a capture is never OK from the recording command alone.

## Output

- `findings/CAM-<beat>.md` per beat; `CAM-ROLLUP.md`.
- The new `web/e2e/beats/twoside-*.spec.ts` specs (product-test code, committable on the
  operator gate; the recorded media is not).

## Advance gate

CAPTURE OK advances to SCR. RESHOOT returns to CAM, or to BLK if a moving part regressed.

## Operator gate

Capture-start is an operator gate when it consumes a paid surface or a long Playwright run
on a shared host. The director requests the green light through O0.

# Stage 3, SCR (screen test, the real approval), waveset charter

Family DSCR. Parent: `../PROGRAM.md`. Rubric: `SCREEN_TEST_RUBRIC.md`. Enters per take only
after CAPTURE OK in `../cam/CAM-ROLLUP.md` (live beats) or directly for slide beats.

## Intent

The Director scores each take against the binary five-item rubric. First ADs assist by
pulling evidence; they never approve. There is no conditional approval: every item must
PASS for APPROVED. The output is `APPROVED_TAKES.md`, the only input the render lane may
use.

## Unit

The Director scores. One First AD per take may be dispatched to pull evidence (the
Read-examined frame for a captured beat, or the slide content for a slide beat).

## Method

1. For each take, the Director reads the beat record, the rubric, and the evidence.
2. Score R1 through R5 binary. Any FAIL is a RETAKE with the failed items numbered and the
   return target (CAM, or BLK if a moving part regressed).
3. APPROVED takes are written to `APPROVED_TAKES.md` with take path, rubric score, the
   on-screen caption text, and locks confirmed.

## Slide beats

C1 and C2 skip BLK and CAM and are scored here as slide content (R1 through R4 read as
slide; R5 reduces to the honesty locks holding and figures keeping their real values).

## Output

- `findings/SCR-<beat>.md` per take: APPROVED / RETAKE with scores.
- `APPROVED_TAKES.md`: the signed manifest the render lane consumes.

## Hard limit

No conditional approval. No render before the signed manifest. The Director signs;
operator gates govern any commit of test specs and the render itself.

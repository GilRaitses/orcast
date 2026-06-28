# Screen-test rubric (SCR)

Binary. Every item must PASS for APPROVED. No conditional approval. Evidence is a
Read-examined frame for a captured beat, or the slide content for a slide beat.

| Item | Criterion | PASS means |
|---|---|---|
| R1 the Say lands | the narration line is supported by what is on screen | the take shows exactly what the Say claims; no capability is claimed that the take does not show |
| R2 the Show lands | the full Show is on screen, in order, at the demo viewport | no missing or truncated step; readable at 1280x900 |
| R3 the Honesty caption is present and truthful | the on-screen caption is legible and accurate against the honesty locks | every figure keeps its real value; the 0% promoted shows as 0% with its gate caveat; modeled is labeled modeled; detections labeled confidence scores; direction labeled direction |
| R4 the take matches the Evidence | the named Evidence is real | the render, panel, trace, detector output, or turn is real, not staged or mocked |
| R5 camera-ready and locks hold | clean crop and timing, room for the caption | no mid-take error, no dead air, all eight honesty locks hold; for A-side beats no reviewer-only copy on screen |

## Per-beat lock focus (from PROGRAM.md section 4)

- A1, A4: lock 1 (0% shown with gate caveat, real number), lock 2 (modeled probability).
- A2, A3: lock 2, lock 8 (no reviewer-only copy on the public path).
- A5, B2: lock 3 (detections are confidence scores, not ground truth).
- A6: lock 6 (low-weight attribution, effort-biased sightings).
- B1: lock 2 (estimates, not labels).
- B3: lock 4 (modeled not measured; research sandbox).
- C1: lock 5 (direction, chartered not shipped).
- C2: all locks; figures keep their real values (nine-table proof, architecture).

## Outcome

- APPROVED: write to `APPROVED_TAKES.md` with take path, R1-R5 = PASS, caption text, locks
  confirmed.
- Any FAIL: RETAKE with the failed item numbers and the return target (CAM, or BLK if a
  moving part regressed). The render lane never sees a RETAKE.

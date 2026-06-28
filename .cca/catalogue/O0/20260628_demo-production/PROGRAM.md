# orcast demo-production program (director-based)

Curated 2026-06-28. This program replaces the old A-side cut and the blocked B-side
`DEMO` waveset as the canonical orcast submission video. It is modeled directly on the
pax director briefing
(`/Users/gilraitses/pax/.cca/catalogue/O0/20260628_demo-production/DIRECTOR_PREPRODUCTION_WAVESET_BRIEFING.md`)
and instantiated for orcast: the role model, the four-stage chain, the gates, and the
binary screen-test rubric are kept verbatim; the beat set, the SET prerequisites, the
honesty locks, and the capture settings are orcast's.

Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`. Capture and assembly:
`~/.cursor/skills/demo-video-assembly/SKILL.md` and `~/.cursor/skills/pax-demo-capture/SKILL.md`.

## 1. Core thesis

A demo render is gated behind film discipline. No beat is rendered until it has been
rehearsed, captured, tested, and approved. There is no conditional approval at the final
gate: a beat is APPROVED or it is not. This replaces "the build looks done, capture it"
with a four-stage chain every beat must clear.

## 2. Role model (do not collapse)

| Role | Who | Does | Does NOT |
|---|---|---|---|
| O0 / central orchestrator | operator-facing thread | charters the program, holds the map, resolves director escalations, surfaces operator gates | run a stage itself |
| Director | the dispatched orchestrator of one stage waveset | charters and runs the stage, dispatches First ADs in parallel, confirms the rollup, is the creative approval authority at SCR | edit product code; capture outside CAM; render |
| First AD | the parallel subagents a director dispatches, one per beat or per prerequisite | clear / capture / verify / pull evidence for one unit, write one card | touch another unit's files; edit product code; commit; approve |
| Operator | the human | holds commit, push, program-promotion, paid/GPU/render-start gates | get solicited directly by a First AD |

Escalation: First AD to Director; Director resolves or escalates to O0; only operator
gates reach the human. No First AD blocks on the human, fakes a result, or invents a take.

## 3. The chain

```
BEAT_SET --> [0 SET] --> [1 BLK] --> [2 CAM] --> [3 SCR] --> DEMO render (approved takes only)
```

| Stage | Family | One First AD per ... | Produces | Advance gate |
|---|---|---|---|---|
| 0 SET (stage readiness) | DSET | environment prerequisite | `SET-<prereq>.md` READY / NOT READY + `READINESS.md` | director confirms manifest; ports/pids recorded; READY only from a Read-examined runtime check |
| 1 BLK (blocking rehearsal) | DBLK | live beat | `BLK-<beat>.md` each moving part CLEARED / BLOCKED + `BLK-ROLLUP.md` | beat advances only when every moving part is CLEARED |
| 2 CAM (camera test) | DCAM | cleared beat | `CAM-<beat>.md` CAPTURE OK / RESHOOT + take path + Read-examined frames + `CAM-ROLLUP.md` | take advances only on CAPTURE OK |
| 3 SCR (screen test) | DSCR | take (director scores; First ADs pull evidence) | `SCR-<beat>.md` APPROVED / RETAKE + `APPROVED_TAKES.md` | director signs the manifest; render uses nothing else |

Stages run in sequence; First ADs run in parallel within a stage. Lane homes:
`set/`, `blk/`, `cam/`, `scr/` under this folder; render handoff in `RENDER_HANDOFF.md`.

## 4. orcast honesty locks (enforced at SCR R3 and R5, on every captured beat)

1. Every confidence value is shown with its gate caveat and its real number. The honest
   0% promoted confidence is shown as 0% with the gate caveat, never hidden, rounded up,
   or implied higher.
2. Encounter forecasts are labeled as a modeled probability or estimate, never as an
   observed sighting.
3. Acoustic detections are labeled as model confidence scores, not human-reviewed
   ground truth.
4. The 3D twin is labeled modeled, not measured, and shown as a research-sandbox surface,
   not a shipped production route.
5. dtag replay, the full collaborative-annotation workbench, and the orchestration console
   are named as direction (chartered, not shipped). No shot implies they ship today.
6. Provenance and lineage caveats hold on stewardship beats: low-weight attribution on
   approved community reports, effort-biased sightings.
7. Show only what is built. No staged or mocked beats. Every Evidence is a real rendered
   surface, trace, panel, or turn.
8. No reviewer-only or internal copy appears on any public-tier capture. The CXR redaction
   discipline holds on every A-side beat (no promotion-blocker copy, raw agent IDs, skill
   manifest, or `ui_intent` strings on the anonymous path).

Origin of the honesty constraint: `.sst/tracked_limits_register_v1.json`,
`docs/devpost/PRODUCT_NARRATIVE_2026.md`, and the CXR lane.

## 5. Binary screen-test rubric (SCR; every item PASS for APPROVED, no conditional approval)

- R1 the Say lands. The narration line is supported by what is on screen; it claims no
  capability the take does not show.
- R2 the Show lands. The full Show is on screen, in order, readable at the demo viewport;
  no missing or truncated step.
- R3 the Honesty caption is present and truthful. Legible and accurate against the locks;
  every figure keeps its real value.
- R4 the take matches the Evidence. The named Evidence is real, not staged or mocked.
- R5 camera-ready and locks hold. Clean crop and timing, no mid-take error, room for the
  caption, all honesty locks hold.

APPROVED writes the take to `APPROVED_TAKES.md` with take path, rubric score, caption
text, and locks confirmed. Any FAIL is a RETAKE with the failed items numbered and the
return target (CAM, or BLK if a moving part regressed).

## 6. Beat set

The two-sided-loop beat set is in `BEAT_SET.md` (Say / Show / Evidence / Honesty /
Film-state per beat, live vs slide, capturable-now vs needs-build). It is the single
source the four stages and the render lane consume.

## 7. Capture settings (orcast)

- Viewport 1280x900, `DEMO_RECORD=1`, one silent clip per beat, gif loop exported from the
  same recording. Media to the capture output location, never git.
- Specs live in `web/e2e/beats/` (new two-sided-loop specs authored in CAM, one per live
  beat). Narration voice: orcast XTTS clone via `tools/testing/tts_narrate.py` /
  `tts_clone.py`.

## 8. Discipline invariants (all stages)

- One First AD per unit, disjoint scope. File-ownership discipline keeps the parallel wave
  safe.
- First ADs clear / capture / verify and report; they never approve and never edit product
  code.
- No capture outside CAM. No approval outside SCR. No render before the signed manifest.
- No commit or push inside the stage wavesets. Commit, push, program promotion, and any
  paid/GPU/render start are operator gates.
- No reassurance bias. Every READY, CLEARED, CAPTURE OK, and PASS cites a Read-examined
  runtime or frame observation, never an assumption.
- The escalation catch is in every dispatch.

## 9. Registry

Families DEMO-PROD (umbrella), DSET, DBLK, DCAM, DSCR, and the render lane DRENDER are
registered in `docs/devpost/waves.registry.yaml`. The render is operator-gated.

# BLK-A4, provenance and the gates

Verdict: CLEARED (with 1 presentation-delta note). Advances to CAM.

Prereqs: SET-web READY, SET-maps READY, SET-forecast READY.

## Moving parts

1. Tap a cell -> provenance with kernels + verdicts — CLEARED (substance). Clicking a
   water cell on the scene surfaced, in the console, a `FITNESS GATES` panel
   ("This forecast is modeled, not a direct observation. It is a likelihood, not a
   certainty." + the full integrity-conditions list) and a Guide "Provenance Panel"
   with a kernel-contributions table (Diel phase 0.608, contribution +0.704, status
   Active; Lunar ...). Backed by `/api/be/api/provenance` 200 returning
   `kernel_contributions` (diel available; lunar beats_null), `confidence 0.0`,
   `caveats` (integrity conditions), `nearby_sample` (10), and a `trace_note` with
   back-link ids (fit_plan_id, snap_id, repr_id, run_id). Files:
   `web/app/components/ProvenanceModal.tsx`, `web/app/components/ProvenanceGraph.tsx`,
   `src/aws_backend/routers` provenance.
2. `/gates` integrity conditions + Level 1 PSTH — CLEARED. `/gates` renders the
   integrity-conditions list and the Level 1 PSTH rows (diel, tide, lunar, season
   with modulation / null_z / null_p / beats_null; lunar+season beat null). File:
   `web/app/gates/page.tsx`.

## Presentation-delta note (numbered, not a hard block)

1. The standalone `ProvenanceModal` popup (`web/app/components/ProvenanceModal.tsx`,
   `data-demo="provenance-modal"`, heading "Why is this cell hot?") did NOT open via
   the live home/explore 3D-scene cell-tap; the scene routes the tap to a console
   grounding turn instead (CDP: `hasProvenanceModal:false`). All A4 Evidence (kernel
   contributions, gate verdicts, integrity conditions) still renders via the console
   panel + Guide table + `/gates`. If the beat specifically needs the modal popup,
   that surface (`MapHero` / `ExploreGuidePanel` `provenancePick`) is not triggered by
   the current scene cell-tap; CAM should capture the console provenance panel + Guide
   table + `/gates`, or the charter should update A4's Show wording.

## Honesty caption

Presentable. "single station, unreviewed acoustic candidates, covariates excluded
when data does not support them" render in both the console gates panel and `/gates`.
Locks 1 and 3 hold.

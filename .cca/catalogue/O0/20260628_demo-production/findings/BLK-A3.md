# BLK-A3, one forecast grounds many trips (trip branches)

Verdict: CLEARED. Advances to CAM.

Prereqs: SET-web READY.

## Moving parts

1. Trip-branch control present — CLEARED. The home console renders the orienting
   chips "Planning a visit", "I'm here now", "Kayaking", "Just curious". File:
   `web/app/components/ExploreGuidePanel.tsx` (orienting question chips).
2. Selecting a branch routes and re-grounds — CLEARED. Clicking "Planning a visit"
   set the chip to active/pressed, pre-filled a branch-specific prompt ("I'm planning
   a visit to the San Juans. How do I get there and what should I plan around?"), and
   the subsequent turn produced visiting-mode panels (`COMPARE PLACES`,
   `CONNECTION PLAN`) distinct from the default. Branch routing backed by
   `src/aws_backend/casting/planner.py` (`_branch_plan`, branch=visiting ->
   compare_places + connections_plan).

## Honesty caption

Presentable. Each branch reads the same modeled forecast; the connection plan is
labeled "modeled" with "Not enough information to judge the connection" and
"modeled, never measured" caveats. Lock 2 holds.

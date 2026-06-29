# BLK-A2, intent becomes planning objects (public console)

Verdict: CLEARED. Advances to CAM.

Prereqs: SET-web READY, SET-maps READY, SET-session not required (public path).

## Moving parts (cleared in beat order, in the running app)

1. Public console accepts the prompt — CLEARED. On `/`, the Ask box accepts input;
   the Ask button enables after a branch/prompt is set. File:
   `web/app/components/ExploreGuidePanel.tsx` (`sendTurn`).
2. Planning panels render — CLEARED. After sending "I'm planning a visit to the San
   Juans...", the console rendered: `COMPARE PLACES`, `CONNECTION PLAN` (Overall
   modeled; drive/ferry legs), `INTERACTION TRACE` (steps 1-6: Set up the guide,
   Plan the answer, Gather grounded data x3, Write the reply), the Guide reply, and
   deep links Gates / Explore / Explore pin. Backed by the live turn
   `/api/be/api/interactions` 200 (source bedrock, managed_agent_id explore-guide-v1,
   annotations gate_citation + deep_link). Files:
   `web/app/components/ActiveSurfaceHost.tsx`, `src/aws_backend/routers/interactions.py`.
3. CXR redaction holds on the public path — CLEARED. CDP body probe:
   `reviewerLeak:false`, `showsCastLabel:false` (no `ui_intent`, `skill_plan`,
   `resolved_spec_hash`, `surface-planner-v1`, `X-ORCAST`, `agent_orcast_automation`,
   `managed_agent`, or `Cast:` copy on the home console). Lock 8 holds.

## Honesty caption

Presentable. The panels carry modeled-probability labels: "Today's forecast is
modeled from recent patterns, not a live sighting feed. It is a likelihood, not a
certainty." and "WSDOT travel-time coverage ... is modeled, never measured." Locks
2 and 8 hold; no reviewer-only copy on screen.

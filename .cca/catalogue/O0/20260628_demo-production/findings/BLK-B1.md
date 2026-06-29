# BLK-B1, ask-the-console orchestrator trace (reviewer)

Verdict: trace CLEARED via keyed API; in-browser reviewer console BLOCKED-on-session;
1 numbered defect (agent-key tier_block). Does not fully advance as a reviewer beat.

Prereqs: SET-session READY (agent key).

## Moving parts

1. Plan turn -> orchestrator trace — CLEARED (keyed API). `/api/interactions/plan`
   with `surface-planner-v1` + the `X-ORCAST-Agent-Key` header returns 200 with
   `planner_agent_id: surface-planner-v1`, `panels: [gates_summary, explore_trace]`,
   `skill_plan: [fetch_gates, fetch_hotspots]`, and the orchestrator trace
   `prepare.steps`: resolve_agent -> plan_output -> fetch_gates -> fetch_hotspots.
   Files: `web/app/api/interactions/plan/route.ts`,
   `src/aws_backend/routers/interactions.py` (`plan_cast_interaction`),
   `src/aws_backend/casting/planner.py`.
2. Reviewer console renders the trace in-browser — NOT exercised. The reviewer
   console is `?planner=1` (`web/app/components/ExploreGuidePanel.tsx`, line 109,
   `plannerMode`), and its plan fetch is keyed; an unauthenticated browser turn
   throws "Reviewer sign-in required for surface planner" (401). The browser cannot
   carry the server-side agent key, so the in-browser reviewer console needs WorkOS
   reviewer sign-in (operator gate) or the CAM Playwright `installAgentAuth`.

## Numbered defect

1. Reviewer-tier T2/T3 panels tier_block via the agent key. A planner message that
   plans T2/T3 skills (e.g. "review"/"dossier" -> `fetch_review_dossier_summary`,
   `fetch_decision_records`) returns 400 `{"error":"invalid_ui_intent","reason":
   "tier_blocked"}`. Root cause: the backend computes `public_route = identity.
   reviewer_id is None` (`src/aws_backend/routers/interactions.py:218`), and on the
   `/api/interactions/plan` path the agent reviewer identity is treated as public, so
   `validate_agent_skills(..., public_route=True)` blocks T2/T3
   (`src/aws_backend/casting/manifest.py:71`). Effect: the reviewer-distinguishing
   surfaces (decisions_table, review_dossier) are unreachable via the agent key, so
   even the CAM Playwright agent-key capture cannot show them. Note: the `/api/be`
   protected paths DO honor the agent reviewer (moderation 200), so this gap is
   specific to the surface-planner plan route. Fix (build/operator, not First-AD):
   honor the agent reviewer identity for tier on `/api/interactions/plan`, or capture
   B1's reviewer-tier panels with a WorkOS reviewer session.

## Honesty caption

Presentable for the trace ("narration is grounded in live context; outputs are
estimates, not labels", lock 2). The basic T0/T1 trace is agent-key-capturable; the
T2/T3 reviewer panels need the defect fix or a WorkOS reviewer.

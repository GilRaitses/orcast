# Stage 1 BLK, rollup

Director: DEMO-PROD. Stage: BLK (DBLK). Live beats A1-A6, B1, B2, B3. Slide beats
C1, C2 skip BLK. Every CLEARED below cites a Read-examined live observation
(rendered pane or real API turn) recorded in `findings/BLK-<beat>.md`. Capture
target `https://orcast-h0.vercel.app`.

## Beat-by-beat

| Beat | Verdict | Basis |
|---|---|---|
| A1 | BLOCKED | Map + lowercase hero CLEARED, but no confidence meter / 0% promoted on `/` (CDP `hasConfidenceWord:false`); the honest 0% lives on `/gates`, not `/` |
| A2 | CLEARED | Public console turn renders COMPARE PLACES + CONNECTION PLAN + INTERACTION TRACE + Guide reply; modeled labels present; CXR holds (no reviewer copy) |
| A3 | CLEARED | Branch chips present; "Planning a visit" routes and re-grounds to visiting-mode panels |
| A4 | CLEARED (note) | Cell-tap surfaces gates + kernel-contribution table + integrity conditions; `/gates` PSTH renders. Note: standalone `ProvenanceModal` popup not triggered by scene cell-tap (console panel used instead) |
| A5 | CLEARED | `/ask` pin + Check sighting returns a Bedrock-badged grounded reply, likelihood vs verification, lock 3 caveats |
| A6 | BLOCKED-on-render | Moderation queue data CLEARED via agent key (200, 6 pending); in-browser journal/moderation panes + approve write not exercised (need WorkOS or CAM Playwright; approve mutates prod) |
| B1 | trace CLEARED / console BLOCKED | Keyed plan returns the orchestrator trace (resolve_agent -> plan_output -> fetch_gates -> fetch_hotspots); in-browser reviewer console needs a session; T2/T3 panels tier_block via agent key (defect) |
| B2 | BLOCKED | Reviewer annotation surface + provenance lineage not observed; planner T2/T3 tier_block via agent key + no WorkOS reviewer session |
| B3 | CLEARED (scoped) | `/journey` twin renders, land at waterline, non-random W1 camera director. Labeled-place pan + deployed route are needs-build; CAM scopes to the sandbox scene |

## Beats advancing to CAM

- Fully CLEARED: A2, A3, A5.
- CLEARED with a documented note (CAM scopes/uses the noted surface): A4 (capture the
  console provenance panel + Guide kernel table + `/gates`, not the modal popup),
  B3 (capture the sandbox twin scene + existing East Sound choreography, sandbox/
  modeled caption).
- Partially clearable at CAM via the agent-key Playwright path (data layer verified,
  in-browser pane render to confirm at CAM): A6 (moderation queue), B1 (the T0/T1
  orchestrator trace only).

## Not advancing without an operator action

- A1 — BLOCKED. Needs a build/charter fix (confidence meter + 0% on `/`, or re-point
  A1 to `/gates`).
- B1 reviewer-tier panels and B2 (annotation + lineage) — BLOCKED. Need either the
  backend tier fix (honor the agent reviewer identity for tier on
  `/api/interactions/plan`) or a WorkOS reviewer sign-in for capture.

## Operator gates surfaced (to O0)

1. WorkOS reviewer sign-in: required to render the in-browser reviewer/user panes for
   A6 (journal + moderation), B1 (reviewer console), B2 (annotation). The browser
   cannot carry the server-side agent key; only the CAM Playwright `installAgentAuth`
   route injection or a WorkOS session renders them.
2. Agent-key tier_block defect (build/operator-actionable): on
   `/api/interactions/plan`, `public_route = identity.reviewer_id is None`
   (`src/aws_backend/routers/interactions.py:218`) treats the agent reviewer as
   public, so T2/T3 reviewer skills tier_block (`src/aws_backend/casting/manifest.py:71`).
   This blocks B1's reviewer-tier panels and B2 even for the agent-key capture path.
   The `/api/be` protected paths are unaffected (moderation 200 via the key).

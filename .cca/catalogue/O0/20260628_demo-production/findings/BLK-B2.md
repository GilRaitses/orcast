# BLK-B2, provenance and hydrophone annotation (reviewer)

Verdict: BLOCKED-on-reviewer-session + agent-key tier_block. Not cleared; not
observed rendering.

Prereqs: SET-session READY (agent key) — but see the tier_block defect below.

## Moving parts

1. Hydrophone-detection annotation surface — NOT observed. The annotation surface is
   a reviewer-tier console panel (`HydrophoneSignalPanel`, rendered inside
   `web/app/components/ActiveSurfaceHost.tsx`). The live hydrophone SIGNAL skill
   (`fetch_live_hydrophones`) is T0/public, but the ANNOTATION (write) capability and
   the planner-driven reviewer panels require a non-public route. I could not render
   the annotation surface from a real observation in this thread.
2. Provenance lineage — NOT observed. The lineage renders via
   `ProvenanceGraphFromPrepare` (`web/app/components/ProvenanceGraph.tsx`) inside
   `ActiveSurfaceHost`, driven by the surface-planner (`provenance_graph` panel in
   `surface-planner-v1` allowed_panels). This is a planner-driven reviewer surface.

## Why blocked

Same root cause as the B1 defect: B2's reviewer panels are driven by the
`/api/interactions/plan` surface-planner, whose T2/T3 skills tier_block via the agent
key (`public_route = identity.reviewer_id is None`,
`src/aws_backend/routers/interactions.py:218`; `src/aws_backend/casting/manifest.py:71`).
The browser cannot carry the agent key, and there is no WorkOS reviewer session in
this thread. So neither the annotation surface nor the provenance-lineage panel could
be rendered from a real observation.

## Numbered defects / gates

1. Agent-key tier_block on the surface-planner path (see BLK-B1 defect 1) blocks the
   reviewer-tier annotation/lineage panels even for the CAM Playwright agent-key path.
2. Operator gate: rendering B2 in a real browser requires a WorkOS reviewer sign-in.

## Honesty caption

Would be: "a detection is a model confidence score, not reviewed ground truth;
lineage caveats hold" (locks 3, 6). Not presentable until the surface renders.

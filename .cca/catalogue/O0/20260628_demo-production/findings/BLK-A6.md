# BLK-A6, journal to moderation (stewardship seam)

Verdict: BLOCKED-on-render in this rehearsal (data layer CLEARED). CAM path exists.

Prereqs: SET-session READY (agent key works; in-browser pane render uses Playwright
`installAgentAuth`).

## Moving parts

1. `/moderation` queue (reviewer pane) — data layer CLEARED, in-browser render NOT
   exercised here. `/api/be/api/community/submissions?status=pending` returns 401
   unauth and 200 with the `X-ORCAST-Agent-Key` header (6 pending submissions,
   reviewer-only PII). Unauthenticated `/moderation` in the browser renders only
   "Reviewer access required. Sign in" (no reviewer pane). The browser cannot send
   the agent key, so the pane renders only via WorkOS reviewer sign-in (operator
   gate) or the CAM Playwright `installAgentAuth` route injection. Files:
   `web/app/moderation/page.tsx`, `web/app/api/be/[...path]/route.ts`.
2. `/moderation` approve write — NOT exercised. The approve endpoint is wired
   (`web/app/moderation/page.tsx` `postJSON('/api/community/submissions/{id}/approve')`
   -> `src/aws_backend/routers/community.py`). I did not execute it because it mutates
   prod data (approves a queued sighting into low-weight attribution). The write
   should be exercised in the CAM capture context, not in BLK.
3. `/journal` save + publish — NOT exercised. `/api/be/api/journal` returns 401
   unauth (protected path). The journal pane is a signed-in-user surface; the
   in-browser render needs a WorkOS user session or the Playwright agent-key
   injection. (A keyed GET via `/api/be/api/journal` hung on App Runner latency and
   was killed; the auth gate itself is confirmed by the 401.)

## Why blocked here

The in-browser authenticated panes (journal entries, moderation approve) cannot be
rendered in this director thread: the browser has no WorkOS session and cannot carry
the server-side agent key. The moderation data layer is verified reachable via the
key, so the CAM Playwright capture (`installAgentAuth`) can render the panes. This is
an operator/CAM-harness gate, not a product defect, and is distinct from the
`tier_block` defect (B1/B2): the `/api/be` protected paths honor the agent reviewer
identity (moderation 200), so A6's panes are agent-key-capturable at CAM.

## Honesty caption

Presentable at CAM. Approved reports carry low reliability weight; sightings are
effort-biased (lock 6).

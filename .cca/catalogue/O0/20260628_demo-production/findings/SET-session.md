# SET-session

Status: READY

Prerequisite: reviewer/agent session for journal, moderation, planner, reviewer
console, serving A6, B1, B2.

## Read-examined check

Authenticated runtime check against the prod reviewer API
`/api/be/api/community/submissions?status=pending` (the same endpoint the
`/moderation` queue reads):

Unauthenticated:

```
status=401
{"error":"Authentication required"}
```

With the `X-ORCAST-Agent-Key` header (value loaded from the repo-root
`.agent-credentials.env`, never echoed):

```
status=200
{"status":"success","total_count":6,"submissions":[{"id":"f3afc44e...","place":"Lime Kiln Point",...,"observer_name":"agent@orcast.dev","status":"pending",...}, ...]}
```

The local agent key matches the prod-deployed `ORCAST_AGENT_KEY`: the request
returns 200 with the reviewer-only moderation queue (6 pending submissions, with
PII fields such as `observer_name`). Unauthenticated `/moderation` in the browser
renders only "Reviewer access required. Sign in" (no reviewer pane), confirming the
gate is real.

## In-browser pane rendering (capture mechanism, for CAM)

The browser bundle never receives the key. The reviewer pane renders in-browser by
injecting the header on same-origin requests via Playwright route interception:
`web/e2e/loadAgentCreds.ts` -> `installAgentAuth(page)` (default base already
`https://orcast-h0.vercel.app`). The WorkOS sign-in path is the interactive
alternative. This is a CAM capture detail, not a SET blocker, because the session
itself is verified working in prod.

## Evidence

- Auth resolution: `web/lib/agentAuth.ts` (`agentUserFromHeaders`, `resolveReviewer`).
- Proxy gate: `web/app/api/be/[...path]/route.ts` (`PROTECTED_PATHS` includes
  `api/community/submissions`; agent identity injected after the auth check).
- Capture injection: `web/e2e/loadAgentCreds.ts` (`installAgentAuth`).
- Credential file: `.agent-credentials.env` (repo root, gitignored, `ORCAST_AGENT_KEY`
  64 chars, `ORCAST_AGENT_REVIEWER_ID=agent_orcast_automation`).

## Ports / pids

None.

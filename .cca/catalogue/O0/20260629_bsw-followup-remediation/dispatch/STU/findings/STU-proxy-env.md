# STU-R3 findings: proxy authorization, agent-token path, ORCAST_API_BASE deploy wiring

Read-only research. Author: STU-R3. Scope: `web/app/api/be/[...path]/route.ts`, `web/lib/agentAuth.ts`, and the `ORCAST_API_BASE` deploy wiring across the repo. No code edited.

Client target under study: `HttpAnnotationStore` posts and reads at `/api/be/api/dtag/annotations` (`web/lib/annotation/store.ts:84`). Inside the proxy the joined backend path is `api/dtag/annotations`.

## 1. The isPublicRequest classification model

The proxy classifies every request through `isPublicRequest(method, path)` where `path` is the joined backend path after `api/be/`. If the request is not public, it requires an authenticated identity (WorkOS user session OR a valid agent token). The key `X-ORCAST-Key` is injected only after this check passes.

Classification order in `route.ts`:

| Check | Function | Behavior |
|---|---|---|
| Specific public POSTs | `isPublicRequest` body | A hard-coded list of POST paths returns public true. The list is `api/sighting-assist`, `api/explore/sessions`, `api/explore/turn`, `api/interactions`, `api/interactions/prepare`, `api/interactions/plan`, `api/interactions/narrate`, `api/interest`. |
| Public GET | `isPublicGet` | GET only. Returns false if path matches `PROTECTED_PATHS`. Otherwise returns true only if path matches `PUBLIC_GET_PATHS`. |
| Everything else | falls through | Not public. Requires auth in `forward()`. |

`matchesPath(path, entries)` matches an entry exactly or as a path prefix of the form `entry + "/"`. So `api/sightings` matches `api/sightings` and `api/sightings/anything`.

`PUBLIC_GET_PATHS` (the only public reads):

```
api/gates, api/provenance, api/sighting-assist/status, api/explore/status,
api/interactions/status, api/realtime/events, api/status, health, api/hotspots,
api/sightings, api/verified-sightings, api/environmental, api/live-hydrophones,
api/onc/hydrophone-signal, api/onc/archivefile, forecast
```

`PROTECTED_PATHS` (listed for clarity, never public even for GET):

```
api/community/submissions, api/decision-records, api/review-dossier, api/journal
```

### Where api/dtag/annotations lands today

`api/dtag/annotations` is NOT in `PUBLIC_GET_PATHS` and NOT in any public POST branch of `isPublicRequest`. It is also not in `PROTECTED_PATHS`, but that list is only a documentation aid. The operative rule is the default: any path not in `PUBLIC_GET_PATHS` and not in the public POST list falls through as not public.

Confirmed current behavior for `api/dtag/annotations`:

| Request | isPublicRequest | Effect in forward() |
|---|---|---|
| `POST /api/be/api/dtag/annotations` | false | Requires WorkOS session or agent token. 401 if neither. |
| `GET /api/be/api/dtag/annotations` (list) | false | Requires WorkOS session or agent token. 401 if neither. |
| `GET /api/be/api/dtag/annotations/{id}` | false | Requires WorkOS session or agent token. 401 if neither. |

Default behavior for a non-allow-listed GET is deny. It needs a session (or agent token). It is NOT public by default.

This means the annotation write path is ALREADY authenticated-only with no proxy edit. The POST and both GETs already demand auth today. The current 500 responses observed by BSS (`...gate_screenshots/VERDICT.md`) are not an auth gap; they are `ORCAST_API_BASE not configured` on the host dev server plus the missing backend route. On production where `ORCAST_API_BASE` is set, an unauthenticated POST/GET to this path returns 401, and the backend route does not yet exist to answer an authenticated one.

## 2. The exact minimal proxy change to name for STU-INT

The locked decision forbids adding `api/dtag/annotations` to the public POST allow-list. The write must be authenticated. Given the default-deny model above, two options exist. I recommend Option A.

### Option A (recommended): authenticated read and write, no functional proxy change

The desired behavior is POST authenticated, GET list/get authenticated. That is ALREADY the default for any non-allow-listed path. So the functional proxy change is a no-op. No edit to `isPublicRequest`, `PUBLIC_GET_PATHS`, or the POST branches is required for the path to work once the backend route exists.

The only optional, non-functional edit is a documentation-only entry. Add `api/dtag/annotations` to `PROTECTED_PATHS` so the intent reads explicitly in the source:

```ts
const PROTECTED_PATHS = [
  "api/community/submissions",
  "api/decision-records",
  "api/review-dossier",
  "api/journal",
  "api/dtag/annotations",
];
```

This is safe and changes nothing at runtime for this path, because `isPublicGet` already would not return true for it (it is not in `PUBLIC_GET_PATHS`). It only documents that the path is intentionally session-gated. STU-INT may include or skip this line; it is cosmetic.

This option matches the locked not-public posture exactly and is the cleanest. The change is effectively zero functional lines.

### Option B (not recommended without an O0 decision): public community read

If O0 wants the annotation LIST and GET to be readable by anonymous community users, the GET path must be added to `PUBLIC_GET_PATHS`:

```ts
const PUBLIC_GET_PATHS = [
  // ...existing entries...
  "api/dtag/annotations",
];
```

Because `matchesPath` treats an entry as a prefix, this single entry makes BOTH `GET api/dtag/annotations` (list) and `GET api/dtag/annotations/{id}` public. The POST still stays authenticated, since the POST branch is not touched and `isPublicGet` is GET-only.

This widens read exposure of all annotations to the anonymous public. That is an O0 data-exposure decision, not a default. It also conflicts with the locked not-public posture for the path. Do not take this without an explicit O0 sign-off.

### Recommendation

Take Option A. The write path needs no proxy edit. Optionally add the one documentation line to `PROTECTED_PATHS`. Keep reads authenticated to match the locked posture. Do not add anything to `PUBLIC_GET_PATHS` or the public POST list.

## 3. The agent-token path for live accept without a browser session

`web/lib/agentAuth.ts` defines the automation identity. An automated client authenticates by sending an HTTP header instead of a WorkOS cookie.

Mechanism:

- Header name: `X-ORCAST-Agent-Key` (case-insensitive; `agentUserFromHeaders` reads both `x-orcast-agent-key` and `X-ORCAST-Agent-Key`).
- Server secret: env `ORCAST_AGENT_KEY`. If the env is empty, `agentUserFromHeaders` returns null and the header is ignored.
- Match rule: the provided header value must equal `ORCAST_AGENT_KEY` exactly. On match it returns the reviewer identity `{ id: ORCAST_AGENT_REVIEWER_ID, email: ORCAST_AGENT_REVIEWER_EMAIL }`, defaulting to `agent_orcast_automation` and `agent@orcast.dev`.

How `forward()` uses it (`route.ts:142-155`): it calls `agentUserFromRequest(req)` first. For a non-public request, if `agentUser` is present it is accepted as the authenticated identity and `withAuth()` (the WorkOS session lookup) is skipped entirely. So a valid agent key satisfies auth with no browser session. The proxy then injects `X-ORCAST-Trusted-Proxy: vercel`, `X-ORCAST-Reviewer-Role: reviewer`, `X-ORCAST-Reviewer-Id`, and `X-ORCAST-Reviewer-Email` to the backend via `reviewerProxyHeaders`, plus the server `X-ORCAST-Key`.

How STU-ACCEPT supplies it: the key lives in gitignored repo-root `.agent-credentials.env` as `ORCAST_AGENT_KEY`. Playwright loads it through `web/e2e/loadAgentCreds.ts` and injects `X-ORCAST-Agent-Key` on same-origin requests only (`installAgentAuth`). curl and CI gates pass `-H "X-ORCAST-Agent-Key: $ORCAST_AGENT_KEY"` (see `tools/waves/gates/*.sh`, `tools/testing/agent_smoke.py`, `docs/devpost/API_AGENTS.md`). The local key matches the prod-deployed `ORCAST_AGENT_KEY` on Vercel (confirmed in `.cca/.../findings/SET-session.md`).

Live accept round-trip without a browser:

```bash
# create
curl -sf -X POST "$WEB/api/be/api/dtag/annotations" \
  -H "X-ORCAST-Agent-Key: $ORCAST_AGENT_KEY" \
  -H "Content-Type: application/json" \
  -d '{ ...submission request... }'
# list
curl -sf "$WEB/api/be/api/dtag/annotations?deployment_id=$DEP" \
  -H "X-ORCAST-Agent-Key: $ORCAST_AGENT_KEY"
# get
curl -sf "$WEB/api/be/api/dtag/annotations/$ID" \
  -H "X-ORCAST-Agent-Key: $ORCAST_AGENT_KEY"
```

STU-ACCEPT can run create -> list -> get with the agent key alone, no WorkOS login.

## 4. The ORCAST_API_BASE deploy wiring

`route.ts:15` sets `const API_BASE = process.env.ORCAST_API_BASE ?? "";`. If empty, `forward()` returns `500 {"error":"ORCAST_API_BASE not configured"}` before any auth or upstream call. The proxy builds the upstream as `${API_BASE}/api/dtag/annotations`.

| Item | Value |
|---|---|
| Env var | `ORCAST_API_BASE` |
| Scope | Server only on the Vercel project. Never `NEXT_PUBLIC_`. |
| Where configured | Vercel project env for production (`web/.vercel` links to `orcast-h0`). Locally `web/.env.local` from `web/.env.example`. |
| Required value | The App Runner backend base URL. `docs/devpost/DEPLOY_VERCEL.md` records `https://pjrftm3bkv.us-west-2.awsapprunner.com`. The cloudflared host `https://orcast-api.aimez.ai` is the dormant rollback value. Hosting-consolidation state confirms App Runner is the sole upstream. |

### It is already wired for reads

Production public GETs through this same proxy already work, which proves `ORCAST_API_BASE` is set and reaches the backend. Examples in active CI gates: `GET /api/be/api/gates`, `/api/be/api/hotspots`, `/api/be/api/sightings`, `/api/be/api/provenance` (`tools/waves/gates/q1b-api-schema.sh`). These would 500 with `ORCAST_API_BASE not configured` if the env were unset.

On `api/dtag/deployments`: note it is NOT in `PUBLIC_GET_PATHS`, so it is authenticated-only through this proxy just like annotations. The backend dtag router exists (`src/aws_backend/routers/dtag.py` serves `GET /api/dtag/deployments`, `/dives/{id}`, `/feeding/{id}`). So an authenticated GET (agent key) to `/api/be/api/dtag/deployments` reaches a real backend route and returns data, which proves the dtag namespace itself is reachable through `ORCAST_API_BASE`. The proof that `ORCAST_API_BASE` is wired for reads in general comes from the public reads above; the proof that the dtag namespace specifically is reachable comes from the existing dtag deployments router. The annotations gap is the missing backend route plus the host dev server lacking the env, not the proxy env on prod.

### The precise deploy/env change for O0 to approve

The new `POST/GET /api/dtag/annotations` route is additive on the SAME App Runner service (`orcast-aws-backend`) that already answers `api/dtag/deployments` and the public reads. Because the base host does not change, `ORCAST_API_BASE` itself does NOT need a new value. The human gate is the BACKEND DEPLOY of the new route to App Runner, not a new env value.

State to O0 precisely:

- Backend deploy: ship the new `/api/dtag/annotations` route to App Runner `orcast-aws-backend`. This is the human gate.
- `ORCAST_API_BASE`: unchanged. It already points at App Runner and already serves the dtag namespace. No env edit required on prod.
- Vercel proxy: no functional edit (Option A). Optional one-line `PROTECTED_PATHS` documentation entry.
- Host dev server caveat: the `ORCAST_API_BASE not configured` 500 seen by BSS is a local dev-env gap, not a prod env change. STU-ACCEPT must run against a target that has `ORCAST_API_BASE` set (prod Vercel or a preview with the env), not the bare host dev server.

## 5. Non-GET retry and idempotency, double-submit risk for the annotations POST

`forward()` buffers the body into `init.body` and runs up to `maxAttempts = 2`. Retry rules (`route.ts:196-221`):

| Condition | Retried? |
|---|---|
| `fetch` throws (network) | Retried once for any method. After the last attempt, returns `502 upstream_unreachable`. |
| Upstream `503` | Retried once for ANY method, including POST. Rationale in code: a 503 from the App Runner edge means no healthy instance received the request, so it had no side effect and is safe to replay. |
| Upstream `502`, `504`, `404` | Retried once ONLY for idempotent GET (`idempotent = req.method === "GET"`). Not retried for POST. |

Implication for the annotations POST double-submit risk (hand to R4):

- A `503` on `POST /api/dtag/annotations` triggers an automatic proxy replay. The code assumes 503 means the request never reached an instance, so no side effect. If a real backend instance ever returns 503 AFTER beginning to persist an annotation, the replay would create a duplicate. R4 should confirm the backend never returns 503 mid-write, or design the create path to be idempotent (for example a client-supplied dedupe key or upsert on a stable annotation id) so a 503 replay cannot double-insert.
- A network throw on POST is also retried once. Same duplicate risk if the original request actually reached the backend and persisted before the connection dropped. R4 should account for this exactly-once concern at the backend layer.
- `502/504/404` on the annotations POST are NOT retried, so they carry no proxy-side double-submit risk; they surface to the client as-is.

R4 should treat the POST create as at-least-once under the proxy retry policy and add an idempotency guard at the backend.

## Summary for the STU orchestrator

- Proxy edit required: NO functional edit. `api/dtag/annotations` is already authenticated-only by default (not in `PUBLIC_GET_PATHS`, not in the public POST list). POST and both GETs already require a WorkOS session or agent token today. Optional non-functional one-liner: add `api/dtag/annotations` to `PROTECTED_PATHS` for documentation only.
- Recommended read auth posture: authenticated reads (Option A), matching the locked not-public posture. Do not add the path to `PUBLIC_GET_PATHS`. Only consider a public community read (Option B) under an explicit O0 data-exposure decision.
- Agent-token mechanism for live accept: send `X-ORCAST-Agent-Key` equal to `ORCAST_AGENT_KEY`. The proxy accepts it as the reviewer identity and skips WorkOS, so STU-ACCEPT can run create -> list -> get with curl or Playwright, no browser session. Key loads from gitignored `.agent-credentials.env`.
- ORCAST_API_BASE / backend-deploy change for O0: `ORCAST_API_BASE` does NOT change; it already points at App Runner and already serves the dtag namespace (proven by existing public reads and the dtag deployments router). The human gate is the BACKEND DEPLOY of the additive `/api/dtag/annotations` route to App Runner `orcast-aws-backend`. STU-ACCEPT must target an env that has `ORCAST_API_BASE` set (prod or a preview), not the bare host dev server.

Findings file path: `/Users/gilraitses/orcast/.cca/catalogue/O0/20260629_bsw-followup-remediation/dispatch/STU/findings/STU-proxy-env.md`

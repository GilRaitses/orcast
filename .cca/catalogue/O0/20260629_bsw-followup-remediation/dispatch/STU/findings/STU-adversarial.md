# STU-R4 adversarial findings: the annotation write path

Lane: BSWR-STU (studio-live-persistence). Role: R4 read-only adversarial research.
Scope: the net-new authenticated backend `POST /api/dtag/annotations`,
`GET /api/dtag/annotations` (list), and `GET /api/dtag/annotations/{id}`, conforming
to the client wire schema in `web/lib/annotation/serialize.ts`, persisting
provenance-tagged community annotations against the SIMULATED partnership-gated
DTAG deployment.

This is research only. No code was edited. The findings hand off to STU-Q for design
and to STU-ADV for verification of zero open P0/P1.

## How the existing auth model actually works

The proxy at `web/app/api/be/[...path]/route.ts` does the following for a non-allow-listed
POST such as `api/dtag/annotations`:

1. Rejects unauthenticated callers with 401 (`isPublicRequest` is false for this path).
2. Resolves identity from a WorkOS session or from the agent key (`agentUserFromRequest`).
3. Injects three trust signals into the upstream request:
   - `X-ORCAST-Key` (the shared secret, from `ORCAST_API_KEY`).
   - `X-ORCAST-Trusted-Proxy: vercel` (a fixed literal string, not a secret).
   - `X-ORCAST-Reviewer-Id` / `X-ORCAST-Reviewer-Email` / `X-ORCAST-Reviewer-Role`
     (the reviewer identity, role hardcoded to `reviewer`).

On the backend, `src/aws_backend/auth.py`:

- `require_api_key` compares `X-ORCAST-Key` against `settings.api_key`. In production it
  is always enforced. This is the ONLY cryptographic factor in the chain.
- `require_trusted_reviewer` checks that `X-ORCAST-Trusted-Proxy == "vercel"` and that a
  `X-ORCAST-Reviewer-Id` header is present. It does NOT verify any secret. The `vercel`
  marker and the reviewer id are both attacker-controllable strings.

The correct existing pattern is `routers/community.py` approve and reject, which depend on
BOTH `require_api_key` AND `require_trusted_reviewer`. The shared key is the real gate; the
reviewer headers ride on top of it once the key proves the caller is the proxy.

Key consequence for design: reviewer identity has no second factor. Anyone who holds the
shared key, or who can reach the backend on a route that omits `require_api_key`, can stamp
any `X-ORCAST-Reviewer-Id` and any role and be trusted. The new route must never trust the
reviewer headers without `require_api_key` in the same dependency set, and must never trust
provenance identity from the request body.

## Risk register

| id | risk | class | attack | impact | mitigation for STU-Q |
| --- | --- | --- | --- | --- | --- |
| R4-1 | Direct-backend header spoof auth bypass | P0 | If App Runner is internet-reachable and the annotations route omits `require_api_key`, an attacker sends `X-ORCAST-Trusted-Proxy: vercel` plus `X-ORCAST-Reviewer-Id: anyone` straight to the backend, since the trusted-proxy marker is a plain literal and reviewer headers carry no secret. | Write annotations as any forged identity, full impersonation, bypass of the not-public posture. | The route MUST depend on `require_api_key` AND `require_trusted_reviewer`, matching the community approve/reject pattern. Keep the App Runner ingress private to the proxy or enforce the key at the edge. Treat the `vercel` marker as non-authenticating. Derive the role server-side, do not trust the client role. |
| R4-2 | Provenance identity tampering | P0 | The client body carries `provenance.annotator_id`, `annotator_role`, and `source`. A community caller sets `source=expert` and `annotator_id=famous_scientist` to impersonate an expert author. | Forged authorship and trust labels on persisted records, corrupting the provenance contract. | Derive `annotator_id` and `annotator_role` server-side from the validated reviewer headers (`require_trusted_reviewer`), never from the body. Pin `source` to `community` for the human write path (or derive from the verified role). Ignore body-supplied identity fields entirely. |
| R4-3 | Provenance dataset, license, tool, h5 spoof | P1 | The body also carries `dataset`, `license_status`, `tool`, and `h5_refs[]`. A caller forges a permissive `license_status` or fake `h5_refs` to fabricate grounding. | Mislabeled license and false grounding claims on stored annotations. | Pin `dataset`, `license_status`, and `tool` from the server-side deployment record loaded by `dtag._load_deployments()`, not from the body. Validate `h5_refs` against an allow-listed set or drop them server-side. |
| R4-4 | Honesty-contract mislabel via unknown deployment id | P1 | The caller posts against a fabricated or future `deployment_id` that is not the simulated bundled example. | An annotation persists labeled real or unlabeled, breaking the locked simulated-only honesty contract. | Reject writes whose `deployment_id` is not in `_load_deployments()` with 404 or 422. Stamp `simulated` from `entry["simulated"]` of the deployment record, never from the client. The only writable deployment today is the simulated example. |
| R4-5 | PII leakage of reviewer email through the list read | P1 | The WorkOS email arrives as `X-ORCAST-Reviewer-Email`. If it is stored as or alongside `annotator_id` and the list or get read returns it via a blind `model_to_dict`, the email is exposed to every reader of the list. | Reviewer email disclosure, violating the locked no-PII-beyond-provenance rule. | Store the opaque WorkOS `reviewer_id` as the annotator identity, not the email. Do not persist or return the email on the annotations read path. Build the read DTO with an explicit field allow-list, do not return the raw stored item. |
| R4-6 | Idempotency, retried POST double-write | P1 | The proxy retries a 503 once for the non-idempotent POST. The body is buffered and replayed, and the client supplies no request id. A 503 emitted after a partial backend write produces a duplicate annotation. | Duplicate community annotations, inflated counts, ambiguous provenance. | Add a client-supplied idempotency key (request id or dedup key) to the wire contract and enforce a conditional put on it. Absent a client id, derive a deterministic dedup key from `(reviewer_id, deployment_id, target, behavior, created-at-bucket)` and reject the second write with the first record. |
| R4-7 | Stored injection in free-text fields | P1 | `notes`, `behavior`, `state`, `dataset`, and any body-trusted id are free text. Stored content such as `<script>` or control characters is returned on read and rendered in the studio, or written into logs and query expressions. | Stored XSS if any read path renders raw HTML or exports outside React escaping; log forging; malformed records. | Cap every string field (mirror community.py, notes max 2000, short fields max 120 to 200). Allow-list enums for `source`, `method`, `target.kind`, and `behavior` against `fixture.behavior_taxonomy`. Strip control characters on write. Sanitize on render and never use raw HTML injection for notes. Use parameterized DynamoDB put and key conditions, never string-built expressions. |
| R4-8 | Resource abuse and DoS on the write and list | P1 | `notes` and `h5_refs[]` have no size cap in the wire schema, the list has no pagination, and `explorePathLimit` does not cover annotations, so only the coarse global 60-per-minute per-IP limit applies to an authenticated writer. | Oversized bodies, unbounded table growth, and unbounded list responses degrade the service. | Enforce a request body-size cap, cap `notes` length and `h5_refs` count, paginate the list with a bounded page size and a `deployment_id` filter, and add a dedicated lower write rate limit keyed on `reviewer_id` rather than IP. |
| R4-9 | Agent-key exposure grants a fixed write identity | P2 | `agentUserFromRequest` accepts `x-orcast-agent-key` and maps it to a fixed identity `agent_orcast_automation`. A leaked `ORCAST_AGENT_KEY` lets an attacker write annotations as the automation identity through the public proxy. | Unauthorized writes attributed to the automation account. | Keep the agent key server-side only and out of any browser bundle. Scope or rotate it. Distinguish agent-authored annotations in provenance so automation writes are auditable and separable from human community writes. |
| R4-10 | NoSQL and expression injection on query and conditional put | P2 | If the list query or an idempotent conditional put builds DynamoDB FilterExpression or KeyConditionExpression by string concatenation from `deployment_id` or other input. | Query manipulation or condition bypass. | Use the SDK expression-attribute-value binding for all conditions and key queries. Never interpolate user input into expression strings. |
| R4-11 | Log injection through newline-bearing fields | P3 | Free-text fields containing newlines or ANSI sequences are written verbatim to structured or plaintext logs. | Forged or split log lines, harder forensics. | Strip or escape control characters before logging, and log identity from the validated reviewer id rather than from body fields. |
| R4-12 | Unauthenticated POST must 401 end to end | P3 | Confirmation item rather than an open attack. The proxy already 401s a non-allow-listed POST without a session or agent key. | None if preserved. The risk is a future allow-list mistake. | Do NOT add `api/dtag/annotations` to the public POST allow-list. Confirm the backend also 401s a direct call lacking the key, so the not-public posture holds at both layers. |

## Must fix before ship (P0 and P1)

- R4-1 P0. The annotations route depends on `require_api_key` AND `require_trusted_reviewer`,
  and the backend ingress is not directly writable without the key. The `vercel` marker is
  not authentication.
- R4-2 P0. Derive `annotator_id` and `annotator_role` from the verified reviewer headers,
  pin `source` server-side, ignore body-supplied identity.
- R4-3 P1. Pin `dataset`, `license_status`, and `tool` from the deployment record, validate
  or drop `h5_refs`.
- R4-4 P1. Reject unknown `deployment_id`, stamp `simulated` from the deployment record.
- R4-5 P1. Store the opaque reviewer id, never return the reviewer email on the read path,
  build the read DTO with an explicit field allow-list.
- R4-6 P1. Add an idempotency or dedup key so the proxy retry cannot double-write.
- R4-7 P1. Field length caps, enum allow-lists, control-char stripping, safe render,
  parameterized storage.
- R4-8 P1. Body-size cap, list pagination, and a write rate limit keyed on reviewer id.

## Single highest risk

R4-1, the direct-backend header-spoof auth bypass. The trust chain rests on one secret, the
shared `X-ORCAST-Key`. The `X-ORCAST-Trusted-Proxy: vercel` marker and the
`X-ORCAST-Reviewer-*` headers carry no secret and are fully attacker-controllable. If the new
annotations route omits `require_api_key`, or if the App Runner backend is reachable directly
on the internet, an attacker forges the reviewer headers and writes as any identity, defeating
both the not-public posture and the provenance contract in one request. The route must reuse
the community approve/reject pattern of `require_api_key` plus `require_trusted_reviewer`, and
the backend ingress must not accept direct unauthenticated writes.

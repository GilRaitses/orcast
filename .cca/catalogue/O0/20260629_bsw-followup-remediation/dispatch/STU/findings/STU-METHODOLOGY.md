# STU-Q methodology (studio-live-persistence)

Records the O0-ruled endpoint design for the DTAG annotation write path. This
file is the build contract for STU-B and STU-INT. It conforms to the existing
client wire schema documented in `STU-contract.md` and follows the backend
patterns documented in `STU-backend-surface.md`.

`repo_state_verified_against`: 61ba1d69ee36cf605f7ba741bdaa1defa8762834

## Locked gate decisions (O0)

1. Storage backing is Option A. A tenth DynamoDB table `orcast-dtag-annotations`,
   composite key `pk=deployment_id` and `sk=annotation#{...}`, behind a new
   `ORCAST_DTAG_ANNOTATIONS_TABLE` setting. Default `storage_backend=memory` so
   STU-B and its tests stay fully offline and deterministic. Real table
   provisioning and the env set are deferred to the deploy gate at STU-ACCEPT.
   Nothing is provisioned now.
2. Read auth posture is authenticated. No public read is added. `api/dtag/annotations`
   stays authenticated-by-default through the proxy. The optional documentation
   only `PROTECTED_PATHS` line is allowed and changes nothing at runtime.
3. Idempotency is server-side content-key dedup. The dedup key is a hash of
   reviewer_id, deployment_id, target.start_sample, target.end_sample, and
   behavior, enforced with a conditional put. The server generates the
   authoritative `uuid4` id.

## Route shape

Three routes in a net-new `src/aws_backend/routers/annotations.py`. The
read-only `dtag.py` surface is not edited; the new router reuses its deployment
loader read-only to validate the target deployment.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/dtag/annotations` | `require_api_key` (router) plus `require_trusted_reviewer` | create one annotation |
| GET | `/api/dtag/annotations?deployment_id=...` | `require_api_key` (router) plus `require_signed_in` | list a deployment's annotations |
| GET | `/api/dtag/annotations/{id}` | `require_api_key` (router) plus `require_signed_in` | read one annotation |

The router declares `APIRouter(dependencies=[Depends(require_api_key)])`, the
same pattern `journal.py` uses to close the direct-backend bypass. A direct
caller without the server `X-ORCAST-Key` gets 401 before any reviewer logic runs.

## Request and response schema

The POST request body is the client `AnnotationSubmissionRequest` exactly as
`toSubmissionRequest` emits it. The server parses it, then ignores every
identity, authority, and license field in the request and re-derives those
server-side. See the security section.

POST response is `{ "id": "<uuid4 hex>", "status": "created" | "duplicate", "simulated": <bool> }`.
The client reads only `id`. `status` is `duplicate` when content-key dedup
returned an existing record. `simulated` is honest reporting and the client
ignores it.

GET list returns a bare JSON array of full `Annotation` objects, no envelope,
matching the client `Annotation[]` parse. GET by id returns one full `Annotation`;
a missing id returns 404, which the client maps to null.

The full `Annotation` returned on read carries the 10-field provenance. The
server reshapes the 8-field POST provenance into the 10-field read provenance by
moving `deployment_id` into the provenance block and adding a server-assigned
`created_at`. This is the asymmetry STU-R1 flagged.

## Storage

A dedicated store module `src/aws_backend/annotations/store.py` follows the
three-class pattern of `journal/store.py`: an abstract `AnnotationStore`, a
`MemoryAnnotationStore`, an `AwsAnnotationStore`, and a `build_annotation_store`
factory that returns the AWS impl only when `storage_backend=aws`. The default
memory backend backs the store with plain dicts so STU-B tests run offline with
no boto3.

The AWS impl keys items `pk=deployment_id`, `sk=annotation#{dedup_key}`, stores
the `uuid4` id as an attribute, and writes with
`ConditionExpression="attribute_not_exists(sk)"`. On a conditional-check failure
it re-reads the existing item and returns it, so a proxy retry returns the first
writer's id instead of creating a duplicate. List is a `query` on the partition;
get by id is a small `scan` filtered on the id attribute, with a GSI noted as the
scale path. The AWS impl is exercised in STU-B only by a mocked unit test that
asserts the conditional expression. It is wired live at STU-ACCEPT.

## Idempotency

`dedup_key = sha256(reviewer_id|deployment_id|start_sample|end_sample|behavior)[:32]`.
The reviewer id is the verified identity, not a client value, so two users
labeling the same window are distinct, and one user replaying the same content
through a proxy 503 retry collapses to one record.

## Security mitigations built in STU-B from the start

Both P0 fixes ship in STU-B, not deferred to STU-ADV.

- P0 auth bypass. The route depends on `require_api_key` at the router level and
  `require_trusted_reviewer` per write. The backend trusts reviewer identity only
  when the request carries the server key, so a forged `X-ORCAST-Reviewer-Id` on a
  direct, keyless request is rejected.
- P0 provenance identity tamper. `annotator_id`, `annotator_role`, and `source`
  are stamped from the verified reviewer identity. `annotator_id` is the opaque
  WorkOS reviewer id, never the email. `source` is derived from the reviewer role
  (see the honesty rulings below). The request body's identity fields are ignored.

P1 mitigations also in STU-B.

- `dataset` is pinned to the deployment id. `license_status` is pinned from the
  deployment record (`simulated-example` for the simulated bundled deployment).
  `tool` is pinned to the server constant. `h5_refs` are pinned to the server dive
  reference set for a dive target and empty otherwise, so the client cannot inject
  through them.
- Unknown `deployment_id` is rejected with 404. The deployment is looked up with
  the read-only dtag loader.
- `simulated` is copied from the deployment record onto the stored record and
  every response, so an annotation against `cascadia_2010_k33_test` stays labeled
  simulated end-to-end.
- Reads return an explicit field allow-list. The reviewer email is never stored
  and never returned.
- Injection caps and enum allow-lists. `target.kind` is one of `dive` or
  `time_range`. `method` is one of `manual` or `derived`. `behavior` and `state`
  match a lowercase slug pattern with a length cap. `notes` is capped at 2000
  characters. Request provenance string fields are length-capped so the parsed
  body is bounded.
- Body-size and list bounds. Field length caps bound the request body. The list
  route is capped with a `limit` query parameter, default 100, max 500.
- Write rate limit keyed on reviewer id. An in-process token bucket caps writes
  per reviewer per minute and returns 429 on exceed.

## Honesty rulings (O0, applied)

1. `source` is derived server-side from the verified `ReviewerIdentity`. The
   default is `community`. It maps to `expert` only when the verified identity
   carries a recognized expert or researcher role tier. It is never read from the
   request body and never set to `model` for a human annotation. The
   `ReviewerIdentity` does carry a `reviewer_role` field, but the trusted proxy
   currently stamps only the constant role `reviewer`, so in practice `source`
   pins to `community` today. The recognized-role set in `annotations.py`
   (`_EXPERT_ROLES`) is the expert-mapping hook for when a real role tier lands.
   Implemented in `_derive_source` in `src/aws_backend/routers/annotations.py`.
2. `license_status` is `simulated-example` for the simulated bundled deployment,
   confirmed. A code comment in `annotations.py` records that real
   partnership-gated deployments must carry their actual data-sharing-agreement
   license string when they land. That is future and out of scope now.

## Deploy and provisioning gate named for STU-ACCEPT

`ORCAST_API_BASE` does not change. The human deploy gate is the App Runner
deploy of the additive route on `orcast-aws-backend`, plus provisioning the
`orcast-dtag-annotations` DynamoDB table with key schema `pk` string and `sk`
string, plus setting `ORCAST_DTAG_ANNOTATIONS_TABLE` and `ORCAST_STORAGE_BACKEND=aws`
in the backend environment. STU-ACCEPT runs the live create then list then get
using the agent-key path, header `X-ORCAST-Agent-Key`.

## Rejected alternatives

- Reusing `community_table`. Its submission schema and moderation lifecycle do
  not match reviewer-authored telemetry labels.
- The `dtag_cache` file path. It is a memoized read cache, not a concurrency-safe
  write store.
- A client-supplied idempotency token. The client wire schema is locked and sends
  none, so dedup is derived server-side from content plus reviewer identity.
- Trusting any provenance identity, source, or license field from the request
  body. All are server-derived to prevent impersonation and mislabeling.

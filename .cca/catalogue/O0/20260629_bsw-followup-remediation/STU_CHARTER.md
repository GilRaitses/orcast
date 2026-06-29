# STU — studio-live-persistence (waveset charter)

- Lane code: `STU`  Family: `BSWR`  Owner: dispatched sub-orchestrator (answers to O0)
- Type: execution (backend FastAPI route + web proxy allow-list)
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/` ; dispatch `dispatch/STU/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
- Umbrella: `PROGRAM.md`

## Intent

Make the annotation studio's live persistence path real. The client store already
posts annotations to a backend endpoint that does not exist; build the backend
endpoint, allow-list it through the same-origin proxy, and wire the deploy env so
a community annotation round-trips create -> persist -> read back honestly.

## Grounding (real seams + verified root cause)

- `web/lib/annotation/store.ts`: `HttpAnnotationStore` POSTs to
  `/api/be/api/dtag/annotations` and GETs list / `{id}`. `web/lib/annotation/serialize.ts`
  defines `toSubmissionRequest` (the wire schema) and `AnnotationSubmissionResponse`.
  `web/lib/annotation/factory.ts` selects http vs in-memory; the live console uses http.
- `web/lib/annotation/provenance.ts`: every annotation carries provenance
  (deployment_id, annotator, timestamps) and is validated before persist.
- `src/aws_backend/routers/dtag.py`: the dtag router is READ-ONLY
  (`/api/dtag/deployments`, `/dives`, `/feeding`). There is NO annotations
  endpoint, GET or POST. DTAG data is partnership-gated; the only deployment is
  the SIMULATED bundled example.
- `web/app/api/be/[...path]/route.ts`: the proxy. `isPublicRequest` allow-lists a
  small set of GET paths and a few specific POSTs. `api/dtag/annotations` is not
  allow-listed, so a POST there already requires an authenticated WorkOS user (or
  an agent token). `API_BASE = process.env.ORCAST_API_BASE` is the deploy env.

Root cause: the client write path was built to a contract (`BSS-INTEGRATE` left
the backend route allow-listing "finalized at ACCEPT"), but the backend endpoint,
the proxy allow-list decision, and the deploy env were never landed.

## Locked decisions (do NOT reopen)

1. Annotations are community-authored and provenance-tagged. The write path is
   NOT public. It requires an authenticated WorkOS user or an agent token, the
   same authorization model the proxy already enforces for non-allow-listed
   POSTs. Do NOT add `api/dtag/annotations` to the public POST allow-list.
2. DTAG deployments stay partnership-gated and SIMULATED until an agreement
   lands. Annotating the simulated example is fine and must stay labeled
   simulated end-to-end; this lane does not unlock real deployments.
3. The wire schema is the existing `toSubmissionRequest` / `AnnotationSubmissionResponse`.
   The backend conforms to the client contract; the client is not rewritten to
   fit the backend.
4. No PII beyond the existing provenance fields. The adversarial wave audits for
   injection, PII leakage, auth bypass, and provenance tampering.
5. Storage backing is an O0 decision in `STU-Q` (a DynamoDB table consistent with
   the existing nine-table model, or the cache path). No new datastore is stood
   up without an O0 gate.
6. `web/app/api/be/[...path]/route.ts` is a convergence file. The allow-list edit
   is a single serialized editor in `STU-INT`, serialized across R-Alpha / A1.

## Wave structure

- `STU-R` (research + discovery, read-only). Parallel; each owns one `dispatch/STU/findings/STU-<TOPIC>.md`:
  - R1 contract: the exact wire schema (`toSubmissionRequest`, response, list/get shapes) the backend must serve.
  - R2 backend surface: the dtag router + config + the existing nine-table DynamoDB model; where annotations should live; how other write routes authenticate.
  - R3 proxy + env: the `isPublicRequest` model, the agent-token path, and the `ORCAST_API_BASE` deploy wiring.
  - R4 adversarial: injection, PII, auth bypass, idempotency / double-submit, provenance tampering.
- `STU-Q` (qualify methodology). GATED. Fixes the endpoint design (route, schema, auth tier, storage backing, idempotency); names the deploy/env change for O0. Returns to O0.
- `STU-B` (implement). Net-new backend annotations router + tests, conforming to the client contract; `src/aws_backend/routers/**` + `tests/aws_backend/**`. No proxy edit yet.
- `STU-INT` (integrate). GATED. Single editor adds the annotations path to the proxy authorization model (authenticated, not public) in `route.ts`; confirms `factory.ts` http wiring. `git pull --rebase` first; serialize across R-Alpha / A1.
- `STU-ADV` (adversarial review). Runs the security audit against the wired path; loops back to `STU-B`/`STU-INT` until zero open P0/P1.
- `STU-ACCEPT` (accept). GATED. Live round-trip create -> list -> get against the deployed backend; verdict cites real responses. Deploy/env config (`ORCAST_API_BASE`) is a human gate.

## Acceptance criteria (hard, checkable)

- A backend `POST /api/dtag/annotations` + `GET /api/dtag/annotations` (list, filterable by deployment_id) + `GET /api/dtag/annotations/{id}` exist, conforming to the client wire schema, with tests.
- The endpoint rejects unauthenticated writes; the proxy requires a session/agent token for the annotations POST.
- A live create -> list -> get round-trip succeeds against the deployed backend and the annotation stays labeled simulated for the simulated deployment.
- The adversarial wave reports zero open P0/P1 (injection, PII, auth bypass, provenance tamper, double-submit).
- No public POST allow-list entry was added for annotations.

## Escalation

Per PROGRAM.md. Pause and return to O0 on the storage-backing decision, the
deploy/env change, the convergence edit slot, or commit.

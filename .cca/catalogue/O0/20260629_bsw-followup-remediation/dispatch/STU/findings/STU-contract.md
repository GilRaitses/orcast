# STU-R1 client wire contract

This documents the exact HTTP wire schema the backend must serve so the existing
client annotation store works with no client change. The client is fixed. The
backend conforms to it. Source files are `web/lib/annotation/store.ts`,
`web/lib/annotation/serialize.ts`, `web/lib/annotation/types.ts`,
`web/lib/annotation/provenance.ts`, and `web/lib/annotation/factory.ts`.

## Endpoint base and routing

The HTTP store base path is `/api/be/api/dtag/annotations`. The same-origin proxy
`web/app/api/be/[...path]/route.ts` strips the `/api/be` prefix and forwards to the
backend path `api/dtag/annotations`. The proxy copies query params onto the
forwarded request. The proxy defaults the request `Content-Type` to
`application/json`. The annotations path is not in the public allow-list, so any
request that is not a public GET requires an authenticated session or an agent
user. The POST in particular requires auth through the proxy. That is a wiring
detail for the backend lane and does not change the body or response schemas
below.

The three calls the client makes, from `HttpAnnotationStore`.

| Operation | Method | Path the backend sees | Query |
|-----------|--------|------------------------|-------|
| create | POST | `api/dtag/annotations` | none |
| list | GET | `api/dtag/annotations` | `deployment_id` |
| get | GET | `api/dtag/annotations/{id}` | none |

## 1. POST request body

The client builds the body with `toSubmissionRequest(staged)` and sends
`JSON.stringify` of it. The type is `AnnotationSubmissionRequest`. Optional fields
that are `undefined` are dropped by `JSON.stringify`, so the backend must treat
them as absent rather than null.

```json
{
  "deployment_id": "mn09_203a",
  "target": {
    "kind": "dive",
    "dive_id": 12,
    "start_sample": 100000,
    "end_sample": 250000
  },
  "behavior": "foraging_dive",
  "state": "Feeding",
  "confidence": 0.8,
  "notes": "optional free text",
  "provenance": {
    "source": "expert",
    "annotator_id": "reviewer:demo",
    "annotator_role": "expert",
    "method": "manual",
    "dataset": "mn09_203a",
    "h5_refs": ["depth/values", "dives/dive_indices", "analysis/animal_frame_metrics/odba"],
    "license_status": "CC-BY-NC",
    "tool": "bss-annotation-studio-v1"
  }
}
```

Field by field.

| Field | Type | Required | Client source |
|-------|------|----------|---------------|
| `deployment_id` | string | required | `a.provenance.deployment_id`, lifted to top level |
| `target` | object | required | `a.target`, sent as nested object |
| `target.kind` | `"dive"` or `"time_range"` | required | draft target |
| `target.dive_id` | number | optional | present for dive targets |
| `target.start_sample` | number | required | draft target |
| `target.end_sample` | number | required | draft target |
| `behavior` | string | required | `a.behavior` |
| `state` | string | optional | `a.state`, absent if undefined |
| `confidence` | number | optional | `a.confidence`, absent if undefined |
| `notes` | string | optional | `a.notes`, absent if undefined |
| `provenance` | object | required | nested, exactly 8 fields below |
| `provenance.source` | string | required | `a.provenance.source` |
| `provenance.annotator_id` | string | required | `a.provenance.annotator_id` |
| `provenance.annotator_role` | string | required | `a.provenance.annotator_role` |
| `provenance.method` | string | required | `a.provenance.method` |
| `provenance.dataset` | string | required | `a.provenance.dataset` |
| `provenance.h5_refs` | string array | required | `a.provenance.h5_refs` |
| `provenance.license_status` | string | required | `a.provenance.license_status` |
| `provenance.tool` | string | required | `a.provenance.tool` |

The wire `provenance` block has exactly these 8 fields. The full client
`AnnotationProvenance` type has 10 fields. The two missing from the POST
`provenance` block are `deployment_id` and `created_at`. `deployment_id` is not
absent from the request, it travels at the top level of the body. `created_at` is
not sent at all on POST. The server assigns it.

## 2. POST response body

The client parses the response as `AnnotationSubmissionResponse`.

```json
{ "id": "ann_8f21c0", "status": "accepted" }
```

| Field | Type | Required | Client use |
|-------|------|----------|------------|
| `id` | string | required | read and merged into the local record |
| `status` | string | present in type | parsed into the type, then discarded |

The store does `return { ...staged, id: body.id }`. It reads only `body.id`. It
does not read `status` and does not re-read any other persisted field from the
POST response. The implication is the server-assigned `id` is authoritative and
replaces the client placeholder `"pending"`. Every other field of the persisted
record never comes back on POST, so it must round-trip correctly on the later GET
calls. The server must persist exactly what the client sent plus the fields it
derives, because the GET responses are the only place the full record is read
back.

The client throws when the POST is not ok. A non-2xx status raises
`annotation_persist_failed:{status}`. The success path requires `res.ok` true and
a JSON body with a string `id`.

## 3. GET list response body

Call: `GET api/dtag/annotations?deployment_id={id}`. The client parses the
response as `Annotation[]` directly. It is a bare JSON array of full `Annotation`
objects. It is not the submission-request shape. It is not wrapped in an envelope
such as `{ items: [...] }` or `{ data: [...] }`. The deployment filter is the
`deployment_id` query param, matched in the in-memory reference store against
`a.provenance.deployment_id`.

Each array item is a full `Annotation`.

```json
[
  {
    "id": "ann_8f21c0",
    "target": {
      "kind": "dive",
      "dive_id": 12,
      "start_sample": 100000,
      "end_sample": 250000
    },
    "behavior": "foraging_dive",
    "state": "Feeding",
    "confidence": 0.8,
    "notes": "optional free text",
    "provenance": {
      "dataset": "mn09_203a",
      "deployment_id": "mn09_203a",
      "source": "expert",
      "annotator_id": "reviewer:demo",
      "annotator_role": "expert",
      "method": "manual",
      "h5_refs": ["depth/values", "dives/dive_indices", "analysis/animal_frame_metrics/odba"],
      "license_status": "CC-BY-NC",
      "tool": "bss-annotation-studio-v1",
      "created_at": "2026-06-29T12:00:00.000Z"
    }
  }
]
```

Per-item full `Annotation` shape.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | required | server-assigned, matches POST response id |
| `target` | object | required | same shape as POST target |
| `behavior` | string | required | |
| `state` | string | optional | may be absent |
| `confidence` | number | optional | may be absent |
| `notes` | string | optional | may be absent |
| `provenance` | object | required | full 10-field block below |
| `provenance.dataset` | string | required | |
| `provenance.deployment_id` | string | required | inside provenance here, not top level |
| `provenance.source` | `"expert"`, `"community"`, or `"model"` | required | client union type |
| `provenance.annotator_id` | string | required | |
| `provenance.annotator_role` | string | required | |
| `provenance.method` | `"manual"` or `"derived"` | required | client union type |
| `provenance.h5_refs` | string array | required | |
| `provenance.license_status` | string | required | |
| `provenance.tool` | string | required | |
| `provenance.created_at` | string | required | ISO 8601 timestamp |

The asymmetry to flag. The POST sends the submission-request shape, where
`provenance` carries 8 fields and `deployment_id` rides at the top level. The GET
list and get must return the full `Annotation` shape, where `provenance` carries
10 fields including `deployment_id` and `created_at` inside the provenance block.
The backend cannot echo the POST body verbatim on GET. It must reshape it.

The client throws when the list GET is not ok. A non-2xx status raises
`annotation_list_failed:{status}`.

## 4. GET by id response body

Call: `GET api/dtag/annotations/{id}`. The id is URL-encoded by the client. The
response is a single full `Annotation`, the same per-item shape as the list above,
not an array and not an envelope.

Status-code expectations the client enforces.

| Server status | Client behavior |
|---------------|-----------------|
| 404 | returns `null`, no throw |
| any non-ok that is not 404 | throws `annotation_get_failed:{status}` |
| ok | parses body as a single `Annotation` |

A missing annotation must be a 404 so the client maps it to `null`. Returning
`200` with an empty body, or a non-404 error for a missing id, breaks the
client contract.

## 5. Reconciliation note

The backend receives 9 of the 10 final provenance fields on POST. Eight arrive
inside the request `provenance` block. The ninth, `deployment_id`, arrives at the
top level of the request body. The tenth, `created_at`, never arrives on POST.

To make GET responses satisfy the client `Annotation` type and the
`validateProvenance` rules, the server must do all of the following at persist
time and on read-back.

1. Assign `id`. Return it in the POST response as `body.id` and use the same id in
   every GET response for that record.
2. Assign `created_at` as an ISO 8601 timestamp string at persist time. The client
   never sends it. Store it and echo it in the GET provenance block. The client
   builds this with `new Date().toISOString()` for local records, so an ISO 8601
   string is the expected format.
3. Move `deployment_id` from the top level of the POST body into
   `provenance.deployment_id` in every GET response. Keep it usable as the list
   filter key for `?deployment_id=`.
4. Echo the 8 POSTed provenance fields unchanged into the GET provenance block.
5. Echo `target`, `behavior`, and the optional `state`, `confidence`, `notes`
   unchanged. Absent optional fields stay absent.

After step 3 and step 4 the GET provenance block has all 10 fields:
`dataset`, `deployment_id`, `source`, `annotator_id`, `annotator_role`, `method`,
`h5_refs`, `license_status`, `tool`, `created_at`. The reference in-memory store
confirms this round-trip is byte-stable through `provenanceIntact`, which compares
`JSON.stringify(a.provenance)` against the read-back. The backend does not need to
match key order, since the client does not compare GET responses with
`provenanceIntact`. The client compares only its own local create against its own
read-back. The backend does need every field present and equal in value.

## 6. Validation rules the client already enforces locally

These run in `assembleAnnotation` in `store.ts` and `validateProvenance` in
`provenance.ts` before the POST is sent. The backend should enforce the same rules
so it conforms and so a record it accepts would also pass the client assembler.

| Rule | Source | Enforcement |
|------|--------|-------------|
| `end_sample` must be greater than or equal to `start_sample` | `assembleAnnotation` | reject when `target.end_sample < target.start_sample` |
| `behavior` must be present and non-empty | `assembleAnnotation` | reject empty `behavior` |
| `annotator_id` required | `validateProvenance` | reject empty |
| `annotator_role` required | `validateProvenance` | reject empty |
| `dataset` required | `validateProvenance` | reject empty |
| `deployment_id` required | `validateProvenance` | reject empty, this is the top-level field on POST |
| `license_status` required | `validateProvenance` | reject empty |
| `created_at` required | `validateProvenance` | server-assigned, must be non-empty in the stored record |

The client runs `validateProvenance` against the full 10-field provenance it built
locally, including `created_at`, before it ever calls the HTTP store. The backend
sees only 8 provenance fields plus top-level `deployment_id`, so the backend
equivalent of `validateProvenance` checks the 8 it receives plus top-level
`deployment_id`, then assigns and validates its own `created_at`. The backend
should reject a POST that fails any of these, since the client would never have
produced such a record.

# STU-ACCEPT plan (studio-live-persistence)

Staged live round-trip for the DTAG annotation write path. This is one step from
running. It is NOT run here. It needs the deploy gate cleared first.

`repo_state_verified_against`: 61ba1d69ee36cf605f7ba741bdaa1defa8762834

## Prerequisites (the deploy gate, human)

1. App Runner deploy of the additive route on `orcast-aws-backend` so
   `/api/dtag/annotations` is live.
2. Provision the `orcast-dtag-annotations` DynamoDB table, key schema `pk`
   (string, partition) and `sk` (string, sort).
3. Set `ORCAST_DTAG_ANNOTATIONS_TABLE=orcast-dtag-annotations` and
   `ORCAST_STORAGE_BACKEND=aws` in the backend environment.
4. The Vercel proxy already has `ORCAST_API_BASE`, `ORCAST_API_KEY`, and
   `ORCAST_AGENT_KEY` set. `ORCAST_API_BASE` does not change.

## Auth path

The round-trip goes through the same-origin proxy using the agent token, so no
browser WorkOS session is needed. The client sends header `X-ORCAST-Agent-Key`
equal to `ORCAST_AGENT_KEY`. The proxy matches the agent identity, then injects
`X-ORCAST-Trusted-Proxy: vercel`, `X-ORCAST-Key`, and the reviewer headers
(`X-ORCAST-Reviewer-Id` is the agent id `agent_orcast_automation`, role
`reviewer`). The backend accepts the write under `require_api_key` plus
`require_trusted_reviewer`. Because the agent role is `reviewer`, the derived
`source` is `community`.

## Environment for the run

```
export PROXY_BASE="https://<deployed-vercel-app>"   # the same-origin proxy host
export AGENT_KEY="<value of ORCAST_AGENT_KEY>"        # from the gitignored secret, never written to a tracked file
export DEP="cascadia_2010_k33_test"                   # the simulated bundled deployment
```

## Step 1: create

```
curl -sS -X POST "$PROXY_BASE/api/be/api/dtag/annotations" \
  -H "Content-Type: application/json" \
  -H "X-ORCAST-Agent-Key: $AGENT_KEY" \
  -d '{
    "deployment_id": "cascadia_2010_k33_test",
    "target": { "kind": "dive", "dive_id": 1, "start_sample": 0, "end_sample": 100 },
    "behavior": "foraging_dive",
    "state": "active",
    "confidence": 0.8,
    "notes": "STU-ACCEPT live round-trip",
    "provenance": {
      "source": "community",
      "annotator_id": "ignored-by-server",
      "annotator_role": "ignored-by-server",
      "method": "manual",
      "dataset": "ignored-by-server",
      "h5_refs": ["depth/values"],
      "license_status": "ignored-by-server",
      "tool": "ignored-by-server"
    }
  }'
```

Expected: HTTP 200 and a body shaped like

```
{ "id": "<uuid4 hex>", "status": "created", "simulated": true }
```

Capture `ID` from the response `id`.

## Step 2: list (filter by deployment_id)

```
curl -sS "$PROXY_BASE/api/be/api/dtag/annotations?deployment_id=$DEP" \
  -H "X-ORCAST-Agent-Key: $AGENT_KEY"
```

Expected: HTTP 200 and a bare JSON array (no envelope). The array contains an
object with `id == ID`, and that object is the full `Annotation`:

```
{
  "id": "<ID>",
  "target": { "kind": "dive", "dive_id": 1, "start_sample": 0, "end_sample": 100 },
  "behavior": "foraging_dive",
  "state": "active",
  "confidence": 0.8,
  "notes": "STU-ACCEPT live round-trip",
  "provenance": {
    "dataset": "cascadia_2010_k33_test",
    "deployment_id": "cascadia_2010_k33_test",
    "source": "community",
    "annotator_id": "agent_orcast_automation",
    "annotator_role": "reviewer",
    "method": "manual",
    "h5_refs": ["depth/values", "dives/dive_indices", "analysis/animal_frame_metrics/odba"],
    "license_status": "simulated-example",
    "tool": "bss-annotation-studio-v1",
    "created_at": "<ISO-8601>"
  },
  "simulated": true
}
```

## Step 3: get by id

```
curl -sS "$PROXY_BASE/api/be/api/dtag/annotations/$ID" \
  -H "X-ORCAST-Agent-Key: $AGENT_KEY"
```

Expected: HTTP 200 and the single full `Annotation` above. A missing id returns
HTTP 404.

## Step 4: idempotency confirmation

Repeat Step 1 with the identical body. Expected: HTTP 200 with the same `id` and
`"status": "duplicate"`. A second list (Step 2) still returns exactly one item
for that content, proving the content-key dedup holds across a real round-trip.

## End-to-end simulated-label assertion (the pass criterion)

The deployment is the simulated bundled example, so every response for it must
stay labeled simulated. The verdict passes only if all of the following hold on
the captured live responses:

- the create response has `"simulated": true`.
- every list item and the get response have `"simulated": true`.
- `provenance.license_status == "simulated-example"`.
- `provenance.dataset == "cascadia_2010_k33_test"` and
  `provenance.deployment_id == "cascadia_2010_k33_test"`.
- `provenance.source == "community"` and
  `provenance.annotator_id == "agent_orcast_automation"`, and no reviewer email
  appears anywhere in the responses.

## Negative check (auth, optional but recommended)

```
curl -sS -o /dev/null -w "%{http_code}\n" -X POST \
  "$PROXY_BASE/api/be/api/dtag/annotations" \
  -H "Content-Type: application/json" -d '{}'
```

Expected: HTTP 401. A POST without the agent token and without a WorkOS session
must be rejected, confirming the write path is not public.

## Evidence capture

Save the four captured response bodies and the HTTP status lines under
`dispatch/STU/gate_captures/` as a metrics JSON plus a log, then write
`dispatch/STU/findings/STU-ACCEPT_VERDICT.md` citing the real `id`, the real
`created_at`, and the simulated-label assertion results. Do not run until O0
confirms the deploy gate is cleared. No commit without an explicit operator
request.

# WS2 benchmark plan — O0-executed runbook

This is the runbook O0 (the operator-facing thread) executes. The WS-STREAM
sub-orchestrator authored the probe artifacts in `ws2_probes/` but DEPLOYS
NOTHING and CONTACTS PROD NOTHING. O0 runs the four steps below, captures the
numbers, and relays the JSON results back for the WS2 gate verdict.

Operator has approved throwaway prod probes (Vercel preview + the cloudflared
backend `orcast-api.aimez.ai`) and confirmed the goal: first token <= 1500 ms,
measured on the full prod chain.

## Design: A/B localization

The four steps add one chain layer at a time so a buffering failure localizes to
exactly one layer. The prod chain is
`Browser -> Vercel -> Next /api/be -> cloudflared -> uvicorn`.

| Step | Path measured | Adds which layer | Isolates |
|------|---------------|------------------|----------|
| 1 | `curl` direct to uvicorn on localhost | uvicorn only | the probe + headers are correct at the origin |
| 2 | `curl`/browser to `orcast-api.aimez.ai/__stream_probe` | + cloudflared + Cloudflare edge | whether the edge/tunnel buffers SSE |
| 3 | dedicated Next route on a Vercel preview | + Vercel + Next route handler | whether Vercel buffers a `resp.body` passthrough |
| 4 | `/api/be` passthrough variant | the production convergence path | the real route once the `resp.text()` fix lands |

If Step N passes and Step N+1 fails, the layer added in N+1 is the culprit.

## Probe parameters (held constant across steps)

- 20 token frames, 150 ms interval. Expected server emit window ~3.0 s; meta is
  immediate, so a healthy first-token latency is well under 1500 ms.
- Framing is `event: meta` then 20x `event: token` then `event: done`, the same
  framing T4 narration will use.
- Anti-buffer headers asserted at the origin and re-asserted at the Next layer:
  `text/event-stream`, `Cache-Control: no-cache, no-transform`,
  `X-Accel-Buffering: no`, `Connection: keep-alive`, no `Content-Length`.

---

## Step 0 — stand up the uvicorn probe (one time)

On the cloudflared backend host (the aimez-services host serving
`orcast-api.aimez.ai`), in a scratch dir holding a copy of `stream_probe_app.py`:

```bash
python3 -m venv .ws2venv && . .ws2venv/bin/activate
pip install fastapi "uvicorn[standard]"
uvicorn stream_probe_app:app --host 127.0.0.1 --port 8099
```

Use a port that does NOT collide with prod uvicorn on 8090. Keep this probe
process separate from `orcast-api.service`.

PREREQUISITE TO CONFIRM (see "Open prerequisites" below): the cloudflared
ingress must route a hostname/path to `127.0.0.1:8099`, or O0 must temporarily
point an existing test route at it. Do not disturb the live `:8090` ingress.

---

## Step 1 — direct uvicorn (isolate the origin)

On the backend host:

```bash
# quick eyeball + headers
./measure_stream.sh http://127.0.0.1:8099/__stream_probe

# machine-readable
node measure_stream.mjs http://127.0.0.1:8099/__stream_probe \
  --label direct-uvicorn --out result_step1_uvicorn.json
```

Record: `first_token_ms`, `median_gap_ms`, `incremental`, the response headers.

- Expected: tokens ~150 ms apart, `incremental: true`, first token a few ms.
- If NOT incremental here, the probe/headers are wrong (fix before continuing).
  This step is the control; it should always pass.

---

## Step 2 — through cloudflared / Cloudflare edge (isolate the edge)

From the operator laptop (off the backend host, so traffic traverses the edge):

```bash
./measure_stream.sh https://orcast-api.aimez.ai/__stream_probe
# also try forcing HTTP/1.1 to rule out h2 framing effects:
curl -N --http1.1 https://orcast-api.aimez.ai/__stream_probe

node measure_stream.mjs https://orcast-api.aimez.ai/__stream_probe \
  --label cloudflared-edge --out result_step2_cloudflared.json
```

Record the same fields.

- PASS: `incremental: true`, first token <= 1500 ms. Edge/tunnel does not buffer.
- STOP/INVESTIGATE: if Step 1 was incremental but tokens now arrive in one burst
  (`median_gap_ms ~0`, `client_span_ms ~0`), the Cloudflare edge or cloudflared
  buffered. Remediation to try, in order: confirm origin `Content-Type:
  text/event-stream` + `no-transform`; add a zone Configuration Rule
  `response_body_buffering: none` scoped to `orcast-api.aimez.ai` +
  `/__stream_probe`; disable compression for SSE; update cloudflared. Re-measure.

---

## Step 3 — dedicated Next stream route on a Vercel preview (isolate Vercel)

This is shortlist method #1 (`dedicated_next_stream_route`).

1. On a THROWAWAY preview branch (never main), copy the candidate into place:
   ```bash
   mkdir -p web/app/api/__streamprobe
   cp ws2_probes/next_stream_route_candidate.ts web/app/api/__streamprobe/route.ts
   ```
2. Deploy a Vercel PREVIEW with `ORCAST_API_BASE=https://orcast-api.aimez.ai` set
   in the preview env. Capture the preview URL `<preview>.vercel.app`.
3. Measure:
   ```bash
   ./measure_stream.sh https://<preview>.vercel.app/api/__streamprobe
   node measure_stream.mjs https://<preview>.vercel.app/api/__streamprobe \
     --label vercel-dedicated-route --out result_step3_vercel.json
   ```

Record the same fields.

- PASS: `incremental: true`, first token <= 1500 ms through Vercel + Next + edge
  + uvicorn. This is the headline: the full prod chain streams.
- STOP/INVESTIGATE: if Step 2 was incremental but Step 3 bursts, Vercel/Next
  buffered. Check the route exports (`runtime="nodejs"`, `dynamic="force-dynamic"`,
  `maxDuration`), confirm `resp.body` passthrough (not `resp.text()`), confirm the
  outbound `X-Accel-Buffering: no` + `no-transform`. Re-measure.
- After measuring, DELETE the preview and the scratch route. Do not merge.

---

## Step 4 — `/api/be` passthrough variant (production convergence path)

This is shortlist method #3 (`sse_through_proxy_passthrough`): the real generic
proxy, once its line 176 `await resp.text()` is replaced by a `resp.body`
passthrough for streaming responses. Step 4 proves the production route, not just
a bespoke probe route.

OPTION A (cleanest, still throwaway): on the same preview branch, apply the
minimal streaming branch to `web/app/api/be/[...path]/route.ts` (detect
`Accept: text/event-stream` or an SSE upstream `Content-Type`, return
`new Response(resp.body, { headers })` instead of buffering) and add
`api/__stream_probe` to the public allow-list for the probe only. Point the
client at `/api/be/__stream_probe`.

```bash
node measure_stream.mjs "https://<preview>.vercel.app/api/be/__stream_probe" \
  --label apibe-passthrough --out result_step4_apibe.json
```

- PASS: `incremental: true`, first token <= 1500 ms through the real `/api/be`
  shape. This is the path WS4 will actually ship.
- STOP/INVESTIGATE: if the dedicated route (Step 3) streamed but `/api/be` does
  not, the generic proxy is doing something extra. Suspects: the inbound
  `Content-Type: application/json` override (route.ts:149-150), header stripping,
  or the buffered return at route.ts:176-180 not fully replaced. Compare against
  the Step-3 route and reconcile.
- This branch is throwaway. The real WS4 implementation is gated separately.

---

## PASS / STOP rubric (the WS2 gate)

PASS (gate cleared, proceed to WS3) requires, for at least ONE method through the
FULL prod chain (Step 3 and/or Step 4):

- `incremental: true` — tokens arrive spread apart (`median_gap_ms` near the
  150 ms probe interval, `client_span_ms` a large fraction of the ~3 s emit
  window), NOT one terminal burst.
- `first_token_ms <= 1500` measured on the prod chain.
- `http_status: 200` and `content_type: text/event-stream` preserved end to end.

STOP (do not build; keep panels-first) if NO method streams incrementally end to
end. The report must name the FIRST layer that buffered, using the A/B steps:

- Step 1 buffers -> probe/headers wrong (not a real STOP; fix and re-run).
- Step 2 buffers (Step 1 clean) -> cloudflared / Cloudflare edge.
- Step 3 buffers (Step 2 clean) -> Vercel / Next route handler.
- Step 4 buffers (Step 3 clean) -> the generic `/api/be` proxy logic.

## Numbers to capture per step (for BENCHMARK_REPORT.md)

For each step, keep the `result_stepN_*.json` file and record:

- `label`, `url`, `http_status`, `content_type`
- `first_byte_ms`, `meta_ms`, `first_token_ms`, `done_ms`
- `token_count`, `client_span_ms`, `median_gap_ms`, `gaps_ms`
- `incremental` (bool), `first_token_under_1500ms` (bool), `verdict`
- the raw response headers from `measure_stream.sh` (to confirm anti-buffer
  headers survived each layer)

The per-layer buffering map (which layer first buffered, or "none") plus the
chosen method and its measured first-token latency are the WS2 deliverable
(`BENCHMARK_REPORT.md`).

## Open prerequisites O0 must confirm before running

1. cloudflared routing for the probe: which hostname/path maps to the probe port
   (e.g. a temporary `orcast-api.aimez.ai/__stream_probe` ingress rule to
   `127.0.0.1:8099`), without disturbing the live `:8090` `orcast-api.service`
   ingress. The probe must be reachable through the same edge as prod for Step 2
   to be meaningful.
2. uvicorn probe port: confirm 8099 (or another free port) is open on the backend
   host and not in use.
3. Vercel preview availability: confirm a preview deployment can be created with
   `ORCAST_API_BASE=https://orcast-api.aimez.ai` in its env, and that the throwaway
   `web/app/api/__streamprobe/route.ts` may be added on a non-main branch.
4. Whether Step 4 (Option A, touching `/api/be` on a throwaway branch) is in scope
   now, or deferred to WS4 — Step 3 alone can clear the gate; Step 4 de-risks the
   convergence path early.

# WS-STREAM WS1 research synthesis

Output of the WS1 Research wave (4 read-only investigators: R1 transport methods,
R2 platform buffering, R3 backend streaming, R4 higher-reward reuse sizing).
Read-only; no code edited; no live calls. This document is the WS1 deliverable
named in `wave_shape.yml`.

Prod chain under study (LOCKED): `Browser -> Vercel -> Next /api/be/[...path]/route.ts
-> ORCAST_API_BASE (https://orcast-api.aimez.ai) -> cloudflared tunnel -> uvicorn/FastAPI`
(App Runner = rollback). Narration is non-streaming JSON end-to-end today.

## 0. The shared blocker chain (confirmed in code)

| Flag | Evidence | State |
|------|----------|-------|
| Proxy buffers full body | `web/app/api/be/[...path]/route.ts:175-180` `await resp.text()` | CERTAIN today |
| narrate not public | `route.ts:59-69` allow-lists `plan` not `narrate` -> anonymous 401 | CERTAIN today |
| client expects JSON | `web/lib/adaptiveConsole.ts:135-144` `res.json()` | CERTAIN today |
| backend returns JSON | `interactions.py:274-343` sync handler, full `compose_guide_reply` | CERTAIN today |
| no IAM stream action | `infra/shared_host/iam/orcast_host_policy.json:44-53` `InvokeModel` only | CERTAIN today |
| no Vercel stream config | `web/vercel.json` framework only; `route.ts:18` has `dynamic=force-dynamic`, no `runtime`/`maxDuration` | partial |

Shared anti-buffering headers (set at uvicorn origin, re-asserted on Next outbound):
`Content-Type: text/event-stream; charset=utf-8`; `Cache-Control: no-cache, no-transform`;
`Connection: keep-alive`; `X-Accel-Buffering: no`; omit `Content-Length`; no gzip/Brotli.
Client constraint (all methods): `EventSource` is GET-only and narrate is a POST with a
large body, so use `fetch` + `response.body.getReader()` + `TextDecoder`.

---

## 1. R1 — transport methods (per-layer anti-buffering config)

Six candidate methods compared. For each: technique, the specific config that defeats
buffering at each chain layer, and the single most-likely culprit.

### 1.1 sse_through_proxy_passthrough (fix /api/be to stream resp.body)
- **Technique:** replace `await resp.text()` at `route.ts:175-180` with
  `new Response(resp.body, { status, headers })`; add `narrate` to the public allow-list
  (`route.ts:59-69`); client switches to a reader loop.
- **Next route:** `resp.body` passthrough; re-set `Content-Type: text/event-stream`,
  `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`; do NOT overwrite
  upstream `Content-Type` with `application/json` (current behavior at `route.ts:149-150`);
  `cache: "no-store"` (already at `:165`).
- **Vercel:** `export const runtime = "nodejs"`; `export const dynamic = "force-dynamic"`;
  `export const maxDuration = 60` (300s Fluid Compute default is enough for ~5.5s).
- **Cloudflare/cloudflared:** origin `text/event-stream` (cloudflared bypasses buffering for
  this type); `Cache-Control: no-transform`; `X-Accel-Buffering: no`; disable compression;
  zone Configuration Rule `response_body_buffering: none` for the narrate path if needed.
- **uvicorn:** `StreamingResponse` with a sync `def` generator (so boto3 runs in the
  threadpool), media_type `text/event-stream`, headers above; periodic `: ping\n\n` heartbeats.
- **Most-likely culprit:** the Next `resp.text()` buffer (certain today); after the fix,
  Vercel platform or cloudflared edge.

### 1.2 dedicated_next_stream_route (purpose-built route, bypass generic /api/be)
- **Technique:** a new route (e.g. `web/app/api/stream/narrate/route.ts`) that does auth,
  allow-list, upstream fetch, and `resp.body` pipe with abort propagation (`request.signal`),
  isolated from generic `/api/be` matching.
- **Per-layer:** same anti-buffer headers as 1.1 but scoped to this one file; `maxDuration`
  attaches to this route without touching other `/api/be` traffic; avoids the inbound
  `Content-Type: application/json` override the generic proxy forces.
- **Most-likely culprit:** Vercel platform or cloudflared (Next-layer buffering eliminated by
  design). This is the cleanest WS2 probe to isolate which upstream layer still buffers.

### 1.3 direct_backend_domain (client streams straight from backend, bypass Vercel)
- **Technique:** browser `fetch("https://orcast-api.aimez.ai/api/interactions/narrate/stream")`
  cross-origin; Vercel not on the stream path. Auth cannot put `X-ORCAST-Key` in the browser
  (`src/aws_backend/auth.py:14-20`), so needs either a public session-scoped stream route
  (mirror the `plan` posture) or a short-lived HMAC stream ticket minted by Next.
- **Per-layer:** CORS at uvicorn (`ORCAST_CORS_ORIGINS=https://orcast-h0.vercel.app` — the `*`
  default at `main.py:51-68` disables credentials), `Access-Control-Allow-Methods: POST,OPTIONS`,
  OPTIONS preflight; same SSE headers; one fewer proxy hop (no Vercel).
- **Most-likely culprit:** cloudflared/Cloudflare edge (the only HTTP proxy left). If this
  streams but 1.1/1.2 do not, Vercel/Next is confirmed guilty.

### 1.4 chunked_ndjson (if SSE buffered but chunked transfer is not)
- **Technique:** `StreamingResponse` yielding `json.dumps(obj)+"\n"`, media_type
  `application/x-ndjson`; client splits on `\n` and `JSON.parse` each line.
- **Per-layer:** same passthrough; BUT cloudflared/Cloudflare buffering is tuned for
  `text/event-stream`, not arbitrary types — NDJSON may be held until a byte threshold or
  connection close. Workaround: wrap NDJSON payloads inside SSE `data:` frames.
- **Most-likely culprit:** cloudflared/Cloudflare edge treating it as bufferable non-SSE.
  Weakest edge story; deprioritized.

### 1.5 websocket (if unidirectional SSE buffered at an edge)
- **Technique:** `wss://` direct to backend; FastAPI `@router.websocket(...)`.
- **Per-layer:** standard App Router Route Handlers do NOT support WS upgrade on serverless,
  so this is only viable as direct-backend WS (Vercel proxy cannot carry it). cloudflared
  tunnels WS natively; no HTTP response-buffering class of bug.
- **Most-likely culprit:** Vercel/Next (WS upgrade unsupported). Overkill for unidirectional
  narrate; deprioritized for consumer #1.

### 1.6 platform_response_streaming (Vercel/Lambda streaming primitives)
- **Technique:** not a distinct transport — the operational knob layer on top of 1.1/1.2:
  `runtime="nodejs"`, `dynamic="force-dynamic"`, `maxDuration`, `fetchCache="force-no-store"`,
  return the stream before awaiting the full upstream body. Edge runtime is a trap (30s cap,
  25s TTFB gate).
- **Most-likely culprit:** `maxDuration`/plan timeout if streaming works locally but cuts off;
  otherwise same as 1.1.

---

## 2. R2 — platform buffering (Vercel / Cloudflare / uvicorn)

### 2.1 Vercel
- Node.js runtime (App Router default) is correct for SSE; Edge has a 25s TTFB gate + 300s cap
  and no `maxDuration`. Use Node.js explicitly.
- Function duration: Fluid Compute default 300s (all plans), max 800s Pro/Enterprise. A ~5.5s
  reply is far inside default; duration is NOT the current blocker. Failure mode if someone
  sets `maxDuration` too low: 504 `FUNCTION_INVOCATION_TIMEOUT`, stream cut mid-response,
  not reliably catchable in the handler.
- Vercel does NOT buffer if the handler returns a streaming `Response` immediately. It
  effectively buffers when the handler awaits the full upstream body first — which is exactly
  `route.ts:175-180` today.
- Anti-buffer: `X-Accel-Buffering: no` (respected by Vercel's nginx-like layer), `no-transform`
  (stop re-compression), omit `Content-Length`, let `Transfer-Encoding: chunked` happen.
- **Culprit:** `resp.text()` (certain); after fix, missing `X-Accel-Buffering`/`no-transform`.

### 2.2 Cloudflare / cloudflared
- cloudflared (token, remote-managed; no host `config.yml`) should NOT buffer `text/event-stream`
  (fixes in cloudflared #1095/#1404, ~2025.5+); non-SSE streaming historically buffered until a
  byte threshold/close.
- Cloudflare edge default `response_body_buffering: standard` inspects a prefix of the body for
  WAF/Bot — can batch small SSE chunks; community reports of ~100KB accumulation before flush;
  Brotli/gzip at edge requires buffering.
- Anti-buffer: origin `text/event-stream` + `Cache-Control: no-cache, no-transform` +
  `X-Accel-Buffering: no` + omit `Content-Length`; zone Configuration Rule
  `response_body_buffering: none` scoped to `orcast-api.aimez.ai` + `/api/interactions/narrate*`;
  optional Compression Rule off for SSE; cache bypass; keep cloudflared current.
- **Culprit:** edge `standard` body buffering + compression without `no-transform`. cloudflared
  is a secondary suspect (old version / wrong content-type).

### 2.3 uvicorn / FastAPI
- Prod is a SINGLE uvicorn process (`infra/shared_host/systemd/orcast-api.service:12`),
  `--proxy-headers` default-on, `forwarded-allow-ips=127.0.0.1` (correct for cloudflared->localhost).
- uvicorn does not application-buffer ASGI streaming bodies; bytes flush as the generator yields.
- CRITICAL gotcha: use a sync `def` generator (Starlette runs it via `iterate_in_threadpool()`,
  keeping the event loop free). An `async def` generator wrapping sync boto3 blocks the loop and
  collapses concurrency. Don't wrap the generator in body-collecting middleware.
- Concurrency: each sync stream holds one threadpool slot (~40 default) for ~5.5s; at the proxy
  rate limit (10/min) single-worker uvicorn is adequate.
- In-repo SSE reference `scripts/data_processing/realtime_sse.py:201-209` is NOT wired to prod
  and is missing `X-Accel-Buffering`/`no-transform` — do not copy it verbatim.
- **Culprit:** not buffering today; after implementation, `async def`+sync boto3, or missing
  the anti-buffer headers so an upstream layer buffers despite correct uvicorn behavior.

### 2.4 Recommended probe isolation order (for WS2)
1. Direct uvicorn (`curl -N` to `127.0.0.1:8090`) — confirms generator + headers.
2. Through cloudflared (`curl -N https://orcast-api.aimez.ai/__stream_probe`) — isolates edge+tunnel.
3. Through Vercel preview (`curl -N` POST via `/api/be/...`) — isolates Next + Vercel edge.
If 1 streams but 3 bursts -> fix Next. If 2 bursts but 1 streams -> fix Cloudflare headers/rules.

---

## 3. R3 — backend streaming (Bedrock / persistence / IAM / allow-list / meta)

### 3.1 Bedrock chunk parsing (Claude Haiku, Anthropic Messages on Bedrock)
- Only the API call changes: `invoke_model_with_response_stream` replacing
  `invoke_model` at `guide.py:184-196`. Body, `modelId`, region, model default
  (`settings.bedrock_sighting_model_id`, Haiku 4.5) stay identical.
- `response["body"]` is a botocore EventStream (sync iterator). Per item:
  `payload = json.loads(event["chunk"]["bytes"])`; emit a token only when
  `payload["type"] == "content_block_delta"` and `payload["delta"]["type"] == "text_delta"`
  -> `payload["delta"]["text"]`. Control events: `message_start`, `content_block_start`,
  `content_block_stop`, `message_delta`, `message_stop` (stream complete -> safe to finalize).
- Add a sibling `_bedrock_guide_stream` generator in `guide.py`; keep `_bedrock_guide`.

### 3.2 Persistence at stream end
- `save_interaction_exchange` (today `interactions.py:318-331`) writes user + assistant turns
  atomically via `append_turn` (`session_store.py:153-189`); tests assert exactly one exchange
  on narrate success (`test_interactions_plan.py:175-176`).
- Streaming approach: mint `interaction_id` before the stream (emit in `meta`); accumulate
  deltas; on `message_stop` build the full `GuideReply` (reply = joined deltas;
  citations/deep_links/etc. from the prefetched tuple) and call `save_interaction_exchange`
  ONCE; emit `done`. On abort/error/disconnect before `message_stop`: emit `error`, persist
  NOTHING (no partial DB turn). Persistence stays best-effort try/except.

### 3.3 IAM
- Add `bedrock:InvokeModelWithResponseStream` alongside `bedrock:InvokeModel` (same ARNs) in
  TWO places: live co-tenant `infra/shared_host/iam/orcast_host_policy.json:44-53` (role
  `aimez-host-role`) and App Runner rollback `infra/aws/template.yaml:258-265`
  (`AppRunnerInstanceRole`). Operator-applied ops task (`wave_shape.yml:48,116`).

### 3.4 Narrate allow-list gap (confirmed)
- `route.ts:59-69` allow-lists `api/interactions/plan` but NOT `api/interactions/narrate`;
  the console calls narrate anonymously (`adaptiveConsole.ts:135-138`) -> 401 today.
  Path join has no leading slash (`route.ts:111`). Add:
  `if (method === "POST" && path === "api/interactions/narrate") return true;`
  and, if a stream route is split out, `"api/interactions/narrate/stream"`. Consider adding
  narrate to `explorePathLimit` (`route.ts:97-104`) for rate-limit parity. Backend still
  requires `X-ORCAST-Key` via `Depends(require_api_key)` (`interactions.py:274`); the proxy
  injects it for public routes (`route.ts:156`).

### 3.5 Meta-event metadata (available before Bedrock)
- Plan phase (`/plan`) builds grounded context and embeds `prepare.{context, citations,
  deep_links, tools_used, gate_ids, provenance_refs}` (`interactions.py:140-148`). The client
  forwards these to `/narrate` (`adaptiveConsole.ts:120-134`); narrate passes them as
  `prefetched` so skills are NOT re-run (`interactions.py:300-316`, `guide.py:120-128`).
  Therefore an opening `meta` SSE event can carry interaction_id + citations + deep_links +
  tools_used + gate_ids + provenance_refs + source + model BEFORE any token streams — prose
  only streams, metadata is byte-identical to panels-first.

---

## 4. R4 — higher-reward reuse (SIZE-AND-DOCUMENT ONLY)

No abstraction designed. Three charter-named future consumers sized against repo evidence:

| Future consumer | What streaming unlocks | Repo surface today | Reward | Push/pull |
|---|---|---|---|---|
| Live ferry/corridor connection refresh | push updated WSF ETAs, sailing space, corridor travel-time while a `connections_plan` is open so feasibility/freshness stay current | live stack exists, snapshot-only UI: `planner.py`, `trips/connections.py`, `ActiveSurfaceHost.tsx`, sources `wsf.py`/`wsdot_traffic.py`, `corridor.py`; background poll `tools/corridor_poll.py` | **High** — confirmed trips product, realtime sources, panel goes stale in minutes | Push (server-initiated subscription) |
| Progressive whole-turn | multiplex panel/`ui_intent` deltas with narration tokens in one stream; one abort/generation guard | shipped two-phase split: `adaptiveConsole.ts`, `AdaptiveExplore.tsx`, `/plan`+`/narrate` | **Medium** — panels-first already removes the first-paint gate; mainly consolidates client lifecycle, saves a hop | Pull (response-streaming, same as #1) |
| Hydrophone / acoustic event push | push new acoustic candidates/detections to map pins, `hydrophone_signal`, sidequests without poll | pull snapshots only: `HydrophoneSignalPanel.tsx`, `onc.py`, `read.py`; batch ingest `ingest_multistation.py`; legacy unwired SSE prototype | **Medium** — strong domain fit but no prod push path, ONC live is token-gated, QC means not every candidate should surface | Push (server-initiated) |

Transport note: consumer #1 is pull response-streaming (POST + reader). #2 and #3 are push
subscriptions (likely GET-side SSE/WS fan-out). A proven channel justifies investment if it
carries both an opaque POST pass-through AND a durable subscription fan-out, without conflating
the two semantics at the application layer.

Deferred abstraction-boundary note (NOT a now-task): if built later, the reusable boundary
sits at the transport edge only — a browser module owning proxy-pass-through reading + abort
guards (+ optional subscription lifecycle), paired with a backend helper owning framed
`StreamingResponse` (headers, anti-buffering, thread-safe generators) and a separate
subscription endpoint. Consumer semantics (token parsing, connection-delta JSON, acoustic
envelopes) stay in existing owners. WS4 already names the transport-client-module split at a
high level. R4 does not specify APIs or implementation order.

---

## 5. WS1 gate verdict

Gate (from `wave_shape.yml`): each candidate_method has named techniques + the specific
anti-buffering config at each chain layer; R4 sizes the reusable-capability reward.

**PASS.** Reasons:
- All six candidate methods have a named technique and per-layer anti-buffering config
  (Next handler / Vercel / Cloudflare-cloudflared / uvicorn) — §1.
- Platform buffering behavior named per layer with specific flags/headers and the most-likely
  culprit each, plus a probe isolation order — §2.
- Backend streaming is fully grounded: chunk-parse recipe, persistence-at-end, the exact IAM
  action and the two policy files, the exact allow-list string, and the pre-Bedrock meta
  source — §3.
- R4 sizes three future consumers with reward + push/pull + a deferred boundary note, staying
  inside size-only scope — §4.

The single dominant, code-confirmed culprit across all methods is the Next proxy
`await resp.text()` buffer (`route.ts:175-180`). Whether Vercel and cloudflared also buffer
after that fix is the empirical unknown that ONLY WS2 (which touches prod) can settle.

## 6. Ranked shortlist to benchmark in WS2 (top 3)

1. **dedicated_next_stream_route + SSE** — best throwaway probe; eliminates the known Next
   anti-patterns without touching the `/api/be` convergence file; measures whether Vercel +
   cloudflared pass SSE. Most-likely culprit if it fails: Vercel platform or cloudflared edge.
2. **direct_backend_domain + SSE** — bypasses Vercel; A/B against #1 to localize the layer.
   Most-likely culprit if it fails: cloudflared / Cloudflare edge (only HTTP proxy left).
3. **sse_through_proxy_passthrough + platform_response_streaming config** — the production
   convergence path once proven; minimal diff to `route.ts:175-180` + runtime/maxDuration +
   allow-list. Most-likely culprit: the `resp.text()` buffer, then missing
   `X-Accel-Buffering`/`no-transform` on the outbound stream.

Deprioritized: chunked_ndjson (weak edge story unless SSE specifically fails at Cloudflare),
websocket (architectural mismatch with the Vercel proxy; unnecessary for unidirectional narrate).

Fallback invariant for every method: the non-streamed `/narrate` JSON path
(`interactions.py:274-343`, `adaptiveConsole.ts:135-144`) stays as the L5 fallback.

## 7. STOP

WS1 complete. WS2 is GATED on operator approval of prod probes (throwaway Vercel preview +
cloudflared backend) and confirmation of the 1.5s first-token goal. Do not start WS2.

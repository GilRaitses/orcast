# WS2 benchmark report (the WS2 deliverable)

O0 executed the `BENCHMARK_PLAN.md` runbook. The sub-orchestrator authored the
probes and runbook; O0 deployed, measured, and relayed the numbers. Raw results
are in `WS2_O0_MEASUREMENTS.md` and `ws2_probes/result_*.json`. This report is
the WS2 deliverable: the per-layer buffering map, the result tables, the gate
verdict, and the chosen method with its caveats.

## 1. Per-layer buffering map

Prod chain studied: `Browser -> Vercel -> Next /api/be -> cloudflared -> uvicorn`.
App Runner (`*.awsapprunner.com`) is the Cloudflare-free alternative kept RUNNING
as rollback per DD-1/DD-3.

| Layer | Buffers SSE? | Evidence | Notes |
|-------|--------------|----------|-------|
| uvicorn + `StreamingResponse` (origin) | NO | Step 1 PASS: first token 310 ms, ~157 ms gaps, client span 3142 ms | The probe headers and sync `def` generator stream correctly. The backend is not the problem. |
| Cloudflare edge / cloudflared | YES | Step 2 FAIL: entire SSE held and delivered in one burst across QUIC and HTTP/2, across ~1.4 KB and ~28 KB payloads | Not a protocol artifact and not a buffer-size threshold. The edge held the whole response. See caveat. |
| Vercel dedicated Node route (`resp.body` passthrough) -> App Runner | NO | WS4 step-0 PASS: first token ~0.4-0.5 s, incremental (151 ms and 51 ms gaps), stable on a 10 s / 200-token stream | Measured on the FULL production shape. The generic `/api/be` (Cloudflare path) still buffers and is NOT used for the stream. |
| App Runner (Cloudflare-free) | NO | 3 runs PASS: first token ~0.5-0.6 s, incremental at the server interval, content-type preserved, stable on a ~10 s / 200-token stream | App Runner supports HTTP response streaming natively. Clears the gate. |

## 2. Result tables

### 2.1 Step 1 — origin (local uvicorn + anti-buffer headers)

| Step | Path | first_byte | first_token | client_span | incremental | verdict |
|------|------|-----------|-------------|-------------|-------------|---------|
| 1 | direct uvicorn | 161 ms | 310 ms | 3142 ms | YES (gaps ~157 ms) | PASS |

### 2.2 Step 2 — Cloudflare-fronted path (cloudflared quick tunnel to the local probe)

| Step | Path | first_byte | first_token | client_span | incremental | verdict |
|------|------|-----------|-------------|-------------|-------------|---------|
| 2 | quick tunnel, QUIC | 3783 ms | 3784 ms | 0 ms | NO (one burst) | FAIL |
| 2 | quick tunnel, HTTP/2 | 4497 ms | 4497 ms | 1 ms | NO (one burst) | FAIL |
| 2 | quick tunnel, 400 frames ~28 KB | 5768 ms | 5768 ms | 7 ms | NO (one burst) | FAIL |

Caveat: this used a `trycloudflare.com` QUICK tunnel, a different Cloudflare
product from the production `aimez.ai` NAMED-tunnel zone. A named zone can carry
different edge settings. So this proves a default Cloudflare-fronted path buffers
our SSE and strongly indicates the prod zone will too, but it is not a measurement
of the exact prod hostname. A faithful prod-zone test would need an SSM session on
the shared `aimez-services` host plus a temporary named-tunnel ingress (operator-
gated; the host also serves other traffic). The chosen method routes around
Cloudflare, so this is left as a known-unmeasured edge.

### 2.3 App Runner lane (Cloudflare-free) — the chosen method

Throwaway amd64 probe image -> throwaway ECR repo -> SEPARATE throwaway App Runner
service (`ws2-stream-probe`, never touched the `orcast-aws-backend` rollback),
measured, then torn down.

| Run | Path | first_byte | first_token | client_span | median_gap | incremental | verdict |
|-----|------|-----------|-------------|-------------|-----------|-------------|---------|
| A (20x150ms) | App Runner direct | 463 ms | 608 ms | 2880 ms | 150 ms | YES | PASS |
| B (20x150ms) | App Runner direct | — | 578 ms | 2856 ms | 150 ms | YES | PASS |
| C (200x50ms, ~10s) | App Runner direct | — | 464 ms | 10008 ms | 50 ms | YES | PASS |

Throwaway infra deleted after measuring (App Runner service + ECR repo). No change
to the production `orcast-aws-backend` service or the cloudflared host.

### 2.4 WS4 step-0 — full production shape (browser -> dedicated Vercel Node route -> App Runner)

This settles the one layer Step 3 left unmeasured: a dedicated Vercel Node route
with `resp.body` passthrough, upstream = App Runner (NOT the cloudflared `/api/be`
path). Throwaway infra torn down after measuring. Detail in
`WS2_O0_MEASUREMENTS.md` (Vercel step-0 table + gotchas).

| Path | first_token | gaps | stability | incremental | verdict |
|------|-------------|------|-----------|-------------|---------|
| browser -> Vercel Node route -> App Runner | ~0.4-0.5 s | 151 ms / 51 ms | stable on a 10 s / 200-token stream | YES | PASS |

The full production shape streams unbuffered end to end, first token well under
the 1.5 s goal.

## 3. WS2 gate verdict

Gate (from `wave_shape.yml`): at least one method PROVEN to stream incrementally
through the full prod chain with a measured first-token latency; a per-layer
buffering map recorded; if none stream, report which layer buffered and STOP.

**PASS — via the App Runner (Cloudflare-free) lane.** App Runner streams SSE
incrementally with first token ~0.5-0.6 s, under the confirmed 1.5 s goal, stable
across short and ~10 s streams. The per-layer map above is recorded: origin
streams, Cloudflare buffers, App Runner streams.

The gate is cleared by routing the narration stream around Cloudflare via App
Runner, NOT through the cloudflared/`aimez.ai` path that the rest of the API uses.

## 4. Chosen method and caveats

**Chosen shape (LOCKED for WS4):** the narration stream traverses App Runner, not
cloudflared. The browser calls a NEW dedicated Vercel Node route
(`web/app/api/narrate-stream/route.ts`) whose upstream is an App Runner base URL
from a NEW env var (`ORCAST_STREAM_BASE`), injecting `X-ORCAST-Key` server-side and
passing `resp.body` through with streaming headers. The generic `/api/be`
(-> `aimez.ai`/cloudflared) is NOT used for the stream (it buffers) and is left
unchanged; everything non-stream stays on `/api/be`. WS4 step-0 PROVED this full
shape streams unbuffered (§2.4).

Resolved / remaining items:

1. **Browser reachability — RESOLVED.** Shape = dedicated streaming Vercel route ->
   App Runner with server-side key injection. Key never reaches the browser.
2. **Vercel pass-through buffering — RESOLVED.** WS4 step-0 measured the dedicated
   Node route + `resp.body` passthrough as incremental (§2.4). Vercel does not
   re-buffer on the Node runtime for this shape.
3. **Prod Cloudflare zone is a strong negative signal, not a measurement.** Moot —
   the chosen shape routes around Cloudflare entirely.
4. The honesty invariants and fallback (non-streamed `/narrate` JSON via `/api/be`)
   are unchanged.

## 5. Next gate

WS3 Discovery grounds the App Runner method in the codebase (read-only). WS4
Implementation is gated on operator approval via O0.

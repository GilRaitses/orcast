# WS2 measurements (O0-executed, partial)

O0 ran the WS2 runbook gate-only (Steps 1-2). Step 3 (Vercel) is on hold pending
the operator decision below, because Step 2 already surfaced a blocking signal.

## Method

- Probe: `ws2_probes/stream_probe_app.py` (FastAPI SSE, meta|token|done, exact
  anti-buffer headers: `Cache-Control: no-cache, no-transform`,
  `X-Accel-Buffering: no`). 20 token frames at 150 ms by default.
- Harness: `ws2_probes/measure_stream.mjs` (fetch + getReader, records per-token
  client arrival; `incremental` = median gap > 20 ms AND client span > 50 ms).
- Cloudflare path tested via a `cloudflared` QUICK TUNNEL to the local probe (no
  prod host or prod tunnel touched). Caveat below.

## Results

| Step | Path | first_byte | first_token | client_span | incremental | verdict |
|------|------|-----------|-------------|-------------|-------------|---------|
| 1 | direct uvicorn (origin) | 161 ms | 310 ms | 3142 ms | YES (gaps ~157 ms) | PASS |
| 2 | Cloudflare quick tunnel, QUIC | 3783 ms | 3784 ms | 0 ms | NO (one burst) | FAIL |
| 2 | Cloudflare quick tunnel, HTTP/2 | 4497 ms | 4497 ms | 1 ms | NO (one burst) | FAIL |
| 2 | Cloudflare quick tunnel, 400 frames ~28 KB | 5768 ms | 5768 ms | 7 ms | NO (one burst) | FAIL |

Result JSONs: `ws2_probes/result_step1_uvicorn.json`,
`result_step2_cloudflare.json`, `result_step2_cloudflare_http2.json`,
`result_step2_cloudflare_bigpayload.json`.

## Reading

- The ORIGIN streams correctly. uvicorn + `StreamingResponse` + the headers are
  not the problem; the backend will stream.
- The Cloudflare-fronted path BUFFERED the entire SSE response and delivered it in
  a single burst after the full server emit window — across QUIC and HTTP/2, and
  across tiny (~1.4 KB) and large (~28 KB) payloads. So it is not a transport
  protocol artifact and not a buffer-size threshold; the edge held the whole
  response.

## Caveat (why this is a strong signal, not a final verdict)

The test used a `trycloudflare.com` QUICK TUNNEL, which is a different Cloudflare
product from the production `aimez.ai` NAMED-tunnel zone. A named zone CAN carry
different edge settings. So this proves "a default Cloudflare-fronted path buffers
our SSE," and strongly indicates the prod zone will too, but it is not a
measurement of the actual prod hostname.

## Architectural implication

The prod backend (`orcast-api.aimez.ai`) is Cloudflare-fronted. BOTH candidate
methods that reach it — the Vercel `/api/be` pass-through AND the
direct-backend-domain bypass — traverse Cloudflare. If the prod zone buffers like
the quick tunnel did, neither clears the gate, and testing Vercel (Step 3) is moot
because Cloudflare is upstream of the answer.

The only Cloudflare-FREE path to a running backend is the App Runner URL
(`pjrftm3bkv.us-west-2.awsapprunner.com`, kept RUNNING as rollback per DD-1/DD-3).
App Runner supports HTTP response streaming natively. A viable method may be a
dedicated narration-stream lane served from App Runner (Cloudflare-free), separate
from the main cloudflared API path.

## App Runner (Cloudflare-free) test — PASS

Operator chose to pivot to the App Runner lane. O0 built a throwaway amd64 probe
image, pushed it to a throwaway ECR repo, stood up a SEPARATE App Runner service
(`ws2-stream-probe`, url `mcumxy76pe.us-west-2.awsapprunner.com`, never touching
the `orcast-aws-backend` rollback service), measured, then tore both down.

| Run | Path | first_byte | first_token | client_span | median_gap | incremental | verdict |
|-----|------|-----------|-------------|-------------|-----------|-------------|---------|
| A (20x150ms) | App Runner direct | 463 ms | 608 ms | 2880 ms | 150 ms | YES | PASS |
| B (20x150ms) | App Runner direct | — | 578 ms | 2856 ms | 150 ms | YES | PASS |
| C (200x50ms, ~10s) | App Runner direct | — | 464 ms | 10008 ms | 50 ms | YES | PASS |

Result JSONs: `ws2_probes/result_step_apprunner*.json`.

App Runner does NOT buffer SSE. Tokens arrive incrementally end-to-end, first
token ~0.5-0.6 s (well under the 1.5 s goal), content-type preserved, stable
across short and long (~10 s) streams. The Cloudflare-free App Runner lane CLEARS
the WS2 gate.

Throwaway infra (deleted after measuring): App Runner service
`arn:.../ws2-stream-probe/cd426e3b44ef4b10824e9ff1c8f0ed10`, ECR repo
`ws2-stream-probe`. No change to the production `orcast-aws-backend` service or
the cloudflared host.

## WS2 verdict

PASS via the App Runner lane. The method that clears the gate is: serve streamed
narration from an App Runner endpoint (Cloudflare-free), NOT through the
cloudflared/`aimez.ai` path. The Vercel `/api/be` proxy and the cloudflared edge
both buffer (or at least the default Cloudflare path does); App Runner streams.

Open follow-ups for WS3/WS4:
- The browser must reach the App Runner stream. Either call the App Runner URL
  directly for the narration stream (CORS + the API key, separate from `/api/be`),
  or add a STREAMING Vercel route that passes through to App Runner (Vercel's own
  buffering still to be confirmed, but Vercel streaming on the Node runtime is
  documented; the cloudflared hop is the one we now avoid).
- Confirm Vercel pass-through does not re-buffer (deferred; can be measured on the
  real WS4 preview deploy since a preview is needed anyway).

## WS4 step-0 — Vercel stream route -> App Runner — PASS

The one unmeasured layer in the recommended shape (c): does the Vercel Node route
re-buffer when it passes `resp.body` through to App Runner? Measured on a throwaway
Vercel preview (dedicated `streamprobe` route, `ORCAST_API_BASE` -> the throwaway
App Runner probe), then torn down.

| Run | Path | first_byte | first_token | client_span | median_gap | incremental | verdict |
|-----|------|-----------|-------------|-------------|-----------|-------------|---------|
| 1 (20x150ms) | browser -> Vercel route -> App Runner | 345 ms | 479 ms | 2861 ms | 151 ms | YES | PASS |
| 2 (200x50ms, ~10s) | same | — | 340 ms | 10081 ms | 51 ms | YES | PASS |

Result JSONs: `ws2_probes/result_step3_vercel*.json`.

The full production shape streams unbuffered end to end: first token ~0.4-0.5 s
(under the 1.5 s goal), tokens incremental at the server interval, content-type
preserved, stable on a 10 s stream. Vercel's Node route handler does NOT re-buffer
with `resp.body` passthrough. Shape (c) is proven; no fallback to direct
browser->App Runner is needed.

Gotchas found and recorded for WS4: (1) App Router treats `_`-prefixed route
folders as PRIVATE (not routed) -> the real route must not start with `_`;
(2) Vercel Deployment Protection (SSO) is ON by default for the team and 302s a
preview to a login page -> the real `/api/.../stream` route's reachability for
anonymous judges must be verified (the prod `orcast-h0` project's protection
state, and the proxy public allow-list, both apply).

Throwaway infra (all deleted after measuring): App Runner service
`.../ws2-stream-probe/24413b4c9ad141b39e098b6fca7de8ae`, ECR repo
`ws2-stream-probe`, Vercel project `prj_AyXcMBajaMuBlEVpKrnwFqd1LPkx`. No prod
service touched.

## Decision needed (escalated to operator via O0) — RESOLVED

Operator picked the App Runner lane; measured PASS. WS4 step-0 confirms the Vercel
stream route -> App Runner shape (c) streams end to end. Operator approved WS4
start (step-0 first), shape (c), and the two downstream ops gates. WS4
implementation (diffs only, no deploy) is cleared.

1. Faithful prod-zone test: SSM to the shared `aimez-services` host + a TEMPORARY
   ingress on the named tunnel for the probe path -> measure the real `aimez.ai`
   edge. Definitive, but touches shared prod infra (operator-gated; SSM-only, the
   host also serves pax).
2. Test the App Runner (Cloudflare-free) streaming lane as the method instead.
3. Treat Cloudflare as a likely blocker and STOP per the charter (keep
   panels-first), pending a cheaper definitive test.

Status: WS2 PARTIAL. Origin PASS; Cloudflare path FAIL via quick tunnel. Held at
the prod-zone decision.

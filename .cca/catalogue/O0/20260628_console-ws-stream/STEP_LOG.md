# WS-STREAM step log

## 2026-06-28 — charter

- Graduated WS-PERF T4 (streamed narration) into WS-STREAM after the T4 research
  showed the transport chain, not the narration code, is the risk.
- Seven-wave shape: Research, Benchmark (added), Discovery, Implementation,
  Adversarial, Remediation, Acceptance. Artifacts: `README.md`,
  `WAVESET_CHARTER.md`, `wave_shape.yml`.
- Framed as a reusable real-time channel (streamed narration is consumer #1) so
  the transport investment is higher-reward than a narration-only feature.
- Ten transport flags and six candidate methods enumerated in `wave_shape.yml`.
- Status: chartered, pending operator go. No wave has run.

## 2026-06-28 — WS1 Research (complete, PASS)

- Ran WS1 with 4 read-only parallel subagents (R1 transport methods, R2 platform
  buffering, R3 backend streaming, R4 reuse sizing). No code edited; no live calls.
- Deliverable: `RESEARCH_SYNTHESIS.md` (uncommitted local state).
- Gate verdict: PASS. Each of the six candidate methods has named techniques +
  per-layer anti-buffering config (Next handler / Vercel / Cloudflare-cloudflared /
  uvicorn); the dominant code-confirmed culprit is the `/api/be` `await resp.text()`
  buffer (`route.ts:175-180`); R4 sized three future consumers (ferry/corridor refresh
  High; progressive whole-turn Medium; hydrophone push Medium) with a deferred
  boundary note.
- WS2 shortlist (top 3 to benchmark): (1) dedicated_next_stream_route + SSE,
  (2) direct_backend_domain + SSE, (3) sse_through_proxy_passthrough +
  platform-streaming config. Deprioritized: chunked_ndjson, websocket.
- STOP at WS2 gate: WS2 prod probes need operator approval (via O0) plus the 1.5s
  first-token goal confirmation. WS2 not started.

## 2026-06-28 — WS2 Benchmark (artifacts authored; awaiting O0 deploy+measure)

- O0 relay: operator APPROVED throwaway prod probes (Vercel preview + cloudflared
  backend) and CONFIRMED first-token <= 1500 ms on the prod chain.
- Per locked discipline, sub-agents DEPLOY NOTHING / CONTACT PROD NOTHING. This
  rotation AUTHORED the probe artifacts + runbook only; O0 deploys and measures.
- Authored (all uncommitted local scratch state, NOT installed/merged):
  - `ws2_probes/stream_probe_app.py` — minimal FastAPI `/__stream_probe` SSE probe
    (meta/token/done framing, exact anti-buffer headers, sync `def` generator).
  - `ws2_probes/next_stream_route_candidate.ts` — CANDIDATE dedicated Next stream
    route (resp.body passthrough, nodejs/force-dynamic/maxDuration); not under web/app.
  - `ws2_probes/measure_stream.mjs` — fetch+getReader harness emitting JSON
    (first-token latency, incremental-vs-buffered).
  - `ws2_probes/measure_stream.sh` — curl --no-buffer -N eyeball + header dump.
  - `ws2_probes/README.md` — scratch index.
  - `BENCHMARK_PLAN.md` — 4-step A/B localization runbook (uvicorn -> cloudflared
    -> Vercel preview dedicated route -> /api/be passthrough) with PASS/STOP rubric.
- STOP: O0 runs the measurement and relays results back for the WS2 gate verdict.

## 2026-06-28 — WS2 Benchmark (complete, PASS via App Runner lane)

- O0 executed the runbook and relayed results (`WS2_O0_MEASUREMENTS.md`,
  `ws2_probes/result_*.json`). Deliverable: `BENCHMARK_REPORT.md`.
- Per-layer buffering map: origin uvicorn streams (Step 1 PASS, first token 310 ms);
  Cloudflare-fronted path BUFFERS the entire SSE into one burst (Step 2 FAIL, across
  QUIC + HTTP/2 + small/large payloads) via a trycloudflare quick tunnel — strong
  negative signal, not a prod-zone measurement; App Runner (Cloudflare-free) streams
  (3 runs PASS, first token ~0.5-0.6 s, stable on a ~10 s stream).
- WS2 gate verdict: PASS via the App Runner lane. Chosen method: serve streamed
  narration from an App Runner endpoint (Cloudflare-free), NOT the cloudflared
  `aimez.ai` path. Throwaway probe infra (ECR repo + separate App Runner service)
  built and torn down; rollback service untouched.
- Caveats carried forward: Vercel pass-through buffering unmeasured (Step 3 skipped);
  prod Cloudflare zone not definitively tested.

## 2026-06-28 — WS3 Discovery (complete, PASS)

- Ran WS3 with 3 read-only subagents (D1 frontend reachability, D2 backend endpoint
  placement, D3 convergence + invariants). Deliverable: `DISCOVERY_MAP.md`.
- Key findings: same FastAPI code on both App Runner and cloudflared; the stream lane
  needs App Runner for TRANSPORT only and routing is client/env-side (a new
  stream-base env is required; none exists today). Browser CANNOT reach App Runner
  directly today (narrate not allow-listed -> 401, proxy buffers, key required, no
  stream endpoint, no browser URL, CORS may exclude Vercel). Cleanest shape = a
  dedicated streaming Vercel route injecting the key and passing `resp.body` through
  to App Runner. IAM gate = App Runner instance role.
- Gate verdict: PASS. Convergence files named with seams (interactions.py,
  /api/be route.ts, adaptiveConsole.ts, AdaptiveExplore.tsx); phase-A producers
  located (guide.py stream generator, new sseTransport.ts, optional stream route);
  one-file-one-owner map + honesty invariants enumerated; panels-first (fd50929)
  structure documented to avoid regression.
- Biggest WS4 risk: whether the dedicated Vercel stream route re-buffers (Vercel
  streaming never measured); settle FIRST in WS4 on a throwaway preview before
  building the full endpoint + UI.
- STOP before WS4 implementation (operator approval via O0).

## 2026-06-28 — WS4 Implementation (complete, diffs-only)

- BSO authored WS4 as uncommitted diffs; step-0 measured browser → Vercel Node
  route → App Runner streaming first token ~0.4-0.5 s (PASS), so Vercel
  re-buffering risk RESOLVED. Nothing deployed/committed/pushed.
- Backend: `guide.py` `_bedrock_guide_stream()` generator; `interactions.py`
  `POST /api/interactions/narrate/stream` (StreamingResponse, sync gen →
  threadpool): meta (citations/deep_links/source/model from prefetched plan) →
  tokens → done; persist-once at end, persist-nothing on error.
- Frontend: new `sseTransport.ts`, dedicated `web/app/api/narrate-stream/route.ts`
  (Node, force-dynamic, resp.body passthrough to ORCAST_STREAM_BASE, server-side
  X-ORCAST-Key); `adaptiveConsole.runAdaptiveNarrationStream` (JSON path kept as
  fallback); `AdaptiveExplore.tsx` rAF-batched progressive render + AbortController
  + turn-generation guard; panels-first (fd50929) preserved.
- Validation: `tsc --noEmit` clean; pytest 320 passed (4 new stream tests).
- Deploy/ops deferred to O0: App Runner deploy, ORCAST_STREAM_BASE env, IAM
  bedrock:InvokeModelWithResponseStream, narrate JSON-fallback allow-list,
  ORCAST_ENABLE_BEDROCK on App Runner, anonymous-reach guard.

## 2026-06-28 — WS5 Adversarial (dispatched)

- Operator (via O0): run WS5 adversarial review on the diffs FIRST, then deploy
  for WS7 acceptance; fold the open Bedrock-cost narrate-stream guard
  (rate-limit/session-scope) into WS6 remediation BEFORE any public deploy.
- Launched one INDEPENDENT reviewer (not the WS4 builder) to run L1-L5 on the
  uncommitted diffs and file `DEFECT_REGISTER.md`; review-only, no code edits.
- STOP after WS5 for triage + WS6/deploy sequencing (operator approval via O0).

## 2026-06-28 — WS6 Remediation (complete, diffs-only)

- Closed all 1 blocking + 3 major defects from `DEFECT_REGISTER.md`; also closed
  the two recommended minors (m1, m2) as part of the same never-hang contract.
  m3/m4/m5 deferred (WS7 prod re-measure / info / pre-existing out-of-scope).
- B1 (open Bedrock-cost surface): per-IP rate bucket + per-IP concurrent-stream
  cap in `web/app/api/narrate-stream/route.ts` BEFORE key injection; backend
  per-session `assert_turn_quota` (→429) on `narrate/stream` in `interactions.py`.
- M1 (anonymous fallback 401s): `api/interactions/narrate` added to the `/api/be`
  public allow-list + an `explorePathLimit` bucket in `web/app/api/be/[...path]/route.ts`.
- M2 (no stall timeout): first-token + idle deadlines in `sseTransport.ts` that
  abort an INTERNAL controller and throw `SseStallError` (caller's signal left
  un-aborted → component falls back to JSON, never hangs in "Narrating…").
- M3 (threadpool exhaustion): process `BoundedSemaphore` bounds concurrent
  streams (busy→error frame→client fallback) + a per-stream wall-clock cap in
  `interactions.py`, independent of the Vercel `maxDuration`. Bound 8, cap 30 s.
- Minors: m1 superseded "Narrating…" bubble cleared via `pendingAssistantRef`;
  m2 EOF-without-`done` now throws → JSON fallback.
- Tests: +3 backend (turn-quota 429, concurrency-busy, wall-clock-cap); new
  client transport contract `web/lib/sseTransport.test.mts` (5 cases: normal/done,
  error-frame, EOF-without-done, stall→SseStallError signal-untouched,
  user-abort→signal-aborted). No JS/DOM runner is wired (only Playwright e2e);
  client fallback covered at the transport-contract level via `node --test`.
- Validation: `tsc --noEmit` clean; `pytest tests/aws_backend` 323 passed;
  `node --test lib/sseTransport.test.mts` 5 passed. panels-first (fd50929) and
  the JSON fallback intact. Nothing deployed/committed/pushed.

## 2026-06-28 — Commit + backend deploy (WS7 in progress)

- Operator (via O0): commit WS4+WS6 first, then O0 runs the deploy/ops checklist
  directly. Committed scoped to streaming as `874f830` (code + tests + WS-STREAM
  wave record; unrelated tree churn untouched).
- IAM: added `bedrock:InvokeModelWithResponseStream` to `infra/aws/template.yaml`
  (uncommitted) AND, non-destructively, applied it live as a separate inline
  policy `orcast-stream-bedrock` on the instance role
  `orcast-aws-backend-AppRunnerInstanceRole-4XtMQYZlzi4X` (verified present).
  Avoided a full CFN deploy because `deploy.sh` defaults
  `ORCAST_ENABLE_EXPLORATION_DATABASE=false` while the live stack has the
  exploration RDS/VPC enabled (teardown risk).
- Backend image: built `linux/amd64` from `tools/deployment/aws/Dockerfile`,
  pushed `orcast-aws-backend:ws-stream-874f830` to ECR, and
  `apprunner update-service` to that image (VPC egress + env + auth preserved;
  `ORCAST_ENABLE_BEDROCK=true` already set). Rollout op SUCCEEDED, service RUNNING.
- Verified on the Cloudflare-free native URL
  `https://pjrftm3bkv.us-west-2.awsapprunner.com`: `GET /health` 200;
  `POST /api/interactions/narrate/stream` (no key) → 401
  "Invalid or missing X-ORCAST-Key" (route present + auth gate live, not 404);
  JSON `POST /api/interactions/narrate` (no key) → 401.
- BLOCKED (operator action): Vercel (`orcast-h0`) needs the committed `web/`
  changes deployed + `ORCAST_STREAM_BASE=https://pjrftm3bkv.us-west-2.awsapprunner.com`
  set. Trigger is a push to main (no-push rule → needs explicit approval) or a
  Vercel token for CLI deploy. Full-chain WS7 acceptance re-measure (browser →
  Vercel /api/narrate-stream → App Runner) is gated on that. JSON fallback keeps
  the UI correct in the interim.

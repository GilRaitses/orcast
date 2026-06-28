# WS3 discovery map (App Runner streamed narration)

WS3 Discovery deliverable. Three read-only investigators (D1 frontend
reachability, D2 backend endpoint placement, D3 convergence + invariants).
Read-only; no code edited. Grounds the WS2-chosen method — serve streamed
narration from App Runner (Cloudflare-free) — in the codebase: how the browser
reaches it, where the endpoint lives, the one-file-one-owner map, and the honesty
invariants. WS4 is gated on operator approval.

Chosen method (WS2): App Runner SSE lane, Cloudflare-free. App Runner streams
incrementally (first token ~0.5-0.6 s); the cloudflared/`aimez.ai` edge buffers SSE.

## 1. Deploy topology — same code, two surfaces

- The SAME FastAPI app (`uvicorn src.aws_backend.main:app`) runs on BOTH surfaces:
  App Runner (ECR container, port 8080, `tools/deployment/aws/Dockerfile:20`) and
  the cloudflared host (systemd, port 8090, `infra/shared_host/systemd/orcast-api.service:12`).
- `main.py:71-90` registers all routers unconditionally; there is NO deploy-specific
  route gating, and `config.py` has NO deploy-mode flag (only generic `ORCAST_*`/`AWS_REGION`).
- Today (DD-1): browser API traffic goes Vercel `/api/be` -> `ORCAST_API_BASE`
  (`https://orcast-api.aimez.ai`) -> cloudflared -> `:8090`. App Runner
  (`pjrftm3bkv.us-west-2.awsapprunner.com`) is the rollback service AND is still
  called by internal EventBridge/Step Functions Lambdas as `BACKEND_URL`
  (`infra/aws/template.yaml` ~752, ~809, ~965, ~1006, ~1071). Region us-west-2,
  account 198456344617.
- App Runner is built via `tools/deployment/aws/Dockerfile` -> ECR `orcast-aws-backend`
  (tag = git SHA) -> `aws cloudformation deploy infra/aws/template.yaml`
  (`AppRunnerService` at `template.yaml:596-725`, `AutoDeploymentsEnabled: true`).
  CI is `.github/workflows/aws-deploy.yml` (`workflow_dispatch` only).

**Dual-serve answer:** the stream route is the SAME shared code on both deploys; it
needs App Runner specifically only for TRANSPORT (App Runner streams, Cloudflare
buffers). Routing is CLIENT/ENV-side, not a backend route fork. There is no
`ORCAST_STREAM_API_BASE` today; WS4 must introduce a way to point the narration
stream lane at the App Runner URL while the rest of the API stays on cloudflared.

## 2. Frontend reachability (D1) — browser CANNOT reach App Runner directly today

CORS (`src/aws_backend/main.py:59-69`, `config.py:51-73`): `ORCAST_CORS_ORIGINS`
defaults to `"*"` (then `allow_credentials=false`); `allow_methods=["*"]`,
`allow_headers=["*"]`. BUT the SAM parameter default omits `orcast-h0.vercel.app`
(`infra/aws/template.yaml:22-24`) while the shared-host example includes it
(`infra/shared_host/env/orcast-services.env.example:14`) — so whether Vercel can
call App Runner cross-origin depends on the LIVE `ORCAST_CORS_ORIGINS` on the
rollback service, currently unknown.

Hard blockers to direct browser->App Runner streaming, all in code today:

| Blocker | Evidence |
|---------|----------|
| narrate not public -> anonymous 401 at proxy | `route.ts:59-69` (only `plan` public); client calls narrate `adaptiveConsole.ts:135` |
| proxy buffers full body | `route.ts:175-180` `await resp.text()` |
| backend requires `X-ORCAST-Key` | `interactions.py:274`, `auth.py:14-25` |
| no stream endpoint in backend | no `StreamingResponse`/`narrate/stream` in `src/` |
| no browser App Runner URL | `ORCAST_API_BASE` is server-only; no `NEXT_PUBLIC_*` App Runner var in `web/` |
| CORS may exclude Vercel in prod | SAM default omits `orcast-h0.vercel.app` |

Auth options for an App Runner stream (key must NOT ship to the browser):

| Option | Mechanism | Posture | Vercel buffering risk |
|--------|-----------|---------|----------------------|
| (a) public session-scoped stream on App Runner | drop/bypass `require_api_key`, mirror anonymous-first `plan` `public_route` posture; add proxy allow-list; tight rate limits + session quotas | weakest auth; Bedrock cost-abuse exposure on a public stream | none (browser -> App Runner direct) |
| (b) short-lived stream token | Vercel mints HMAC/JWT bound to session_id + expiry; backend validates instead of static key | better; key off-browser, narrow + time-boxed; needs mint+validate | none on stream leg |
| (c) streaming Vercel route -> App Runner | new same-origin route injects `X-ORCAST-Key`, `return new Response(resp.body, …)` (pattern in `ws2_probes/next_stream_route_candidate.ts`) | strongest key hygiene, same model as today | YES — Vercel platform streaming unproven; must benchmark on the WS4 preview |

Client change (`adaptiveConsole.ts:114-145`): add a streaming variant using
`fetch` + `res.body.getReader()` + `TextDecoder` (NOT `EventSource`; narrate is
POST with a large body); keep `runAdaptiveNarration` JSON as fallback. App Runner
base would come from a new env var (server `ORCAST_STREAM_API_BASE` for shape (c),
or a `NEXT_PUBLIC_*` for shapes (a)/(b)) — none exists today.

## 3. Backend endpoint seams (D2)

| Piece | File | Seam |
|-------|------|------|
| `_bedrock_guide_stream` generator | `src/aws_backend/exploration/guide.py` | sibling after `_bedrock_guide` (~`:201`); same client/region/model/body as `:184-196` but `invoke_model_with_response_stream`; iterate `response["body"]`, emit on `content_block_delta` + `delta.type=="text_delta"` -> `delta.text`; sync `def` generator (threadpool) |
| SSE route | `src/aws_backend/routers/interactions.py` | new `POST /api/interactions/narrate/stream` adjacent to `:274-343` (dedicated route preferred over `Accept` negotiation); reuse `NarrateRequest` `:254-272` + agent resolution `:289-299`; framing `meta` -> `token`xN -> `done`/`error`; `StreamingResponse(..., media_type="text/event-stream", headers=SSE_HEADERS)` |
| meta payload | same route | `interaction_id` + prefetched `{citations, deep_links, tools_used, gate_ids, provenance_refs}` (from plan, `interactions.py:300-307`, `guide.py:120-128`) + `source`/`model`, emitted BEFORE first token |
| persistence | route generator tail | accumulate deltas; on Bedrock `message_stop` build `GuideReply` and call `save_interaction_exchange` ONCE (`:318-331`, `session_store.py:153-189`); on abort/error persist NOTHING |

Keep `_bedrock_guide` and the sync `/narrate` (`:274-343`) untouched as the fallback.

## 4. IAM

Add `bedrock:InvokeModelWithResponseStream` alongside `bedrock:InvokeModel` on the
same ARNs. For the chosen App Runner lane, the IAM gate that strictly matters is
**`AppRunnerInstanceRole`** (`infra/aws/template.yaml:258-265`, applied via
`deploy.sh`/CFN). The cloudflared host policy
(`infra/shared_host/iam/orcast_host_policy.json:44-53`, role `aimez-host-role`,
applied via `aws iam put-role-policy`) is parity/rollback hygiene unless stream
traffic is ever routed there. Operator-applied ops task (`wave_shape.yml:48,116`).

## 5. Convergence files (single phase-B editor) — change table

| Convergence file | WS4 change (seam) | Why convergence |
|------------------|-------------------|-----------------|
| `src/aws_backend/routers/interactions.py` | add `POST /api/interactions/narrate/stream` after `:274-343`; SSE meta/token/done/error; persist once on `done`; keep JSON `/narrate` | owns narrate contract, prefetched wiring `:300-316`, atomic persistence |
| `web/app/api/be/[...path]/route.ts` | `:175-180` conditional `new Response(resp.body, …)` with SSE headers for stream paths; `:59-69` add `api/interactions/narrate` (+`/stream`) to public allow-list; `:97-104` optional narrate rate-limit; `:18` optional `runtime="nodejs"`/`maxDuration` | all browser->backend traffic; confirmed buffer + allow-list gap |
| `web/lib/adaptiveConsole.ts` | `:114-145` add `runAdaptiveNarrationStream(..., {onToken,onMeta,signal})` reader; keep `runAdaptiveNarration` JSON as fallback; Phase 1 `runAdaptiveTurn` `:77-102` unchanged | sole turn driver; owns the two-phase split |
| `web/app/components/AdaptiveExplore.tsx` | `runTurn` `:102-160` swap blocking narrate for stream + rAF-batched `setTurns` append, fallback on buffer/fail/timeout; `renderReply` `:52-68` defer markdown to stream end; `:308-312` partial prose; add `turnGenRef` + `AbortController` | owns turn UX, pending bubble, panels-first orchestration |

Panels-first (`fd50929`) precise structure to NOT regress: Phase 1
`runAdaptiveTurn` with `narrate:false` (`adaptiveConsole.ts:91`) -> `setPlan`
(`AdaptiveExplore.tsx:120`) -> `setBusy(false)` (`:136`) BEFORE Phase 2; streaming
attaches to Phase 2 ONLY. `ActiveSurfaceHost.tsx` renders citations/deep_links/
provenance from `plan.prepare`/`uiIntent` (`:276-336`, badges `:121-138`, chips
`:365-378`), never from the narration bubble — do NOT edit it.

## 6. Phase-A producers (new sibling code, parallel-safe)

| Producer | Location | Owner |
|----------|----------|-------|
| Bedrock stream generator | `src/aws_backend/exploration/guide.py` (sibling to `:172-201`) | WS4-A-backend |
| transport-client module (NEW) | e.g. `web/lib/sseTransport.ts` (no file today) — opaque `fetch`+`getReader()`+frame parse+`AbortSignal`, no narrate semantics | WS4-A-transport |
| probe->real promotion | promote `ws2_probes` framing/headers into a real backend helper + optional Phase-A sibling route `web/app/api/stream/narrate/route.ts` (App Runner upstream, `resp.body` passthrough) | WS4-A-probe |

## 7. One-file-one-owner map (every WS4 touch)

| File / artifact | Phase | Convergence? | Owner |
|-----------------|-------|--------------|-------|
| `src/aws_backend/exploration/guide.py` | A | no | WS4-A-backend |
| `web/lib/sseTransport.ts` (NEW) | A | no | WS4-A-transport |
| `web/app/api/stream/narrate/route.ts` (NEW, if shape c) | A | no | WS4-A-probe |
| `src/aws_backend/routers/interactions.py` | B | YES | WS4-B (single serialized editor) |
| `web/app/api/be/[...path]/route.ts` | B | YES | WS4-B |
| `web/lib/adaptiveConsole.ts` | B | YES | WS4-B |
| `web/app/components/AdaptiveExplore.tsx` | B | YES | WS4-B |
| `tests/aws_backend/test_interactions_plan.py` (+ stream fixture tests) | B | no | WS4-B |
| `infra/aws/template.yaml:258-265` (App Runner role IAM) | ops | no | Operator |
| `infra/shared_host/iam/orcast_host_policy.json:44-53` | ops | no | Operator (parity) |
| proxy public allow-list (`route.ts:59-69`) | B | via convergence | WS4-B implements; operator approves (`wave_shape.yml:122-123`) |
| `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts` | — | no | NO WS4 edit |

## 8. Honesty / behavior invariants (must stay byte-identical)

| # | Invariant | Grounding |
|---|-----------|-----------|
| H1 | narration is prose only in the bubble | `AdaptiveExplore.tsx:52-68` `renderReply`; defer markdown parse to stream end |
| H2 | labels/citations/deep_links/provenance from prefetched PLAN, arrive in `meta` | `interactions.py:140-148` -> `adaptiveConsole.ts:120-134` -> `interactions.py:300-307` -> `guide.py:120-128`; render `ActiveSurfaceHost.tsx:276-336` |
| H3 | non-streamed `/narrate` JSON stays as fallback | `interactions.py:274-343`, `adaptiveConsole.ts:114-145`, `AdaptiveExplore.tsx:147-152` |
| H4 | persistence: ONE atomic exchange at stream end | `interactions.py:318-331`, `session_store.py:153-189`, test `test_interactions_plan.py:175-176` |
| H5 | never a partial DB turn on abort/error | persist nothing before `done`; best-effort try/except `:332-333` |
| H6 | buffered/failed stream -> fallback, never hang | client detects burst/timeout/mid-stream error -> `runAdaptiveNarration`; clear `pending`; `AbortController` on new message |
| H7 | panels-first split preserved | Phase 1 unchanged; streaming attaches to Phase 2 only |

## 9. Reusable-transport boundary (size-only, deferred)

In scope for WS4: the transport edge only — a browser module owning pass-through
reading + abort guards, and a backend helper owning framed `StreamingResponse`
(headers, anti-buffering, sync generator in threadpool). Deferred: subscription
fan-out, connection-delta JSON, acoustic envelopes, progressive whole-turn
multiplex. Consumer semantics stay in existing owners. R4 sized future consumers
(ferry push High, whole-turn Medium, hydrophone Medium); none are WS4 tasks.

## 10. WS3 gate verdict

Gate (from `wave_shape.yml`): the chosen method grounded in the codebase —
files/owners/seams, the reusable transport module boundary, convergence files
named, honesty invariants listed.

**PASS.** Reasons:
- Deploy topology resolved: same code on both surfaces; the stream lane needs App
  Runner for transport only; routing is client/env-side (a new stream-base env is
  required, none exists today) — §1.
- Browser reachability grounded: direct App Runner is NOT possible today (auth,
  key, CORS, no stream endpoint, no browser URL); three auth shapes enumerated
  with the cleanest = dedicated streaming Vercel route to App Runner — §2.
- Backend seams located to file:line; meta/persistence/threadpool specified — §3.
- IAM gate identified (App Runner instance role) — §4.
- Four convergence files named with seams + single phase-B editor; phase-A
  producers located; full one-file-one-owner map — §5-7.
- Honesty invariants enumerated and grounded — §8.

## 11. Biggest open risk for WS4

The browser-reach shape is unsettled and is the gating risk. The cleanest shape
(c) — a dedicated streaming Vercel route that injects the key and passes
`resp.body` through to App Runner — keeps the API key off the browser and avoids
CORS churn, but reintroduces Vercel as a potential buffering layer that WS2 never
measured (Step 3 was skipped). If Vercel re-buffers, the fallback is shape (a)/(b)
direct browser->App Runner, which trades the proxy unknown for a CORS config
change plus a public/token auth surface and Bedrock cost-abuse exposure. This
should be settled FIRST in WS4 by measuring the dedicated Vercel stream route
against the App Runner upstream on a throwaway preview, before building the full
Bedrock streaming endpoint and progressive UI.

## 12. STOP

WS3 complete (PASS). WS4 Implementation is gated on operator approval via O0.

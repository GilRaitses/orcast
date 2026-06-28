# WS5 defect register (adversarial review of the WS4 streamed-narration diffs)

Independent adversarial review. The reviewer did not build this code. Scope is
the uncommitted WS4 diffs only. No code was edited, deployed, committed, or
pushed. This file is the only artifact written.

Rubric: `wave_shape.yml` `waves[WS5].adversarial.layers` L1-L5 and the `targets`
table. Measured-good shape is `WS2_O0_MEASUREMENTS.md` and `BENCHMARK_REPORT.md`
(App Runner streams unbuffered; the cloudflared/`aimez.ai` edge buffers). Prod
re-measurement is a WS7 task; here L1 verifies the CODE matches the measured-good
shape.

Diffs reviewed in full: `src/aws_backend/exploration/guide.py`,
`src/aws_backend/routers/interactions.py`, `web/lib/sseTransport.ts`,
`web/app/api/narrate-stream/route.ts`, `web/lib/adaptiveConsole.ts`,
`web/app/components/AdaptiveExplore.tsx`,
`tests/aws_backend/test_interactions_stream.py`, `web/.env.example`. Cross-read
for context (not in the diff set): `web/app/api/be/[...path]/route.ts`,
`src/aws_backend/auth.py`, `src/aws_backend/exploration/limits.py`,
`src/aws_backend/exploration/session_store.py`, `src/aws_backend/config.py`.

## Per-layer verdict

| Layer | Dimension | Verdict |
|-------|-----------|---------|
| L1 | transport-robustness | PASS (code matches measured-good shape; prod re-measure is WS7) |
| L2 | correctness-honesty | PASS |
| L3 | failure-fallback | WS6 RESOLVED (anonymous fallback allow-listed; first-token/idle stall timeout + fallback; EOF-without-done → fallback; client contract unit-tested) |
| L4 | frontend-visual-perf | WS6 RESOLVED (stale pending bubble cleared on supersede) |
| L5 | load-concurrency + abuse | WS6 RESOLVED (per-IP rate+concurrency bucket; backend turn quota; bounded concurrent streams + per-stream wall-clock cap) |

## Findings

| ID | Layer | Severity | File:line | Defect | Fix |
|----|-------|----------|-----------|--------|-----|
| B1 | L5 | blocking | `web/app/api/narrate-stream/route.ts:25-48`; `src/aws_backend/routers/interactions.py:456-490` | OPEN Bedrock-cost surface. The dedicated route injects `X-ORCAST-Key` unconditionally and has NO auth, NO per-IP bucket, NO session/turn quota. It bypasses the generic `/api/be` proxy entirely, so none of the `/api/be` rate limits apply. The backend `narrate/stream` route never calls `assert_turn_quota` (only `create_interaction` does); `session_exists` is the only gate and an anonymous session is trivially minted via `api/explore/sessions`. Anyone can POST and drive `invoke_model_with_response_stream` without bound. | Add a per-IP rate bucket and a session-scoped turn quota in `route.ts` BEFORE injecting the key (mirror the `explorePathLimit` buckets in `web/app/api/be/[...path]/route.ts:97-104`), and call `assert_turn_quota(payload.session_id)` in `narrate_cast_interaction_stream` before streaming. Cap concurrent streams per IP/session. WS6 must close this before any public deploy. |
| M1 | L3 | major | `web/app/api/be/[...path]/route.ts:59-70`; `web/lib/adaptiveConsole.ts:136` | Anonymous JSON fallback is unreachable. `isPublicRequest` allow-lists `plan`, `prepare`, `interactions`, `sessions`, `turn`, but NOT `api/interactions/narrate`. The fallback `runAdaptiveNarration` posts to `/api/be/api/interactions/narrate`, which returns 401 for anonymous users, so the L3 "fall back to /narrate, never hang" guarantee fails for the primary anonymous audience. The dedicated stream works anonymously while the safer fallback does not. `route.ts` was NOT edited in WS4. | Add `if (method === "POST" && path === "api/interactions/narrate") return true;` to `isPublicRequest`, plus an `explorePathLimit` bucket for it. This is the operator gate already named in `wave_shape.yml` operator_gates. |
| M2 | L3 | major | `web/lib/sseTransport.ts:54-115`; `web/app/components/AdaptiveExplore.tsx:178-207` | No client stall/idle timeout. `readSseStream` reads until EOF/error with no first-token or idle deadline. If the stream stalls (App Runner cold start, network black hole, edge holds the response open) the bubble stays on "Narrating…" indefinitely, violating "never hang". `DISCOVERY_MAP.md` H6 promised burst/timeout detection; it is not implemented. | Add a first-token deadline and an inter-token idle deadline (timer that calls `controller.abort()` then routes to the JSON fallback). On the no-first-token case, fall back rather than wait. |
| M3 | L5 | major | `src/aws_backend/routers/interactions.py:354-490`; `src/aws_backend/exploration/guide.py:204-248` | Threadpool exhaustion under concurrency. The sync generator is correctly offloaded by Starlette, but each `next()` blocks an AnyIO threadpool thread while boto3 waits for the next chunk. The default limiter (~40 threads) is shared with ALL sync routes and sync DB calls (`session_exists`, `save_interaction_exchange`). Many concurrent ~5.5s streams can saturate the shared pool and stall unrelated sync endpoints. | Bound concurrent streams (semaphore per process), raise/segregate the AnyIO thread limiter for the stream path, or move to an async generator backed by a bounded executor. Add an explicit per-stream wall-clock bound on the backend (do not rely only on the Vercel `maxDuration=60`). |
| m1 | L4 | minor | `web/app/components/AdaptiveExplore.tsx:113-117,193-197` | A superseded turn's assistant bubble is left permanently "Narrating…". When a new message aborts the prior stream, the `myGen` guard returns before `finalize`, so the old assistant turn never clears `pending`. The stale bubble persists until it scrolls out of `slice(-6)`. | On abort/supersede, finalize the prior `assistantId` (clear `pending`, set a terminal label such as superseded) before bumping the generation. |
| m2 | L3 | minor | `web/lib/sseTransport.ts:76-107`; `web/app/components/AdaptiveExplore.tsx:194` | EOF-without-`done` resolves as success. A clean transport close after some tokens but before the `done`/`error` frame makes `readSseStream` resolve normally with partial/empty `acc`; `finalize(nar.reply || acc || "(no narration)")` then shows a truncated reply or "(no narration)" instead of falling back to JSON. | Treat a stream that ends without a terminal `done` (when Bedrock output was expected) as an error so the JSON fallback fires. |
| m3 | L1 | minor | `web/app/api/narrate-stream/route.ts:50-59` | No explicit compression/transform disable beyond `no-transform`; correctness relies on the measured-good shape rather than an asserted `Content-Encoding: identity`. Acceptable because WS2 step-0 measured this exact route shape as unbuffered. | Confirm in the WS7 prod re-measure that Vercel does not gzip `text/event-stream`; optionally set `Content-Encoding: identity`. |
| m4 | L2 | minor (info) | `src/aws_backend/routers/interactions.py:380-389` | The `meta` event emits `source:"bedrock"` provisionally before generation. On a mid-stream Bedrock failure the true source becomes template via fallback. Not user-visible today (the UI renders provenance from `plan.prepare` and discards the stream's `source`/`model`), so no honesty leakage now, but a future `meta`-reading consumer could mislabel. | Either omit `source` from `meta` and emit it only in `done`, or document that `meta.source` is provisional. |
| m5 | L3 | minor (pre-existing) | `src/aws_backend/exploration/session_store.py:167-178` | `save_interaction_exchange` is two separate `append_turn` calls, not one atomic transaction. H4's "one atomic exchange" claim is aspirational. A failure between the two appends leaves a user turn with no assistant turn. Pre-existing and shared with the JSON path; the stream wraps it best-effort. | Out of WS-STREAM scope; note for a later durability pass. |

## WS6 remediation status (diffs only; nothing deployed/committed/pushed)

All blocking + major defects RESOLVED. The two recommended minors (m1, m2) were
also closed because they are part of the same never-hang contract. Validation:
`web` `tsc --noEmit` clean; `pytest tests/aws_backend` 323 passed; transport
contract `node --test lib/sseTransport.test.mts` 5 passed.

| ID | Severity | Status | Fix (file:line, commit-free) |
|----|----------|--------|------------------------------|
| B1 | blocking | RESOLVED | Per-IP rate bucket + per-IP concurrent-stream cap BEFORE key injection: `web/app/api/narrate-stream/route.ts:27-44,62-126`. Backend per-session turn quota on the stream route: `src/aws_backend/routers/interactions.py:498-503` (`assert_turn_quota` → HTTP 429, mirrors the JSON narrate posture). New knobs: `ORCAST_STREAM_RATE_PER_MIN` (12/min), `ORCAST_STREAM_MAX_CONCURRENT_PER_IP` (3). |
| M1 | major | RESOLVED | `api/interactions/narrate` added to the `/api/be` public allow-list: `web/app/api/be/[...path]/route.ts:71`; matching `explorePathLimit` bucket (EXPLORE_TURN_LIMIT): `web/app/api/be/[...path]/route.ts:106`. Anonymous JSON fallback now reaches the backend. |
| M2 | major | RESOLVED | First-token + inter-token idle deadlines that abort an internal controller and throw `SseStallError` (caller's signal left un-aborted so it falls back, not gives up): `web/lib/sseTransport.ts:24-42,85-176`. Component already falls back to JSON on any non-user-abort rejection: `web/app/components/AdaptiveExplore.tsx:200-216`. Stall → fallback, never hangs in "Narrating…". |
| M3 | major | RESOLVED | Bounded concurrent backend streams via a process `BoundedSemaphore` (busy → `error` frame → client fallback): `src/aws_backend/routers/interactions.py:30-35,381-384,477-478`. Per-stream wall-clock cap independent of the Vercel `maxDuration`: `interactions.py:415-420`. Bound = `ORCAST_STREAM_MAX_CONCURRENT` (8), cap = `ORCAST_STREAM_MAX_SECONDS` (30s): `src/aws_backend/config.py:56,59`. |
| Test gap (L3) | — | RESOLVED (unit) | Backend: turn-quota 429, concurrency-busy, wall-clock-cap, plus the existing persist-once/no-persist-on-error: `tests/aws_backend/test_interactions_stream.py`. Client: stall→SseStallError (signal un-aborted), error-frame→reject, EOF-without-done→reject, user-abort→reject (signal aborted, distinct from stall), normal done→resolve: `web/lib/sseTransport.test.mts`. No browser/DOM runner is wired (only Playwright e2e, which needs a live server + Bedrock); the component's `runTurn` fallback branch is exercised only by inspection + the transport-level contract above. |
| m1 | minor | RESOLVED | Superseded turn's "Narrating…" cleared on the next turn via `pendingAssistantRef`: `web/app/components/AdaptiveExplore.tsx:88-92,117-128,150,185`. |
| m2 | minor | RESOLVED | EOF before a terminal `done` now throws so the JSON fallback fires instead of showing truncated/empty prose: `web/lib/sseTransport.ts:188-192`. |
| m3 | minor | DEFERRED to WS7 | `Content-Encoding: identity` assertion deferred to the WS7 prod re-measure; WS2 step-0 measured this exact route shape unbuffered, so no code change now. |
| m4 | minor (info) | DEFERRED | `meta.source="bedrock"` is provisional; not user-visible today (UI renders provenance from `plan.prepare`, discards the stream's source/model). Noted for a future meta-reading consumer; no change. |
| m5 | minor (pre-existing) | DEFERRED (out of scope) | `save_interaction_exchange` two-append non-atomicity is pre-existing and shared with the JSON path; flagged for a later durability pass. |

## Deploy / ops checklist cross-check

| Item | State | Note |
|------|-------|------|
| App Runner deploy of the stream route | code shared on both surfaces | stream needs App Runner for transport only; routing is env-side via `ORCAST_STREAM_BASE` |
| `ORCAST_STREAM_BASE` on Vercel | required, documented in `web/.env.example` | must point at the App Runner URL, NOT the cloudflared host |
| `ORCAST_ENABLE_BEDROCK=true` on App Runner | GAP to verify | `config.py:34` defaults false; if false the stream silently degrades to template-as-one-token (no real streaming, `meta.source=null`) |
| IAM `bedrock:InvokeModelWithResponseStream` | ops task | add on `AppRunnerInstanceRole` alongside `bedrock:InvokeModel` (`DISCOVERY_MAP.md` §4) |
| narrate JSON-fallback allow-list | WS6 RESOLVED (in-code) | M1 closed: `api/interactions/narrate` now public in `web/app/api/be/[...path]/route.ts:71` + rate bucket `:106`. No ops step. |
| anonymous-reach guard on `/api/narrate-stream` | WS6 RESOLVED (in-code) | B1 closed: per-IP rate+concurrency in `narrate-stream/route.ts`; backend turn quota in `interactions.py`. Knobs: `ORCAST_STREAM_RATE_PER_MIN`, `ORCAST_STREAM_MAX_CONCURRENT_PER_IP`, `ORCAST_STREAM_MAX_CONCURRENT`, `ORCAST_STREAM_MAX_SECONDS`. |
| CORS for the stream | moot | shape (c) calls App Runner server-side from the Vercel route; no browser cross-origin |

## Layer detail

### L1 transport-robustness — PASS
`web/app/api/narrate-stream/route.ts` matches the WS2 step-0 measured-good shape:
`runtime="nodejs"`, `dynamic="force-dynamic"`, `maxDuration=60` (ample for a
~5.5s reply), `return new Response(resp.body, ...)` passthrough with no
`resp.text()`/`resp.json()` anywhere on the stream body, `Cache-Control:
no-cache, no-transform`, `X-Accel-Buffering: no`, and content-type passthrough.
Backend `StreamingResponse` (`interactions.py:482-490`) carries the same
anti-buffer headers and `media_type="text/event-stream"`. Request body is read
once with `await req.text()` (small body, fine). Upstream non-200 passes through
with its real status so the client treats it as a failure. Minor m3 only.

### L2 correctness-honesty — PASS
`meta` (`interactions.py:380-389`) carries `citations`/`deep_links` straight from
`payload.*` (the prefetched plan, not re-derived) and `model` from the resolved
agent; `done` (`:453`) carries `reply`/`source`/`model`. The JSON `/narrate`
response (`:338-346`) returns the same prefetched `citations`/`deep_links` (via
`compose_guide_reply(prefetched=...)`), so the honesty fields are byte-identical
across paths. Streamed content is prose-only (text deltas), and the UI defers
markdown to stream end, so H1 holds. `gate_ids`/`provenance_refs`/`tools_used`
are omitted from both `meta` and the JSON response symmetrically and rendered
from `plan.prepare` by `ActiveSurfaceHost`. Test asserts the prefetched metadata
rides `meta` (`test_interactions_stream.py:126-133`). Only the informational m4
note applies.

### L3 failure-fallback — FAIL
Backend honesty is correct and tested: mid-stream exception emits an `error`
frame and persists nothing (`interactions.py:422-425`;
`test_interactions_stream.py:149-198` asserts `event: error`, no `event: done`,
`save_interaction_exchange.call_count == 0`); success persists exactly once
before `done` (`:437-453`; test asserts `call_count == 1`). Pre-stream errors
(aurora/session) raise before `StreamingResponse` and pass through as non-200 so
the client throws and falls back. Client abort is handled
(`AdaptiveExplore.tsx:197` returns without fallback on a superseded/aborted
turn), and a GC'd generator raises `GeneratorExit` (a `BaseException` not caught
by the `except Exception`), so an aborted stream persists nothing.

It FAILS on three counts: M1 (anonymous JSON fallback 401s, so the fallback the
whole layer depends on is unreachable for the primary audience), M2 (no stall
timeout, so a silently stalled stream hangs in "Narrating…"), and m2
(EOF-without-`done` shows a truncated reply instead of falling back).

Do the tests genuinely cover L3? PARTIALLY. They cover the BACKEND
persistence-honesty (persist-once on success, no-persist on mid-stream error,
auth required, delta parsing). They do NOT cover the CLIENT contract that L3 is
mostly about: fall-back-to-JSON, never-hang, exactly-once across stream+fallback,
the anonymous allow-list path, or no-persist on disconnect/abort. There is no
frontend test in the diff. So L3 is not genuinely covered end to end.

### L4 frontend-visual-perf — PASS with one minor
Progressive render is correct: functional `setTurns` append
(`AdaptiveExplore.tsx:135-139`), rAF-batched updates via a single in-flight
`raf` token (`:157-166,188`), `pending->false` on first flush (`:163`), markdown
deferred during `streaming` (plain `white-space: pre-wrap` at `:367-369`,
`renderReply` only at stream end `:371`), so partial `**`/`[]()` never
half-render (H1). The turn-generation guard (`turnGenRef` + `AbortController`,
`:113-117`) is checked in `onToken`, `flush`, the success path, and both catch
branches (`:159,185,193,197,201,204`), so a mid-stream new message aborts the
prior stream and no stale `assistantId` writes land. No auto-scroll logic, so no
scroll thrash. Only m1 (stale "Narrating…" bubble on the superseded turn).

### L5 load-concurrency + abuse — FAIL
The sync boto3 generator is correctly offloaded (sync `def` generator under
`StreamingResponse`, documented at `guide.py:204-216` and
`interactions.py:354-369`), so the event loop is not blocked. But the layer fails
on B1 (open, unauthenticated, unrate-limited Bedrock-cost surface; the stream
route bypasses every `/api/be` guard and the backend stream route has no turn
quota) and M3 (the offloaded generator holds shared-threadpool threads across
chunk waits; concurrent long-lived streams can starve the pool shared with sync
DB work). Backend per-stream timeout is unbounded; only the Vercel
`maxDuration=60` bounds the leg.

## WS5 gate verdict

Gate (from `wave_shape.yml`): "all non-optional layers run and filed; register
complete + triaged."

**Gate PASS as a process gate** — all five layers ran and are filed with
severity, `file:line`, and a concrete fix; the register is complete and triaged.

**The reviewed artifact is NOT acceptance-ready.** WS-STREAM carries 1 blocking
and 3 major defects. WS7 acceptance must not proceed until WS6 closes:

1. B1 — anonymous-reach guard (rate-limit + session/turn quota) on
   `/api/narrate-stream` and `narrate/stream`. BLOCKING before any public deploy.
2. M1 — add `api/interactions/narrate` to the `/api/be` public allow-list so the
   anonymous JSON fallback actually works.
3. M2 — client first-token/idle timeout that aborts and falls back, so a stalled
   stream never hangs.
4. M3 — bound stream concurrency / segregate the threadpool / bound the backend
   per-stream timeout.

Recommended also: m1 (clear the superseded bubble), m2 (treat EOF-without-`done`
as a failure), and the ops verifications (`ORCAST_ENABLE_BEDROCK=true` on App
Runner, IAM `InvokeModelWithResponseStream`, `ORCAST_STREAM_BASE` set).

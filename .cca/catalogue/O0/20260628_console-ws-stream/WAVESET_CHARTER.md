# WS-STREAM: real-time streaming transport waveset charter

## 0. How to use this charter

WS-STREAM graduates the WS-PERF T4 track into a full waveset because the risk is
the transport chain, not the narration code. It runs a seven-wave lifecycle:
the program's standard six plus a dedicated **Benchmark** wave between Research
and Discovery, because the transport must be measured empirically before a method
is chosen. Read this charter, then `wave_shape.yml` for the machine shape
(per-wave subagent counts, candidate methods, flags, adversarial layers,
numeric targets). The program orchestrator (O0) launches one wave at a time and
synthesizes into `STEP_LOG.md`. Do not start a wave whose entry gate is unmet.

## 1. The problem and the higher-reward framing

The WS-PERF T4 research proved the backend and frontend changes are easy and the
transport chain is the unknown. WS-STREAM treats the answer as a reusable
capability: a proven unbuffered real-time channel plus a server streaming
pattern. Streamed narration is consumer #1. The Research wave sizes (without
committing to) future consumers (progressive whole-turn, live connection refresh,
hydrophone push) so the transport investment is justified beyond one feature.

The ten flags to clear are enumerated in `wave_shape.yml` `flags` (proxy
buffering, Vercel/Cloudflare edge buffering, uvicorn streaming, narrate
allow-list, topology drift, EventSource limits, missing AbortController, IAM,
persistence-at-end).

## 2. The waves (parameterized in wave_shape.yml)

### WS1 Research (parallelism 4, read-only)

One researcher per area. Output `RESEARCH_SYNTHESIS.md`.

| Researcher | Question |
|------------|----------|
| R1 transport methods | Compare the `candidate_methods`: SSE pass-through, dedicated stream route, direct-backend-domain bypass, chunked NDJSON, WebSocket, platform response streaming. Name the config that defeats buffering at each layer. |
| R2 platform buffering | Vercel streaming limits + runtime; Cloudflare/cloudflared SSE buffering and the headers/flags that disable it; uvicorn `StreamingResponse`. |
| R3 backend streaming | `invoke_model_with_response_stream` chunk parsing; persistence-at-end; IAM; the narrate auth/allow-list gap. |
| R4 higher-reward reuse | What a reusable realtime channel unlocks; the abstraction boundary; the reward sizing. |

Gate: each candidate method has named techniques + the specific anti-buffering
config per chain layer; R4 sizes the reward.

### WS2 Benchmark (parallelism 3, measure-only) — the added wave

One prober per top candidate. Stand up throwaway probes (a trivial stream
endpoint + a stream route) and MEASURE whether tokens arrive incrementally
through the full prod chain, with first-token latency per method. Output
`BENCHMARK_REPORT.md` with a per-layer buffering map.

Gate: at least one method PROVEN to stream incrementally end-to-end with a
measured first-token latency. If none stream, report which layer buffered and
STOP (do not build).

### WS3 Discovery (parallelism 3, read-only)

Ground the chosen method in the codebase: files, owners, the reusable transport
module boundary, the convergence files, and the honesty invariants that must stay
byte-identical. Output `DISCOVERY_MAP.md`.

### WS4 Implementation (phase-A 3, phase-B 1)

- Phase A: backend stream generator in `guide.py`, the transport-client module,
  promotion of the proven probe into real code.
- Phase B (single serialized editor): `interactions.py` stream endpoint, the
  `/api/be` pass-through + narrate allow-list, `adaptiveConsole.ts` reader, and
  `AdaptiveExplore.tsx` progressive render + abort. Must not regress the
  panels-first split (`fd50929`).

Gate: type-checks/tests green; narration renders progressively in a local run;
the non-streamed fallback is intact.

### WS5 Adversarial (parallelism = active layers)

A reviewer that did not build it runs each layer (the pre-acceptance gate):

| Layer | Dimension | Check |
|-------|-----------|-------|
| L1 | transport-robustness | Re-measure first-token on the prod chain; tokens still incremental; no buffering regression. |
| L2 | correctness-honesty | Labels/citations/deep_links/provenance byte-identical; the `meta` event matches the prefetched plan. |
| L3 | failure-fallback | Buffered / throttled / mid-stream-error / disconnect all fall back to non-streamed `/narrate`, never hang; no partial DB turn. |
| L4 | frontend-visual-perf | Progressive render has no markdown flicker or scroll thrash; a mid-stream new message aborts cleanly (read the rendered output). |
| L5 | load-concurrency | Many concurrent long-lived streams do not exhaust workers; the sync-boto3 generator is offloaded; timeouts bounded. |

Gate: defect register complete and triaged.

### WS6 Remediation (parallelism 4, serialized on convergence files)

Fix filed defects by owner, highest severity first. Gate: every blocking and
major defect closed or deferred with operator sign-off.

### WS7 Acceptance (parallelism 1, orchestrator signs off)

Verify against the `targets` table: measured first-token on the prod chain, a
visual check of progressive render, and a fallback drill. Gate: targets met and
recorded; honesty unchanged; fallback proven.

## 3. Acceptance criteria (the numbers)

- First token: full ~5.5 s reply -> <= 1.5 s first token, MEASURED on the prod
  chain (not synthetic).
- Tokens arrive incrementally through `Vercel -> Next -> cloudflared -> uvicorn`.
- Any buffered or failed stream falls back to the non-streamed `/narrate`, never
  hangs.
- Labels / citations / deep_links / provenance byte-identical to panels-first.

## 4. Collision governance

See `wave_shape.yml` `collision_governance`. The four convergence files have a
single phase-B editor; `guide.py` and the transport module are phase-A producers;
WS2 probes are throwaway; producers commit/deploy/promote nothing; the IAM change
is operator-applied.

## 5. Operator decisions before fan-out

1. Confirm WS-STREAM scope (streamed narration as consumer #1 of a reusable
   transport).
2. Approve the WS2 benchmark probes touching prod (Vercel preview + the
   cloudflared backend), throwaway and not user-facing.
3. Decide how far R4 higher-reward reuse is in scope now vs documented-for-later.
4. Confirm or override the 1.5 s first-token goal.
5. Approve adding `/api/interactions/narrate(/stream)` to the proxy public
   allow-list when implementation lands.

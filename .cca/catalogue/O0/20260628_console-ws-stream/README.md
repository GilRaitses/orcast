# WS-STREAM: real-time streaming transport (suborchestrator home)

Waveset home for WS-STREAM in the Console Journey + Trips program (program
charter: `../20260627_console-journey-trips/PROGRAM_WAVESETS_CHARTER.md`). It
graduates the WS-PERF T4 track (streamed narration) into its own waveset because
the WS-PERF T4 research found the hard problem is the transport chain, not the
narration code. WS-STREAM does not build narration streaming as a one-off; it
researches, benchmarks, and discovers a reusable real-time streaming method for
the live console, of which streamed narration is the first consumer.

Read-only on code until the operator gates implementation. Everything here is
Markdown.

## Why a waveset, not the WS-PERF T4 track

The WS-PERF T4 research (`../20260628_console-ws-perf/T4_RESEARCH_SYNTHESIS.md`)
showed:

- The backend (`invoke_model_with_response_stream` + SSE) and the frontend
  (rAF-batched progressive render) are low-risk and well-understood.
- The risk is the prod transport chain:
  `Browser -> Vercel -> Next /api/be -> cloudflared tunnel -> uvicorn` (App Runner
  is rollback). `/api/be` buffers today (`resp.text()`), and Vercel and Cloudflare
  can buffer SSE in ways not fully under our config control.
- If any layer buffers, no amount of clean code hits the first-token goal.

That is a transport problem worth its own research + benchmark + discovery, and
the answer (a proven unbuffered streaming channel) is higher-reward than
narration alone: it is reusable.

## The flags to solve (from WS-PERF T4 research)

1. `/api/be/[...path]/route.ts` buffers every response (`resp.text()`).
2. Vercel platform buffering of streamed responses (function duration, runtime).
3. Cloudflare / cloudflared edge buffering of SSE.
4. uvicorn / FastAPI streaming correctness (`StreamingResponse`, sync boto3).
5. `/api/interactions/narrate` missing from the proxy public POST allow-list
   (anonymous 401).
6. Topology drift: docs say App Runner; prod is the cloudflared co-tenant host.
7. `EventSource` is GET-only; narrate is a POST with a body (needs fetch reader).
8. No `AbortController` / turn-generation guard in the frontend.
9. IAM `bedrock:InvokeModelWithResponseStream` on the serving role.
10. Persistence-at-end semantics on a streamed exchange.

## Higher-reward framing (the reusable capability)

The deliverable is a proven real-time streaming channel + a server streaming
pattern, not a narration-only feature. Streamed narration is consumer #1.
Candidate future consumers the research wave will weigh (to size the investment),
without committing to them here:

- Progressive whole-turn (panels + narration streamed together).
- Live connection refresh (ferry / corridor updates pushed as they change).
- Hydrophone / acoustic event push.

## Scope (locked at charter)

- First consumer is streamed narration on the live console. No new 3D engine, no
  new route; extend the existing console and the existing two-phase turn.
- Honesty unchanged: narration is prose only; labels / citations / deep_links /
  provenance ride the existing prefetched plan context.
- The non-streamed `/narrate` path stays as the guaranteed fallback.
- No ML promotion. Sub-agents commit / deploy / promote nothing; operator commits.

## Wave artifacts (produced as waves run)

- `WAVESET_CHARTER.md` (here) and `wave_shape.yml` (here).
- `RESEARCH_SYNTHESIS.md`, `BENCHMARK_REPORT.md`, `DISCOVERY_MAP.md`,
  `IMPLEMENTATION_DISPATCH.md`, `DEFECT_REGISTER.md`, `STEP_LOG.md`.

## Status

- Chartered, pending operator go. No wave has run. T4 in WS-PERF is marked
  graduated to WS-STREAM.

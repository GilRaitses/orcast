# WS2 probes — THROWAWAY scratch

These files exist only to MEASURE the transport chain in WS2. They are not
production code and must never be merged. After the benchmark, delete this dir
(or the WS4 editor deliberately promotes the proven pattern into real code).

| File | What it is | Where it runs |
|------|------------|---------------|
| `stream_probe_app.py` | Minimal FastAPI `/__stream_probe` SSE endpoint (meta/token/done framing + anti-buffer headers). Self-contained; does NOT import or edit `src/aws_backend`. | uvicorn on the cloudflared backend host (Steps 1-2) |
| `next_stream_route_candidate.ts` | CANDIDATE dedicated Next stream route that pipes `resp.body` through. NOT installed under `web/app`. | copied to a throwaway Vercel preview branch (Step 3) |
| `measure_stream.mjs` | Node `fetch` + `getReader()` harness. Records per-token arrival times, first-token latency, incremental-vs-buffered. Emits JSON. | the operator's laptop / CI runner |
| `measure_stream.sh` | curl `--no-buffer -N` quick eyeball + header dump. | the operator's laptop |

The exact deploy + measure runbook is in `../BENCHMARK_PLAN.md`. Sub-agents
authored these; O0 deploys and measures. Nothing here is committed, pushed, or
installed yet.

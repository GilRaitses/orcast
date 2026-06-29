# T4 discovery map (streamed narration)

Files to create or edit, owners, seams. T4 is serialized (single editor across
its convergence files); it must not regress the panels-first split (`fd50929`).

## One-file-one-owner map

| Change | File | Phase | Convergence? |
|--------|------|-------|--------------|
| SSE narrate endpoint (stream variant) | `src/aws_backend/routers/interactions.py` | B | YES |
| Bedrock streaming generator | `src/aws_backend/exploration/guide.py` | A | no |
| Proxy stream pass-through + narrate allow-list | `web/app/api/be/[...path]/route.ts` | B | YES |
| Streaming narration client | `web/lib/adaptiveConsole.ts` | B | YES |
| Progressive render + abort | `web/app/components/AdaptiveExplore.tsx` | B | YES |
| Transport spike (throwaway) | a temporary `/api/be` SSE probe + a tiny FastAPI `/__stream_probe` | spike | discard after |
| IAM | App Runner / co-tenant role | ops | `InvokeModelWithResponseStream` |

## Seams (file:line)

- Backend call: `guide.py:172-201` (`_bedrock_guide`, `invoke_model`); add a
  sibling `_bedrock_guide_stream` generator using
  `invoke_model_with_response_stream`, parsing `content_block_delta`/`text_delta`.
- Endpoint: `interactions.py:274-343`; add a `StreamingResponse` path (new route
  `POST /api/interactions/narrate/stream` or `Accept: text/event-stream` on the
  existing one). Emit `meta` (id + citations + deep_links + source + model),
  then `token` events, then `done` (full reply) / `error` (partial + reason).
  Persist after `done`.
- Proxy: `route.ts:175-180` buffer -> `new Response(resp.body, {headers})` with
  streaming headers; `route.ts:59-69` add `api/interactions/narrate(/stream)` to
  the public POST allow-list.
- Client: `adaptiveConsole.ts:114-145`; add `runAdaptiveNarrationStream(..., {
  onToken, signal })` reading `res.body.getReader()` + `TextDecoder`, parsing SSE
  frames; keep `runAdaptiveNarration` (JSON) as the L5 fallback.
- UI: `AdaptiveExplore.tsx:140-153` chunked `setTurns` append (rAF-batched),
  `:308-312` show partial text, `:52-68` defer markdown to stream end; add a
  `turnGenRef` + `AbortController` so a mid-stream new message cancels cleanly.

## Honesty / behavior invariants

- Narration is prose only; labels, citations, deep_links, provenance are
  unchanged and arrive in the `meta` event from the prefetched plan context.
- The non-streamed `/narrate` path stays intact as the fallback (L5). A buffered
  or failed stream must fall back, never hang.
- Persistence semantics unchanged: one atomic exchange written after the full
  reply, never a partial turn on abort.

## Pre-implementation blocker

The transport spike is the WP-T4 entry gate for implementation: an SSE byte
stream must demonstrably reach the browser unbuffered through
`Vercel -> Next /api/be pass-through -> cloudflared -> uvicorn`. If it buffers,
hold implementation and report which layer buffered.

## Gate verdict (T4 discovery)

PASS. Every file owned; convergence files named; the transport-spike blocker and
the narrate allow-list gap recorded; honesty invariants enumerated.

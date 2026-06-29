# T4 research synthesis (streamed narration)

Output of the T4 Research wave. Three read-only investigators (backend Bedrock,
proxy transport, frontend render). The headline: the hard problem is the
**transport**, not the Bedrock or React work.

## T4-A: backend Bedrock streaming

- Today `/api/interactions/narrate` (`interactions.py:274`) calls
  `compose_guide_reply` -> `_bedrock_guide` (`guide.py:172-201`), which uses
  `bedrock-runtime.invoke_model` with an Anthropic Messages body on Claude Haiku
  4.5, then reads the whole body at once.
- Streaming equivalent: `invoke_model_with_response_stream` with the identical
  body; iterate `response["body"]`, parse `chunk["type"] == "content_block_delta"`
  -> `delta["text"]`. Needs IAM `bedrock:InvokeModelWithResponseStream`.
- Citations / deep_links are prefetched (from the plan phase) BEFORE Bedrock, so
  they can be sent in an opening `meta` event; only the prose streams.
- Persist (`save_interaction_exchange`) after the full text is assembled at stream
  end. boto3 is sync, so the generator runs in a thread under `StreamingResponse`.

## T4-B: proxy transport (the blocker)

- `/api/be/[...path]/route.ts:175` does `await resp.text()` — it fully buffers
  every upstream response. Nothing streams to the browser until this becomes a
  `resp.body` pass-through with streaming headers (`text/event-stream`,
  `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`, no gzip).
- Production topology changed and is NOT App Runner directly:
  `Browser -> Vercel -> Next route handler -> ORCAST_API_BASE
  (https://orcast-api.aimez.ai) -> cloudflared tunnel -> uvicorn FastAPI`
  (App Runner is the rollback). Buffering can occur at the Next handler
  (certain today), Vercel, AND the Cloudflare/cloudflared edge.
- `/api/interactions/narrate` is NOT on the proxy public POST allow-list (only
  `plan` is), so anonymous narration would 401 — must be added for the live home
  console.
- Client must use `fetch` + `response.body.getReader()`, NOT `EventSource`
  (EventSource is GET-only; narrate is a POST with a large body).

## T4-C: frontend progressive render

- The two-phase turn is already in place. `AdaptiveExplore.tsx:140-153` replaces
  the bubble content one-shot at narration end; switch to chunked append via
  functional `setTurns`, batched with `requestAnimationFrame`, flipping
  `pending` off on the first chunk.
- `renderReply` (`:52-68`) should render plain text mid-stream and only apply the
  bold/link markdown at stream end (avoids broken `**`/`[](...)` on partial tokens).
- Citations / deep_links / provenance render from the phase-1 `plan` in
  `ActiveSurfaceHost`, NOT from the chat bubble, so stream-end metadata never
  reflows the streamed text.
- `runAdaptiveNarration` (`adaptiveConsole.ts:114-145`) replaces `res.json()`
  with a reader loop + `onToken` callback; keep the JSON path as the L5 fallback.
- Real risks: no `AbortController` today (a mid-stream new message races on the
  stale `assistantId`); needs a turn-generation guard + abort.

## The decisive finding

Every code change (Bedrock stream, React append) is well-understood and low-risk.
The uncertainty is whether an SSE byte stream actually survives the prod chain
(Vercel + Cloudflare/cloudflared + uvicorn) unbuffered. If any layer buffers, the
~1.5 s first-token goal is not met no matter how clean the code is, and some of
those layers are not fully under our config control.

**Recommendation: a thin transport spike first.** Prove a trivial SSE/byte
stream reaches the browser through the production proxy chain BEFORE building the
full Bedrock streaming endpoint and the progressive UI. If the spike streams, do
the full T4; if it buffers, T4 is not worth building until the transport is
fixed, and the panels-first split stays the answer.

## Gate verdict (T4 research)

PASS. Techniques named on all three layers. One blocking dependency (proxy
pass-through + buffering chain) and one auth gap (narrate allow-list) identified.
A transport spike is the recommended next step before implementation.

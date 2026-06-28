# R3: Edge / proxy / client resilience

**Lane:** WS-COLDSTART CS1-R3 (agent `a997c68c-a3ee-4443-9564-54201f78d620`)
**Scope:** Vercel proxy routes + client call graph + retry-safety + double-write guards
**Verdict:** Neither Vercel proxy retries upstream today. The only resilience is the client SSE stall→JSON-narrate fallback. The safest fix is a bounded server-side retry in `/api/be` `forward()` (1 retry, ~300ms backoff, on 502/503/504 + fetch errors; 404 only for idempotent GET allowlist), plus one pre-body retry in `narrate-stream`. Never retry mutating POSTs after headers; guard double-writes with retry-before-first-byte only.

## 1. No upstream retry today

Generic JSON proxy does a single fetch, no status branching (`web/app/api/be/[...path]/route.ts:180-185`); network errors become a Vercel 500; 502/503/504/404 pass straight through. The SSE route fetches once; a network failure maps to a 502 JSON so the client can fall back (`web/app/api/narrate-stream/route.ts:121-139`), non-OK upstream statuses are piped through unchanged (`141-161`), and a top-level catch returns JSON 500 (`53-62`).

## 2. Client call graph + existing fallback

`ensureSession` → `postJSON("api/explore/sessions")` no retry (`adaptiveConsole.ts:66-72`, `api.ts:31-38`). Plan via `/api/be/api/interactions/plan` with `narrate:false`, no retry (`adaptiveConsole.ts:92-102`). Narration stream via `readSseStream("/api/narrate-stream")` (`adaptiveConsole.ts:194-216`); `sseTransport.ts` fetches once, throws on non-OK/missing body (`117-126`), and enforces stall timeouts (10s first token / 15s idle → `SseStallError`, `31-32`,`171-173`). `AdaptiveExplore.tsx` catches a non-abort stream failure and falls back to JSON narrate, else finalizes "(narration unavailable)" (`195-223`); phase-1 (plan/session) failure just surfaces an error, no retry (`225-228`).

## 3. Retry-safety classification (backend persistence)

| Call | Persists? | Retry-safe on transient 5xx/404? |
|------|-----------|----------------------------------|
| GET `/api/explore/status`, gates, provenance, hotspots, `/health` | No | Yes (idempotent reads) |
| POST `/api/explore/sessions` | Yes — `INSERT exploration_sessions`, new UUID each call (`session_store.py:37-57`) | Risky (retry-before-first-byte only) |
| POST `/api/interactions/plan` `narrate:false` | No (persist gated on `narrate:true`, `interactions.py:210-263`) | Yes for DB; re-runs skills |
| POST plan `narrate:true` / `/api/interactions/narrate` | Yes — `save_interaction_exchange` (`interactions.py:330-345`) | No blind retry |
| POST `/api/interactions/narrate/stream` | Yes, only after a successful stream; failed/aborted persists nothing (`interactions.py:376-377,459-475`) | No mid-flight; pre-body only |
| POST `/api/explore/turn` | Yes — `save_exchange` (`explore.py:133-136`) | No |

`/health` does not require Aurora (`read.py:70-90`), which is exactly why it stayed 200 while explore 503'd. Explore routes gate via `_require_aurora()` and map DB-unreachable to 503 (`explore.py:26-30,46-51`).

## 4. Recommended placement + policy

Safest layer: server-side in `web/app/api/be/[...path]/route.ts` `forward()` (single choke point, key stays server-side, per-path policy), plus one pre-body retry in `narrate-stream/route.ts`.

| Parameter | Value |
|-----------|-------|
| Max retries | 1 (2 attempts) |
| Backoff | 300ms + 0-100ms jitter |
| Max added latency | <= 500ms |
| Retry on | fetch network/timeout errors; 502, 503, 504 |
| Conditional 404 | GET only, paths in the public GET allowlist (status, gates, provenance) |
| Never retry | 429, 401, 400, 409; anything after response headers on mutating POSTs |
| Stream route | retry upstream fetch once only when `!resp.ok && !resp.body` (no bytes yet); never after `pipeThrough` starts |
| Outage guard | if the retry also fails, return immediately; no loops; cap added latency so sustained outages still surface |

Do not add client-side retry for plan/session/narrate beyond the existing stream→JSON fallback (a path switch, not a duplicate POST).

## 5. Double-write risks + guards

- Double session: each POST inserts a new UUID row → retry only on fetch-throw or 502/503/504 before the body is read; never after a parsed 200. (Future: `Idempotency-Key`.)
- Double turn (narrate JSON / stream-success): never retry the narrate POST after headers; the client JSON fallback is correct only when the stream failed before backend persist (stream persists nothing on failure, `interactions.py:376-377`).
- Lost `done` frame → JSON fallback double-persist edge case (`sseTransport.ts:190-191`): mitigate by checking the stream `meta.interaction_id` before the JSON fallback, or backend idempotency on `(session_id, message)`.

## Five-point summary

1. Retry today: none in either proxy; only client SSE stall + JSON narrate fallback.
2. Safest layer: server-side in `/api/be` `forward()`, plus one pre-body retry in `narrate-stream`.
3. Policy: 1 retry, 300ms + jitter, on fetch errors + 502/503/504; 404 only for idempotent GETs; <=500ms added.
4. Must NOT retry: narrate (JSON + stream mid-flight), explore/turn, interactions, session-create after ambiguous success, plan `narrate:true`, and 429/401/400.
5. Double-write guard: retry-before-first-byte only; no POST retry after headers; skip JSON fallback if the stream `meta.interaction_id` was received.

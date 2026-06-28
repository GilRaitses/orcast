# WS-STREAM handoff charter

Lane: WS-STREAM (real-time streaming transport; streamed narration is consumer #1).
Owner role: O0 for this lane (operator-facing).
repo_state_verified_against: `origin/main`; local `main` is AHEAD BY 2 unpushed
commits (`82edeec`, `4d2dd73`). Branch: `main`.

## A. Purpose

Resume as O0 owning the WS-STREAM lane and RUN its chartered seven-wave waveset
from WS1. WS-STREAM was graduated out of WS-PERF because the prior T4 research
proved the hard problem is the streaming TRANSPORT CHAIN, not the narration code.
You research, then BENCHMARK the transport empirically, then discover a method,
then build, red-team, remediate, and accept. The charter and machine shape are
written and grounded; your job is to run them, gate the waves, and report to the
operator. Hydrate from files, never from the chat transcript linearly.

## B. Decisions that are LOCKED — do not reopen

1. The risk is the TRANSPORT, not the code. Prod chain is
   `Browser -> Vercel -> Next /api/be -> cloudflared tunnel -> uvicorn`
   (App Runner is ROLLBACK, not the live upstream, despite stale docs).
2. `/api/be/[...path]/route.ts` BUFFERS every response today (`await resp.text()`,
   ~line 175). Nothing streams to the browser until that becomes a `resp.body`
   pass-through with streaming headers. Vercel AND Cloudflare can also buffer SSE.
3. WS-STREAM runs a SEVEN-wave shape: Research, BENCHMARK (added), Discovery,
   Implementation, Adversarial, Remediation, Acceptance. The Benchmark wave is
   non-negotiable: measure before choosing a method.
4. WS2 Benchmark gate is "measure-first-or-stop": at least one method must be
   PROVEN to stream incrementally through the FULL prod chain with a measured
   first-token latency. If NONE stream, report which layer buffered and STOP — do
   not build a feature the pipe swallows.
5. Reuse (R4) scope is SIZE-AND-DOCUMENT ONLY (operator chose this). Build
   streamed narration first; only document future consumers (progressive
   whole-turn, live ferry/corridor push, hydrophone push). Do not build the
   reusable abstraction speculatively now.
6. Honesty unchanged: narration is PROSE ONLY. Labels / citations / deep_links /
   provenance ride the prefetched plan context and must be byte-identical to the
   panels-first split.
7. The non-streamed `/api/interactions/narrate` JSON path MUST REMAIN as the
   guaranteed fallback. A buffered or failed stream falls back, never hangs.
8. Do NOT regress the panels-first split (commit `fd50929`): fast `/plan`
   (narrate=false) paints panels, async narration fills the bubble.
9. Known transport flags to clear (all in `wave_shape.yml` `flags`): proxy
   buffering; Vercel buffering; Cloudflare/cloudflared buffering; uvicorn
   StreamingResponse; narrate NOT on the proxy public POST allow-list
   (`route.ts:59-69`, anonymous 401); topology drift App Runner vs cloudflared;
   `EventSource` is GET-only so use `fetch` + `response.body.getReader()`; no
   `AbortController`/turn-generation guard in the frontend; IAM
   `bedrock:InvokeModelWithResponseStream`; persistence at stream end only.
10. Execution discipline (program-wide): one-file-one-owner per wave; convergence
    files have a SINGLE phase-B editor; no dev server during a parallel phase;
    validate with type-check + fixture pytest; NO live calls in CI; sub-agents
    commit / deploy / promote NOTHING and return diffs + validation; secrets in
    `.env`; never `git add -A`; the operator commits and pushes.
11. NOTHING is pushed. Two local commits are ahead of origin/main; the operator
    has not asked to push. Do not push without an explicit operator ask.

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| WS-PERF T1 (fan-out concurrency) | `casting/trips/fanout.py` + `connections.py` refactor | committed `82edeec`, not pushed |
| WS-PERF T2 (traffic_flows guard) | guard test in `test_planner_trips_branch.py` | committed `82edeec`, not pushed |
| WS-PERF T3 (tiles first-paint) | none — closed no-fix (live `/3dtwin/full/` L0 ~0.97 MB < 1.5 MB; 5.9 MB was the dead pilot) | closed |
| WS-PERF T4 (streamed narration) | research only | GRADUATED to WS-STREAM |
| WS-PERF WP4 adversarial | failure-edge tests + `DEFECT_REGISTER.md` | committed `4d2dd73`, not pushed |
| WS-STREAM | charter + wave_shape + T4 research/discovery synthesis | chartered, WS1 not started |

## D. PRIMER — open items (operator verbatim where given)

- Operator framing: "charter to waveset research benchmark and discover a method
  to implement thats going to be even higher reward and solve these flags" and
  reuse "size_only". That is why WS-STREAM exists with a Benchmark wave and the
  reusable-capability framing, scoped to size-and-document.
- Operator deflected the WS1 launch decision into THIS rotation. So your FIRST
  operator-facing action is to present the WS1 launch gate (and the WS2 prod-probe
  approval), then run.

## E. Dispatch table

| Wave | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| WS1 Research | 4 read-only subagents | `wave_shape.yml` candidate_methods + flags | techniques per method + anti-buffering config per layer; R4 reward sizing | READY |
| WS2 Benchmark | 3 probers | WS1 method shortlist | one method proven to stream through full prod chain, measured; else STOP | GATED on WS1 + operator prod-probe approval |
| WS3 Discovery | 3 read-only | chosen method | files/owners/seams, convergence files named | GATED on WS2 |
| WS4 Implementation | phase-A 3, phase-B 1 | DISCOVERY_MAP | type-checks/tests green; progressive render local; fallback intact | GATED on WS3 + operator |
| WS5 Adversarial | = layers (L1-L5) | WS4 build | defect register complete + triaged | GATED on WS4 |
| WS6 Remediation | 4 | defect register | blocking+major closed/deferred | GATED on WS5 |
| WS7 Acceptance | 1 (you) | targets table | first-token measured on prod chain; visual; fallback drill | GATED on WS6 |

## F. Open gate / metric state

- Target: full ~5.5 s reply -> <= 1.5 s FIRST TOKEN, measured on the prod chain.
- The entire lane is conditional on WS2: if the transport cannot stream
  unbuffered end-to-end, the honest outcome is to STOP and keep panels-first.
- WS-PERF L1 (real-source EC2 re-benchmark of the fan-out win) is DEFERRED by the
  operator; not part of WS-STREAM but noted so you do not re-open it.

## G. Pending uncommitted local state

- Local `main` is ahead of origin/main by `82edeec` + `4d2dd73` (NOT pushed).
- Uncommitted working-tree edits exist: the WS-STREAM charter home
  (`.cca/.../20260628_console-ws-stream/`), this handoff home, and status ticks in
  the WS-PERF `STEP_LOG.md` / `wave_shape.yml`. These are docs; commit them with
  the operator's ask, never `git add -A` (the tree has a large unrelated pile of
  changes — stage only WS-STREAM + handoff paths).
- Same-machine rehydration: a fresh thread on THIS machine sees the uncommitted
  files directly. A cross-actor/cross-machine rehydration would need these
  committed + pushed first.

## H. Return contract (the ack the new thread MUST produce before acting)

Produce a short ack that:
1. Restates locked decisions B.1 (transport is the risk), B.4 (WS2
   measure-first-or-stop), B.5 (reuse size-only), B.7 (non-streamed fallback
   stays), B.8 (do not regress panels-first), and B.11 (nothing pushed).
2. States you will run WS-STREAM from WS1, holding WS2 prod probes and all
   implementation for operator approval.
3. Names the prod chain and the `/api/be` buffering blocker as the thing WS2 must
   empirically clear.
Then present the WS1 launch gate to the operator. Do not start waves before the ack.

## I. Transcript / provenance pointer

This session's transcript:
`/Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/f99daa85-44d1-4b94-ae59-f5d7f89f93f2/f99daa85-44d1-4b94-ae59-f5d7f89f93f2.jsonl`
Search by keyword (WS-STREAM, T4, fanout, traffic_flows, tileset, narrate), not
linearly. The files in HYDRATION_PACKET.md are the authority.

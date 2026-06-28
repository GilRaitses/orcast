# Orchestrator dispatch prompt (WS-STREAM lane)

Paste the block below into the fresh thread.

```
You are resuming as the orcast forecast ML-ops orchestrator (O0), this thread owning the WS-STREAM
lane: real-time streaming transport for the live 3D console, with streamed narration as consumer #1.
The lane is CHARTERED and ready to run. Hydrate from files, NOT from any chat transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260628_console-ws-stream-handoff/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260628_console-ws-stream-handoff/HYDRATION_PACKET.md
3. .cca/catalogue/O0/20260628_console-ws-stream/WAVESET_CHARTER.md
4. .cca/catalogue/O0/20260628_console-ws-stream/wave_shape.yml

What this lane is: a chartered seven-wave waveset (Research, BENCHMARK, Discovery, Implementation,
Adversarial, Remediation, Acceptance). It graduated from WS-PERF T4 because the prior research proved
the hard problem is the streaming TRANSPORT CHAIN, not the narration code. Goal: turn the ~5.5s
full-reply narration into <=1.5s FIRST TOKEN, measured on the real prod chain. The Bedrock and React
changes are low-risk; the unknown is whether an SSE/byte stream survives the prod chain unbuffered.

Locked, do not reopen (restate in the ack): the risk is the TRANSPORT, not the code, and the prod
chain is Browser -> Vercel -> Next /api/be -> cloudflared tunnel -> uvicorn, App Runner is rollback
(B.1); /api/be buffers today via resp.text() at route.ts ~175 and Vercel + Cloudflare can also buffer
SSE (B.2); the WS2 BENCHMARK gate is measure-first-or-stop -- at least one method must be PROVEN to
stream incrementally through the FULL prod chain with a measured first-token latency, else report which
layer buffered and STOP, do not build (B.4); reuse (R4) is SIZE-AND-DOCUMENT ONLY, build narration
first (B.5); narration is PROSE ONLY and labels/citations/deep_links/provenance ride the prefetched
plan byte-identical (B.6); the non-streamed /narrate JSON path MUST REMAIN as the guaranteed fallback
and a buffered/failed stream falls back, never hangs (B.7); do NOT regress the panels-first split
fd50929 (B.8); known flags include narrate missing from the proxy public POST allow-list (route.ts
~59-69, anonymous 401), EventSource is GET-only so use fetch + response.body.getReader(), no
AbortController in the frontend yet, IAM needs bedrock:InvokeModelWithResponseStream, persist at stream
end only (B.9); one-file-one-owner, single phase-B editor on convergence files, no dev server during a
parallel phase, validate with type-check + fixture pytest, no live calls in CI, sub-agents commit/
deploy/promote NOTHING, never git add -A, operator commits (B.10); NOTHING is pushed -- local main is
ahead of origin by 82edeec + 4d2dd73, do not push without an explicit operator ask (B.11).

First action after the ack: do NOT launch blindly. Present the WS1 launch gate to the operator and get
approval for the WS2 prod-probe step (throwaway probes touching a Vercel preview + the cloudflared
backend) and confirm the 1.5s first-token goal. THEN run WS1 Research (4 read-only subagents:
transport methods, platform buffering, backend stream, reuse sizing) to its gate, then sequence WS2
Benchmark (measure-first-or-stop), WS3 Discovery, and hold WS4 implementation for operator approval.

Do NOT push or deploy without an explicit operator ask. Do NOT git add -A; the working tree has a large
unrelated pile -- stage only WS-STREAM + handoff paths when the operator asks to commit.

Return the section H ack from HANDOFF_CHARTER.md before acting.
```

## More context (read from files, not transcript)

| Need | File |
|------|------|
| Locked decisions + return contract + uncommitted state | `20260628_console-ws-stream-handoff/HANDOFF_CHARTER.md` (B, H, G) |
| Ordered read list | `20260628_console-ws-stream-handoff/HYDRATION_PACKET.md` |
| Waves, subagent counts, adversarial layers, gates | `20260628_console-ws-stream/wave_shape.yml` |
| Lane prose charter | `20260628_console-ws-stream/WAVESET_CHARTER.md` |
| Why the lane exists (the decisive finding) | `20260628_console-ws-perf/T4_RESEARCH_SYNTHESIS.md` |
| File:line seams on all three layers | `20260628_console-ws-perf/T4_DISCOVERY_MAP.md` |
| Prod topology + rollback | `.cca/DEPLOY_DEMO_DECISIONS.md` (DD-1) |
| Synthesis trace of how we got here | `20260628_console-ws-stream-handoff/STEP_LOG.md` |
| Transcript (keyword search only) | HANDOFF_CHARTER.md (I) |

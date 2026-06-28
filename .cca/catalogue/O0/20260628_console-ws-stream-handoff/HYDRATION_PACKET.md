# WS-STREAM hydration packet (ordered read list)

Read in this order before acting. Files, not the transcript.

## 1. This handoff (governance for the rotation)

1. `.cca/catalogue/O0/20260628_console-ws-stream-handoff/HANDOFF_CHARTER.md`
   (locked decisions §B, return contract §H, uncommitted state §G)
2. `.cca/catalogue/O0/20260628_console-ws-stream-handoff/ORCHESTRATOR_DISPATCH_PROMPT.md`
3. `.cca/catalogue/O0/20260628_console-ws-stream-handoff/STEP_LOG.md`

## 2. The WS-STREAM lane (the charter you run)

4. `.cca/catalogue/O0/20260628_console-ws-stream/README.md`
5. `.cca/catalogue/O0/20260628_console-ws-stream/WAVESET_CHARTER.md`
6. `.cca/catalogue/O0/20260628_console-ws-stream/wave_shape.yml`
   (candidate_methods, flags, the seven waves with subagent counts + adversarial
   layers, collision_governance, operator_gates)
7. `.cca/catalogue/O0/20260628_console-ws-stream/STEP_LOG.md`

## 3. The T4 research that motivated the lane (evidence)

8. `.cca/catalogue/O0/20260628_console-ws-perf/T4_RESEARCH_SYNTHESIS.md`
   (the decisive finding: transport is the risk; transport spike recommended)
9. `.cca/catalogue/O0/20260628_console-ws-perf/T4_DISCOVERY_MAP.md`
   (file:line seams on all three layers; the narrate allow-list gap)
10. `.cca/catalogue/O0/20260628_console-ws-perf/STEP_LOG.md` (why T4 graduated)

## 4. Program context (parent charter + prior wavesets)

11. `.cca/catalogue/O0/20260627_console-journey-trips/PROGRAM_WAVESETS_CHARTER.md`
    (the six-wave lifecycle and program topology)
12. `.cca/catalogue/O0/20260628_console-ws-perf/README.md` and `wave_shape.yml`
    (sibling waveset; T1/T2 shipped, T3 no-fix, T4 graduated)

## 5. The live code surface WS-STREAM touches (read when WS3/WS4 near)

13. `src/aws_backend/exploration/guide.py` (~172-201: `_bedrock_guide`,
    `invoke_model`; the streaming generator goes here)
14. `src/aws_backend/routers/interactions.py` (~274-343: `/narrate`; the SSE
    endpoint variant goes here; persistence at stream end)
15. `web/app/api/be/[...path]/route.ts` (~175-180 buffer; ~59-69 public allow-list)
16. `web/lib/adaptiveConsole.ts` (~114-145: `runAdaptiveNarration`; the reader
    + onToken variant goes here; keep JSON path as fallback)
17. `web/app/components/AdaptiveExplore.tsx` (~38-44 ChatTurn; ~121-126 pending
    turn; ~140-153 phase-2 swap -> chunked append; ~308-312 pending UI; ~52-68
    `renderReply` defer markdown)

## 6. Repo map + environments

- Prod frontend: Vercel (`orcast-h0.vercel.app`). Prod backend upstream:
  `ORCAST_API_BASE = https://orcast-api.aimez.ai` -> cloudflared tunnel ->
  uvicorn (`orcast-api.service`) on the aimez-services host. App Runner
  (`pjrftm3bkv.us-west-2.awsapprunner.com`) is RUNNING as rollback.
- Deploy decisions: `.cca/DEPLOY_DEMO_DECISIONS.md` (topology DD-1).
- Tests: `tests/aws_backend` (fixture pytest, no live calls). Frontend
  type-check: `tsc --noEmit` in `web/`.

## 7. Provenance

- Transcript:
  `/Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/f99daa85-44d1-4b94-ae59-f5d7f89f93f2/f99daa85-44d1-4b94-ae59-f5d7f89f93f2.jsonl`
  Search by keyword, not linearly.

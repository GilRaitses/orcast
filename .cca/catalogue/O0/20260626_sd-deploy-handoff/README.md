# O0 Handoff Home — sd-deploy lane (2026-06-26)

Self-replacement packet so a fresh O0 thread resumes the Standing Decisions waveset with deploy hardening first, without replaying the chat.

## Files
- `HANDOFF_CHARTER.md` — authority doc; locked decisions (§B), dispatch table (§E), return contract (§H).
- `HYDRATION_PACKET.md` — ordered read list (canon -> charter -> evidence -> tooling).
- `STEP_LOG.md` — synthesis trace (S01..S06).
- `ORCHESTRATOR_DISPATCH_PROMPT.md` — the paste block for the new thread + a "more context" table.
- `README.md` — this file.

## Start a fresh thread
Paste the fenced block from `ORCHESTRATOR_DISPATCH_PROMPT.md` into a new O0 thread, or paste the one-liner the rotating orchestrator emitted in chat.

## Current lane status
- SD-H deploy hardening: PENDING (runs first; production Vercel build is RED since `9fe0a69`). Fix is design-conformant — delete root `vercel.json`, add minimal `web/vercel.json`, confirm dashboard Root Directory = `web`.
- SD-0..SD-4 Standing Decisions Register: PENDING (write `.cca/STANDING_DECISIONS_REGISTER.md`, wire above `CLAIM_BOUNDARIES.md`).
- Nothing committed; operator must approve commit/push and the Vercel dashboard toggle.

# orcast-lane handoff home (2026-06-27)

Self-replacement packet so a fresh orchestrator thread resumes the orcast B-side build,
forecast ML ops, and demo capture without replaying the chat.

Files:
- `HANDOFF_CHARTER.md` authority doc (purpose, locked decisions, registry, open items, return contract).
- `ORCHESTRATOR_NOTES.md` operator intent, PIML + ML-ops strategy, architecture critique, recommended literature.
- `HYDRATION_PACKET.md` ordered read list.
- `STEP_LOG.md` synthesis trace (S01-S09).
- `ORCHESTRATOR_DISPATCH_PROMPT.md` the paste block for the new thread + a context table.

Start the fresh thread: paste the block in `ORCHESTRATOR_DISPATCH_PROMPT.md`, then require the
section H ack from `HANDOFF_CHARTER.md` before any action.

Lane status: CAND done (200 candidates, 166 tier-A); BSIDE B-API done (rest chartered); FIX-CI
done locally (uncommitted, CI red on origin until pushed); MLM ladder runs (L1 diel passes, L2
fails honestly, effective confidence 0%); MLO `mlops-gate` done, AWS platform chartered; DEMO
capture blocked on a target decision. Nothing committed this session (write policy).

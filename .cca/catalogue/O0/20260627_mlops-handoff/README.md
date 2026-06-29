# forecast ML-ops lane handoff home (2026-06-27)

Self-replacement packet so a fresh orchestrator thread resumes the orcast forecast modeling
ML-ops lane (MLM covariate modeling + MLO platform) without replaying the chat. The 3d-twin
lane is handed off separately (`.cca/catalogue/O0/20260627_3d-twin/`); DEMO and BSIDE are dormant.

Files:
- `HANDOFF_CHARTER.md` authority doc (purpose, locked decisions, registry, open items, dispatch
  table, gate state, uncommitted state, return contract, provenance).
- `HYDRATION_PACKET.md` ordered read list.
- `STEP_LOG.md` synthesis trace (S10-S14; earlier steps in the orcast-handoff home).
- `ORCHESTRATOR_DISPATCH_PROMPT.md` the paste block for the new thread + a context table.

Start the fresh thread: paste the block in `ORCHESTRATOR_DISPATCH_PROMPT.md`, then require the
section H ack from `HANDOFF_CHARTER.md` before any action.

Lane status: L0 PASS (ROC AUC 0.879), L1 PASS, L2 FAIL at 0% but multi-station flips held-out
skill positive (+0.078); remaining L2 blockers are time-rescaling and cross-station consistency.
L3 withheld pending summer PRESENCE-DAYS from new in-region nodes (SYN/G3; the Albion Chinook feed is
already real, so L3 is presence-day/power-gated, not feed-gated). MLO platform chartered
(operator/deploy-gated). Effective
confidence stays 0% until a passing gate plus a recorded supervisor decision.

# BSW dispatch handoff (O0 rotation)

Self-replacement packet so a FRESH O0 thread takes over the BSW breadth + integrate campaign and
dispatches background sub-orchestrators for the six dispatch-ready lanes (BST, BAM, BSH, BRE, BSS,
SLICE-INTEGRATE), then reconciles their returns without blocking the operator.

Files:
- `HANDOFF_CHARTER.md` - authority: §B locked decisions, §C registry, §E dispatch table, §F gate authority, §H the ack the new thread must post.
- `HYDRATION_PACKET.md` - ordered read list (method, campaign authority, the six packets, charters, evidence, code seams, data, verification).
- `STEP_LOG.md` - synthesis trace S01..S07 (charter -> research -> slice -> /workbench -> commit -> packets -> this rotation).
- `ORCHESTRATOR_DISPATCH_PROMPT.md` - the fenced paste block for the new thread.
- `README.md` - this file.

State: repo `main` `1b9772e` (pushed). The six lanes are all `gated-on-O0`; the slice is already
committed. This handoff folder is uncommitted until the operator asks.

How to start the fresh thread: open a new chat and paste the one-liner emitted in the rotating thread
(or, equivalently): "Hydrate as O0 (BSW dispatch lane) from
`.cca/catalogue/O0/20260629_bsw-dispatch-handoff/ORCHESTRATOR_DISPATCH_PROMPT.md` and ack per
HANDOFF_CHARTER §H before acting." The new O0 posts the ack, then dispatches the six background
sub-orchestrators per `dispatch/SEQUENCING.md`.

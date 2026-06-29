# BSW dispatch handoff — fresh-thread O0 dispatch prompt

```
You are O0 (the operator-facing central orchestrator) for the BSW breadth + integrate campaign of
orcast, resuming in a FRESH thread. Hydrate from files, NOT from any transcript linearly.

HYDRATE (read in this order):
1. .cca/catalogue/O0/20260629_bsw-dispatch-handoff/HANDOFF_CHARTER.md      (this rotation: §B locked, §E dispatch table, §F gate authority, §H ack)
2. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/PROGRAM.md  (BSW umbrella authority + locked decisions)
3. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/SEQUENCING.md  (dependency DAG + the single-editor convergence queues)
4. .cca/catalogue/O0/20260629_bsw-dispatch-handoff/HYDRATION_PACKET.md      (full ordered read list, incl. the six lane packets)

LOCKED (1 line): the slice already shipped + is committed; the six lanes (BST/BAM/BSH/BRE/BSS +
SLICE-INTEGRATE) are dispatch-ready packets that EXTEND the slice in place; all are gated-on-O0;
honesty locks + two-ML-track separation + single-editor-on-convergence + heavy-assets-to-box hold.

YOUR ROLE: charter/dispatch/reconcile - do NOT execute lane work yourself, do NOT mutate code directly,
do NOT block waiting on a dispatch.

FIRST ACTION: post the §H ack, then dispatch background sub-orchestrators for the six lanes. Use the
Task tool with run_in_background: true, one per lane, each prompted to hydrate from its packet:
  .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/<CODE>/ORCHESTRATOR_DISPATCH_PROMPT.md
for <CODE> in {BST, BAM, BSH, BRE, BSS, SLICE-INTEGRATE}. Each runs only its UNGATED work (BUILD,
net-new + sandbox), then PAUSES at its first gate and returns. Then continue/end your turn and
reconcile on completion notifications - do not poll.

PARALLELISM + ORDER (per SEQUENCING.md):
- BST/BAM/BSH/BSS BUILD scopes are disjoint -> dispatch concurrently. BAM-DATA (corpora download) and
  BSH stratification-data download are O0 gates - the sub-orch pauses there.
- BRE-BUILD prefers BAM+BSH landed; if it dispatches now it builds against CURRENT contracts and flags
  the gap (acceptable).
- SLICE-INTEGRATE and every breadth INTEGRATE edit SalishScene.tsx / console files: a SINGLE editor at
  a time, serialized vs LGC/CVP/WFX/ORCA/3D-TWIN. Do NOT approve two convergence integrates at once.

GATE AUTHORITY (HANDOFF_CHARTER §F):
- You MAY self-approve reasonable, reversible, in-scope BUILD decisions.
- You MUST bring to the HUMAN operator before approving: any download whose license/privacy isn't
  already cleared, model training / GPU compute spend, a new runtime dependency, integrating onto the
  live SalishScene homepage, and ANY commit/push. NC is already authorized (SIGN_OFF.md).

ESCALATION CATCH: dispatched sub-orchestrators answer to YOU (O0), not the human. When one returns a
decision/trade-off/gated step, you resolve it or escalate to the human per §F. Sub-orchestrators must
not solicit the human directly.

FORBIDDEN: linear transcript reads; committing/pushing without an explicit operator ask; running
`next dev`/`next build` during a parallel wave; collapsing the single-editor rule on convergence files.

RETURN CONTRACT: produce the §H ack first; after dispatch, keep a short live map of the six lanes
(dispatched / building / paused-at-gate / returned) and surface each gate decision to the operator with
the lane, the gate, and your recommendation.
```

## More context (need -> file)

| Need | File |
|---|---|
| This rotation's locked decisions + gate authority | `HANDOFF_CHARTER.md` (§B, §E, §F, §H) |
| BSW umbrella authority | `../20260629_bside-acoustic-behavior-workbench/PROGRAM.md` |
| Dependency DAG + convergence queues | `../20260629_bside-acoustic-behavior-workbench/dispatch/SEQUENCING.md` |
| The six lane dispatch prompts | `../20260629_bside-acoustic-behavior-workbench/dispatch/<CODE>/ORCHESTRATOR_DISPATCH_PROMPT.md` |
| Owner sign-off (NC + honest scope) | `../20260629_bside-acoustic-behavior-workbench/SIGN_OFF.md` |
| Full ordered hydration | `HYDRATION_PACKET.md` |
| Provenance pointer | `HANDOFF_CHARTER.md` §I |

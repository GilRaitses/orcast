# BSWR — BSW follow-up remediation

The remediation round that closes the follow-ups the landed BSW breadth +
integrate campaign flagged as STOP-to-O0. Six wavesets, one per follow-up, each
running the same lifecycle: research -> qualify methodology -> implement ->
adversarial review (loop) -> integrate -> accept, gated until every gate and
critique passes.

## Files

- `PROGRAM.md` — umbrella authority, lifecycle, locked decisions, gate ledger, escalation.
- `<CODE>_CHARTER.md` — per-lane authority (ACX, STU, OCN, ENV, PRF, STX).
- `dispatch/<CODE>/ORCHESTRATOR_DISPATCH_PROMPT.md` — the paste block to launch the lane.
- `dispatch/<CODE>/wave_shape.yml` — the waves + per-agent ownership.

## Lanes

| Code | Closes | Front gate |
|---|---|---|
| ACX | ecotype TKW lift + call_type ship-or-stay-diagnostic | new dep / corpora / box compute |
| STU | backend annotations endpoint + proxy allow-list + ORCAST_API_BASE | backend route design / deploy |
| OCN | measured CC0 CTD profile + R09 depth-aware plume-clip | CC0 download / WFX depth seam |
| ENV | drop the slice's duplicate PMREM bake; ORCA publishes its env handle | ORCA coordination / convergence edit |
| PRF | honest client-tier 30fps frame-time (T4 is server-class upper bound) | real-hardware / host run |
| STX | wider Puget Sound nodes (OPTIONAL, 3D-TWIN extent) | build-vs-defer decision |

## Start a lane

Dispatch a background sub-orchestrator with the lane's
`dispatch/<CODE>/ORCHESTRATOR_DISPATCH_PROMPT.md`, or paste it into a fresh
thread. Each lane runs its ungated research wave, then PAUSES at the methodology
gate and returns to O0. O0 holds all gate decisions and serializes convergence
edits across lanes and across the LGC / CVP / ORCA / WFX / 3D-TWIN families.

## Status

Chartered `2026-06-29` against origin/main `61ba1d6`. Registered under family
`BSWR` in `docs/devpost/waves.registry.yaml`.

# Signal & modeling research campaign launch handoff (2026-06-27)

Self-replacement packet so a FRESH orchestrator thread launches and manages the signal & modeling research
campaign without replaying the chat. The campaign (`signal_modeling_research` in
`.cca/catalogue/O0/20260627_mlops/`) is CHARTERED and dispatch-ready at `main` `9a00e15`. The new thread
hydrates from these files, never from the transcript linearly.

## Why a fresh thread

The forecast frontier hit an honest wall: the served 4-station fit is +0.078 -> confidence 0.49 (HOLD),
and the W6 ingest added 0 net-new analysis observations, so the same cached data cannot reach 0.6.
Crossing it needs genuinely new signal to ~+0.144 fold-stable. The campaign researches that lever; the new
thread runs it on a clean context budget.

## Files

- `HANDOFF_CHARTER.md` — authority doc (A–I): §B locked decisions + the +0.144 bar, §D the operator's
  verbatim launch instruction, §E the dispatch table, §H the required ack.
- `HYDRATION_PACKET.md` — ordered read list (governance -> the campaign charter/dispatch -> why it exists
  -> methodology -> code surface -> findings dir/environments).
- `STEP_LOG.md` — full lineage S01–S10 (L0–L3, research waveset, W4+P0, W5 grounding, W6 deploy, W7
  measured-HOLD, the wall, the campaign charter, this rotation) + the launch plan.
- `ORCHESTRATOR_DISPATCH_PROMPT.md` — the paste block for the new thread + a need->file table.
- `README.md` — this file.

## How to start the fresh thread

Paste the one-liner (or the full block in `ORCHESTRATOR_DISPATCH_PROMPT.md`) into a new thread:

> Hydrate as O0 (signal & modeling campaign launch lane) from
> `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/ORCHESTRATOR_DISPATCH_PROMPT.md` and ack per
> `HANDOFF_CHARTER.md` §H before acting.

After the ack, its first action is to dispatch the five research subagents (W9 S1/S2, W10 M1/M2/M3) per
`SIGNAL_MODELING_DISPATCH.md`, then run SYN, then bring ranked graduates back as operator-gated waves.

## Current status

Effective confidence 0%. Campaign CHARTERED; W9 + W10 launch is the next action. Nothing in the campaign
promotes; build/deploy/promote of any graduate is a separate operator-gated wave. This handoff home and the
research findings are uncommitted until an explicit operator ask.

## Authority / lineage

- Inherited forecast ML-ops locks: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` §B.
- Campaign home: `.cca/catalogue/O0/20260627_mlops/` (charter, dispatch, `wave_shape.yml`, `STEP_LOG.md`).
- Operator intent / PIML strategy: `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md`.
- Methodology canon: `docs/methodology/FORECAST_KERNELS.md`, `CALIBRATION_STUDIES.md`.

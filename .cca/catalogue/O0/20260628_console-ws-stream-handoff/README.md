# WS-STREAM handoff home

Rotation packet so a fresh thread can take over O0 for the WS-STREAM lane
(real-time streaming transport; streamed narration is consumer #1) with full
hydration and provenance. Built with the orchestrator-rotation skill.

## Files

- `HANDOFF_CHARTER.md` — authority doc: locked decisions (§B), dispatch table
  (§E), uncommitted state (§G), return contract (§H).
- `HYDRATION_PACKET.md` — ordered read list (handoff -> lane charter -> evidence
  -> program context -> code surface -> environments).
- `STEP_LOG.md` — synthesis trace of how the lane reached this point.
- `ORCHESTRATOR_DISPATCH_PROMPT.md` — the paste block for the new thread + a
  "more context" table.
- `README.md` — this file.

## How to start the fresh thread

Paste the one-liner the originating thread emitted (or open
`ORCHESTRATOR_DISPATCH_PROMPT.md` and paste its fenced block) into a new thread.
The new thread hydrates from files, acks per HANDOFF_CHARTER §H, then presents the
WS1 launch gate before running any wave.

## Status

WS-STREAM is chartered (`../20260628_console-ws-stream/`); WS1 not started. The
lane runs a seven-wave shape with a measure-first-or-stop Benchmark gate. Nothing
is pushed; two local commits are ahead of origin/main.

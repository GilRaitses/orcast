# Trips launch handoff

Rotation home for handing the Console Journey + Trips program to a fresh O0 thread. The program is
CHARTERED and dispatch-ready; this directory hydrates the incoming orchestrator to that exact point.

## Use

1. Open a fresh thread.
2. Paste the block from `ORCHESTRATOR_DISPATCH_PROMPT.md`.
3. The new thread reads `HANDOFF_CHARTER.md` -> `HYDRATION_PACKET.md` -> the program charter, returns
   the §H ack, confirms DECISION_RECORD items 4-8 + the WSDOT access code with the operator, then
   launches W1.

## Files

| File | Role |
|------|------|
| `HANDOFF_CHARTER.md` | Authority doc: purpose, locked decisions (§B), dispatch table, gate state, ack (§H) |
| `HYDRATION_PACKET.md` | Ordered read list (governance -> program -> live code -> sources) |
| `ORCHESTRATOR_DISPATCH_PROMPT.md` | Paste block for the fresh thread |
| `STEP_LOG.md` | Rotation trace (newest last) |

## Program home

`.cca/catalogue/O0/20260627_console-journey-trips/` (charter, visual program, wave_shape, connections
research, W1/W2/W3 dispatches).

## Not in scope for the incoming thread

The OS1 open-science effort/detectability lane
(`.cca/catalogue/O0/20260627_open-science-integration/`) stays with the originating orchestrator. Its
extraction is complete but the measurement has a defect (offset tails) needing a robustness pass.

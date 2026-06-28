# WS-TRIPS — trips journey and connections planner (suborchestrator home)

Waveset home for WS-TRIPS in the Console Journey + Trips program (charter:
`../20260627_console-journey-trips/PROGRAM_WAVESETS_CHARTER.md`). This thread ran
the Research wave then the Discovery wave only. Read-only on code; everything
here is Markdown.

## Scope (locked)

- Real multi-step planner on the live console; port the trip hierarchy (B.3/B.4).
- Connections honesty-labeled measured / modeled / published (B.6).
- No ML promotion; the whale forecast stays the hotspot heuristic with its
  existing `effective_confidence` gate (B.9).
- One-file-one-owner; `planner.py` has a single editor in phase B (B.8).
- Agents commit / deploy / promote nothing (B.10).

## Convergence files (WS-TRIPS only, charter section 4)

- `src/aws_backend/casting/planner.py` (phase B, single editor).
- `web/app/components/ActiveSurfaceHost.tsx` panel registry (phase B).

## Dependencies

- WS-INTENT must land first (WS-TRIPS needs the live surface and the viewport
  bridge). The connections planner and corridor model backend build in parallel
  earlier and do not need INTENT.
- W2 clients are DONE: `src/aws_backend/sources/wsf.py`,
  `src/aws_backend/sources/wsdot_traffic.py`.
- The corridor history log is LIVE and accruing now at
  `data/external/traffic_corridor/seatac_anacortes.jsonl` (gitignored).

## Wave outputs in this folder

- `RESEARCH_SYNTHESIS.md` — branch design, connection-feasibility reasoning,
  corridor ETA model approach, kayak tide/current surface, all cited in code.
- `DISCOVERY_MAP.md` — planner / panel-host structure, the branch seam, the
  one-file-one-owner table, and the honesty map.
- `IMPLEMENTATION_DISPATCH.md` — PROPOSED phase-A producer prompts + the phase-B
  convergence prompt, for the program orchestrator to gate.
- `STEP_LOG.md` — what this thread did, in order.

## Status

- Research wave: complete (gate met — concrete techniques and in-repo sources named).
- Discovery wave: complete (gate met — every create/edit file owned, seams named,
  no unowned convergence-file edits).
- Implementation onward: NOT started here. Held for the program orchestrator gate.

# WS-PERF: console performance waveset (suborchestrator home)

Waveset home for WS-PERF in the Console Journey + Trips program (program charter:
`../20260627_console-journey-trips/PROGRAM_WAVESETS_CHARTER.md`). It charters the
performance recommendations produced by the 2026-06-28 benchmark (EC2 t3.large,
us-west-2, real DynamoDB / Bedrock / WSDOT / WSF) into the fixed six-wave
lifecycle. Read-only on code until the operator gates implementation; everything
here is Markdown.

## Origin: what the benchmark found

| Path | Measured | Verdict |
|------|----------|---------|
| `plan` keyword (narrate=0) | ~16 ms | fine |
| `plan` visiting + connection (narrate=0) | ~365 ms | ~4 sequential live legs |
| `plan` here-now + connection (narrate=0) | ~395 ms p50 / ~1383 ms p95 | tail from a WSF leg |
| `plan` + narration | ~5.5 s | already split (panels-first shipped in `fd50929`) |
| `wsdot.traffic_flows` | ~1.8 s (1465 rows) | slow; must stay off the request path |
| 3D first content payload | ~5.9 MB / ~700 ms | first-paint floor |

## Scope (tracks)

- **T1 connection fan-out concurrency** (backend). The visiting / here-now plan
  runs ~4 live WSF / WSDOT / flight legs sequentially at ~100 ms each. Run them
  concurrently. Owns `src/aws_backend/casting/trips/connections.py`.
- **T2 `traffic_flows` off the request path** (backend). The ~1.8 s
  `wsdot_traffic.traffic_flows()` call must only run in the background corridor
  poller, never inside a `/plan` turn. Audit call sites; add a guard test.
- **T3 tile first-paint LOD** (frontend). Lower the initial level of detail /
  screen-space error so first meaningful content is not a 5.9 MB fetch. Owns the
  scene tiles config module (not `SalishScene.tsx` internals).
- **T4 streamed narration** (OPTIONAL, operator-gated). Extend the panels-first
  split shipped in `fd50929` to stream Bedrock tokens over SSE so first token
  lands ~1.5 s instead of waiting for the full ~5.5 s reply. Owns the `/narrate`
  stream variant + the frontend turn files.

## Locked constraints (inherited from the program charter)

- Honesty labels unchanged: measured / modeled / published / heuristic. A faster
  plan must not relabel any leg, and "unknown" must never collapse to "zero".
- No ML promotion; the whale forecast stays the hotspot heuristic (B.9).
- One-file-one-owner; convergence files have a single phase-B editor (B.8).
- Sub-agents commit / deploy / promote nothing; operator commits (B.10).

## Convergence files (WS-PERF only)

- `src/aws_backend/casting/trips/connections.py` (T1, phase B, single editor).
- The scene tiles config module (T3, phase B, single editor; does not touch the
  `SalishScene.tsx` mount owned by INTENT / SCENIC / BATHY).
- `src/aws_backend/routers/interactions.py` + `web/lib/adaptiveConsole.ts` +
  `web/app/components/AdaptiveExplore.tsx` (T4 only, serialized single editor).

## Dependencies

- WS-TRIPS implementation has landed (connections planner + corridor model live;
  trips deployed in `643eef7`). T1 optimizes the connections planner it built.
- The panels-first narration split (`fd50929`) is live; T4 extends it, it does
  not replace it.
- No dependency on WS-SCENIC / WS-BATHY; T3 touches only the tiles config.

## Wave artifacts (produced as waves run)

- `WAVESET_CHARTER.md` (here) — the six waves, parameterized counts, layers, gates.
- `wave_shape.yml` (here) — machine shape: per-wave parallelism, adversarial
  layers, targets, collision governance.
- `RESEARCH_SYNTHESIS.md` — WP1 output.
- `DISCOVERY_MAP.md` — WP2 output.
- `IMPLEMENTATION_DISPATCH.md` — WP3 proposed producer + convergence prompts.
- `DEFECT_REGISTER.md` — WP4 output.
- `STEP_LOG.md` — what this thread did, in order.

## Status

- Chartered, pending operator go. No wave has run.
- Held for the program orchestrator gate (operator decisions in `wave_shape.yml`
  `operator_gates`).

# WS-PERF: performance waveset charter

## 0. How to use this charter

WS-PERF turns the 2026-06-28 benchmark recommendations into a gated build. It
runs the program's fixed six-wave lifecycle
(`../20260627_console-journey-trips/PROGRAM_WAVESETS_CHARTER.md` section 1). Read
this charter, then `wave_shape.yml` for the machine shape (per-wave subagent
counts, adversarial layers, numeric targets, collision governance). The program
orchestrator (O0) launches one wave at a time and synthesizes into `STEP_LOG.md`
after each. Do not start a wave whose entry gate is unmet.

## 1. What is being optimized

Four tracks, each carrying a measured baseline and a goal (see `wave_shape.yml`
`targets`):

- **T1 connection fan-out concurrency.** The visiting / here-now plan runs ~4
  live WSF / WSDOT / flight legs sequentially at ~100 ms each (~365 ms p50). Run
  them concurrently. Goal: visiting p50 365 ms -> 180 ms; here-now p95 1383 ms
  -> 450 ms.
- **T2 `traffic_flows` off the request path.** `wsdot_traffic.traffic_flows()`
  costs ~1.8 s for 1465 rows. It must run only in the background corridor poller,
  never inside a `/plan` turn. Goal: 0 `traffic_flows` calls per plan turn,
  proven by a guard test.
- **T3 tile first-paint LOD.** The 3D root content payload is ~5.9 MB before
  progressive streaming. Lower the initial level of detail / screen-space error
  (or split the root) so first meaningful content is < 1.5 MB. Goal: first
  content 5.9 MB -> 1.5 MB with scene coherence unchanged (visual-verified).
- **T4 streamed narration (optional).** Extend the panels-first split shipped in
  `fd50929` to stream Bedrock tokens over SSE. Goal: first token < 1.5 s instead
  of the full ~5.5 s reply. Operator-gated in or deferred.

## 2. Lifecycle and parameterization

Every wave below is parameterized in `wave_shape.yml` by `parallelism` (the
subagent count for that wave). Research and Discovery fan one reviewer per track;
Implementation splits into parallel phase-A producers plus a serialized phase-B
convergence editor; Adversarial fans one reviewer per layer; Remediation fans by
owner; Acceptance is a single orchestrator sign-off.

### WP1 Research (parallelism 4, read-only)

One researcher per track. Output `RESEARCH_SYNTHESIS.md`.

| Track | Question to answer with cited options |
|-------|----------------------------------------|
| T1 | Concurrency for a synchronous FastAPI handler: `ThreadPoolExecutor` over the blocking `requests` legs vs converting to async. Bound, timeout, and failure semantics. |
| T2 | The full call graph that reaches `traffic_flows()`; how the corridor poller is scheduled; the cheapest guard that proves the request path never calls it. |
| T3 | `3d-tiles-renderer` `errorTarget` / `geometricError` / screen-space-error knobs; splitting or re-tiling the root; what controls the first content fetch. |
| T4 | `bedrock-runtime` `invoke_model_with_response_stream`; streaming SSE through the same-origin `/api/be` proxy; client `EventSource`/reader progressive render. |

Gate: the synthesis names concrete techniques per track, not directions.

### WP2 Discovery (parallelism 4, read-only)

Ground each technique in this repo: exact files, owners, the convergence seam,
and the honesty-label surfaces that must stay byte-identical. Output
`DISCOVERY_MAP.md`.

Gate: every file to create or edit is owned; convergence files named; no unowned
convergence-file edits.

### WP3 Implementation (phase-A parallelism 3, phase-B parallelism 1)

- Phase A (parallel producers, no convergence files): T1 concurrency in a pure
  helper, T2 guard test, T3 tiles-config change. T4 adds one producer if enabled.
- Phase B (single editor per convergence file): wire the T1 helper into
  `connections.py`; land the T3 tiles config. T4 narration is serialized
  separately on `interactions.py` plus the two turn files.

Gate: type-checks and fixture tests pass; the benchmark harness shows the target
deltas locally; graceful degradation under a slow or empty source is preserved.

### WP4 Adversarial (parallelism = number of active layers)

A reviewer that did not build the change runs each layer. The layers are the
pre-acceptance gate: all non-optional layers must run and file before acceptance.

| Layer | Dimension | Check |
|-------|-----------|-------|
| L1 | performance-regression | Re-run the EC2 benchmark; targets hit AND no p95/p99 regression on keyword / kayak / curious / health. |
| L2 | correctness-honesty | Concurrency drops or duplicates no leg; per-leg and composite labels and the freshness stamp are identical to baseline; unknown stays unknown. |
| L3 | failure-edge | One source times out: the concurrent plan degrades exactly like the sequential plan did; a partial plan is labeled, not fabricated. |
| L4 | frontend-visual-perf | The tile LOD change preserves scene coherence (read the rendered output, never claim a fix unseen); first paint measured improved; no missing geometry at rest altitude. |
| L5 | stream-robustness (optional, T4) | Partial stream, client disconnect, and proxy buffering handled; falls back to the non-streamed `/narrate`. |

Gate: the defect register is complete and severity-triaged.

### WP5 Remediation (parallelism 4, serialized on convergence files)

Fix filed defects by owner, highest severity first. Gate: every blocking and
major defect closed, or explicitly deferred with operator sign-off.

### WP6 Acceptance (parallelism 1, orchestrator signs off)

Verify against the `targets` table with a real measurement: re-benchmark on EC2
and visually verify the tiles. The orchestrator, not the builder, signs off.
Gate: targets met and recorded in `STEP_LOG.md`; honesty labels unchanged.

## 3. Collision governance

- `connections.py` is a convergence file: T1 is its only WP3 phase-B editor; T2
  only audits and adds a separate guard test.
- The tiles config is a convergence file: T3 single editor; it does not touch the
  `SalishScene.tsx` mount owned across INTENT / SCENIC / BATHY.
- T4 (if enabled) is the only editor of `interactions.py`, `adaptiveConsole.ts`,
  and `AdaptiveExplore.tsx`, serialized, and must not regress the panels-first
  split in `fd50929`.
- Producers commit / deploy / promote nothing; the operator commits; never
  `git add -A`; secrets stay in `.env`.

## 4. Per-agent prompt skeleton (copy-paste)

```
## Agent <X> — <role> (owns <path>)
YOUR TASK: <one paragraph>
DELIVERABLES: <files + exported symbols>
VALIDATION: <type-check / pytest command + the benchmark check that proves the target delta>
COLLISION-AVOIDANCE: you own ONLY <path>. Do not edit <convergence file> (that is <phase B owner>).
RETURN: diff summary + validation output + the measured before/after number. Do not deploy/commit/promote.
```

## 5. Acceptance criteria (the numbers)

From `wave_shape.yml` `targets`:

- visiting plan p50: 365 ms -> <= 180 ms.
- here-now plan p95: 1383 ms -> <= 450 ms.
- `traffic_flows` calls per plan turn: 0 (guard-tested).
- tile first content: 5.9 MB -> <= 1.5 MB, scene coherence unchanged.
- (T4) narration first token: <= 1.5 s.

## 6. Operator decisions before fan-out

1. Confirm T1, T2, T3 in scope at this granularity.
2. Decide T4 (streamed narration): in this waveset, or deferred.
3. Approve vendoring the benchmark harness under `tools/testing/bench/` so
   acceptance is repeatable.
4. Approve a short EC2 re-benchmark at adversarial L1 and at acceptance.
5. Confirm or override the numeric goals in section 5.

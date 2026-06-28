# WS-PERF step log

## 2026-06-28 — charter

- Chartered WS-PERF from the 2026-06-28 benchmark findings (EC2 t3.large,
  us-west-2, real DynamoDB / Bedrock / WSDOT / WSF). Artifacts: `README.md`,
  `WAVESET_CHARTER.md`, `wave_shape.yml`.
- Tracks: T1 connection fan-out concurrency, T2 traffic_flows off the request
  path, T3 tile first-paint LOD, T4 streamed narration (optional).

## 2026-06-28 — operator gate

- T4 (streamed narration): DEFERRED to a follow-on. WS-PERF carries T1-T3.
- Launch: WP1 Research + WP2 Discovery now, read-only, in parallel. Implementation
  (WP3) held for the gate.
- WP1/WP2 parallelism set to 3 (one per active track).

## 2026-06-28 — WP1+WP2 dispatch (read-only)

- Dispatched three read-only investigators (T1, T2, T3), each producing the
  research (techniques) + discovery (exact files / owners / seams) slice for its
  track. Synthesized into `RESEARCH_SYNTHESIS.md` and `DISCOVERY_MAP.md`.

## 2026-06-28 — WP1+WP2 gate results

- WP1 Research gate: PASS. WP2 Discovery gate: PASS. Two scope corrections:
- T1: confirmed real win. Bounded `ThreadPoolExecutor` in a new phase-A helper
  `casting/trips/fanout.py`, wired into `connections.py` (convergence). Four
  ferry legs parallelize; matching/labels/freshness stay sequential.
- T2: SCOPE CHANGE. `traffic_flows()` has zero production callers; it is not on
  the `/plan` request path today (the drive leg uses `travel_times` via
  `corridor_route_ids`). T2 becomes a regression GUARD test, not a fix.
- T3: PREMISE CORRECTION. The benchmark's 5.9 MB was the obsolete single-tile
  pilot; the live console serves `/3dtwin/full/` (85 tiles, multi-LoD). T3 has a
  pre-WP3 blocker: re-measure first paint on the full tileset before fixing a
  target. A one-line `SalishScene.tsx:744` `errorTarget` de-override is the only
  collision exception, to be granted at WP3.
- Held for operator: the T3 re-measurement and the SalishScene collision grant
  before WP3 Implementation.

## 2026-06-28 — operator gate + T3 re-measurement

- Operator: re-measure T3 first; launch WP3 for T1 + T2; hold T3 LOD tuning.
- T3 RE-MEASUREMENT (curl on live CDN): the full tileset
  `/3dtwin/full/tileset.json` is 52 KB; its L0 root content `tiles/L0_0_0.glb`
  is 989,724 bytes (~0.97 MB), already UNDER the 1.5 MB goal. The 5.9 MB was the
  dead pilot. geometricError ladder L0 80 -> L1 40 -> L2 20 -> L3 10.
- T3 verdict: no LOD reduction needed and no SalishScene de-override needed.
  T3 reduces to a regression-guard measurement spec (deferred to acceptance), not
  a fix. The `errorTarget:16` override stays as-is.

## 2026-06-28 — WP3 launched (T1 + T2)

- Implementing T1 fan-out concurrency (fanout.py + connections.py) and the T2
  guard test. Producers return diffs; operator commits.

## 2026-06-28 — WP3 implementation done (T1 + T2), not committed

- T1: new `src/aws_backend/casting/trips/fanout.py` (bounded ThreadPoolExecutor,
  per-task exception isolation). `connections.py` `_build_drive_leg` /
  `_build_ferry_leg` split fetch from assemble via a `_UNSET` sentinel
  (backward-compatible); `plan_connection` fans out the four ferry-branch fetches
  (predict_eta, schedule, sailing_space, vessel_locations) concurrently, then
  assembles sequentially. Honesty labels, freshness, leg ordering unchanged.
- T2: `test_visiting_and_here_now_never_call_traffic_flows` added to
  `test_planner_trips_branch.py` (real `_corridor_eta_adapter`, monkeypatched
  `traffic_flows` to raise, `travel_times` to []).
- Validation: full `tests/aws_backend` suite 314 passed (was 312 + 2 new guard
  cases). tsc not needed (backend-only). Lints clean.
- Local micro-benchmark (4 stub legs x 100 ms): concurrent `plan_connection`
  ~105 ms vs ~400 ms sequential floor (~3.8x). Real-source confirmation deferred
  to WP4 L1 (EC2 re-benchmark).
- Status: WP3 complete for T1 + T2. Held for operator commit; WP4 Adversarial
  (L1 perf-regression on EC2, L2 honesty, L3 failure-edge) not yet run.

## 2026-06-28 — committed + WP4 adversarial

- Committed WP3 (T1+T2) + charter as `82edeec` (only WS-PERF files staged; not
  pushed). Large unrelated working tree left untouched.
- WP4 layers: L1 PARTIAL (local ~3.8x; real-source EC2 re-benchmark pending),
  L2 PASS (honesty/labels/freshness identical), L3 PASS (added two failure
  injection tests; degrade-to-unknown, no crash, no fabrication), L4 N/A (T3
  shipped no code). `DEFECT_REGISTER.md` filed: no blocking/major defects; D-1
  (per-call executor) and D-2 (log string) deferred with rationale.
- WP4 test suite: test_planner_trips_branch.py 18 passed.
- Remaining before WP6 acceptance: the L1 real-source EC2 re-benchmark
  (billable, operator-gated).

## 2026-06-28 — operator gate: L1 EC2 deferred

- Operator chose to hold the EC2 re-benchmark; local ~3.8x synthetic proof +
  the L2/L3 test evidence stand as the perf verdict for now.
- WP4 closed: L2/L3 PASS, L1 PARTIAL (real-source confirmation deferred), L4
  N/A. WP5 remediation: nothing blocking (D-1/D-2 deferred with rationale).
- WP6 acceptance: HELD on the deferred L1 re-benchmark. Not signed off.
- Commits 82edeec + 4d2dd73 on main, NOT pushed.

## 2026-06-28 — T4 activated, research+discovery done

- Operator chose research-first on T4 (streamed narration). Ran three read-only
  investigators (backend Bedrock, proxy transport, frontend render).
- Findings (`T4_RESEARCH_SYNTHESIS.md`, `T4_DISCOVERY_MAP.md`): the code is
  low-risk on all three layers (invoke_model_with_response_stream + SSE; proxy
  resp.body pass-through; rAF-batched setTurns append). The REAL risk is the
  transport chain: `/api/be` buffers today (resp.text), and prod now routes
  Vercel -> Next -> cloudflared -> uvicorn (App Runner = rollback), with possible
  buffering at Vercel and Cloudflare that we do not fully control. Also: narrate
  is missing from the proxy public POST allow-list (anonymous 401).
- Recommendation: a thin TRANSPORT SPIKE first (prove an SSE byte stream reaches
  the browser unbuffered through the prod chain) before building the full Bedrock
  endpoint + progressive UI. Held for operator gate.

## 2026-06-28 — T4 graduated to WS-STREAM

- Operator: rather than a one-off spike, charter a waveset to research, benchmark,
  and discover a higher-reward streaming method that solves the transport flags.
- T4 graduated out of WS-PERF into WS-STREAM
  (.cca/catalogue/O0/20260628_console-ws-stream/), a seven-wave waveset (adds a
  Benchmark wave). WS-PERF T1/T2 shipped, T3 no-fix, T4 graduated -> WS-PERF can
  close.

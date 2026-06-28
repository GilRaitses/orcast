# WS-PERF defect register (WP4 adversarial)

Adversarial review of the WP3 implementation (commit `82edeec`). Layers per
`wave_shape.yml` WP4. Severities: blocking / major / minor / info.

## Layer results

| Layer | Dimension | Verdict | Notes |
|-------|-----------|---------|-------|
| L1 | performance-regression | PARTIAL | Local synthetic confirms ~3.8x (4x100 ms legs: ~105 ms vs ~400 ms floor). Full real-source EC2 re-benchmark is the remaining acceptance step (billable, operator-gated). |
| L2 | correctness-honesty | PASS | Happy-path labels, composite, freshness, and feasibility are identical to baseline (existing visiting/here-now tests, unchanged assertions). Unknown-vs-zero preserved. No defect. |
| L3 | failure-edge | PASS | Added two injection tests: a single-leg outage degrades that leg to unknown while survivors still label the leg / composite / freshness; a total outage returns a fully-unknown plan without crashing. No defect. |
| L4 | frontend-visual-perf | N/A | T3 closed with no code change (live `/3dtwin/full/` L0 root ~0.97 MB < 1.5 MB goal). No frontend diff shipped, so no visual regression is possible. |

## Defects filed

### D-1 (minor, deferred) — per-call ThreadPoolExecutor

`plan_connection` creates a fresh `ThreadPoolExecutor` per ferry-branch turn (up
to 4 short-lived worker threads on top of the sync FastAPI worker thread).
Acceptable at current load; under high request concurrency it multiplies thread
churn. Recommendation: revisit a shared module-level bounded executor if request
volume grows. Deferred with rationale; not blocking the target.

### D-2 (info) — leg-failure log string changed

A failed leg now logs `fanout: leg <key> failed` instead of the prior
`connections: wsf.<x> failed`. No functional or honesty impact; the downstream
unknown handling is identical. No action.

## Gate (WP4)

Register complete and triaged. No blocking or major defects. The two minor/info
items are deferred with rationale. The only open item before acceptance (WP6) is
the L1 real-source EC2 re-benchmark.

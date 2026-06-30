# orcast provenance ledger

Rendered from
[GP-LEDGER.json](../../../.cca/catalogue/O0/20260630_grounding-post/findings/GP-LEDGER.json).
repo_state_verified_against: orcast `e794dbd`. Dates America/New_York. Anything
undated is marked UNDATED and never invented.

## Pointer record

- Decisions: 9, in `.ddb/decisions/`. Seven active, two superseded.
- Registered states: 9, in `.sst/`, listed in `.ddb/registry.json`.
- Receipts: 9, in `.ddb/receipts/`, each a subordinate human-readable mirror of
  its decision.
- Step logs: 30, the actor log `.cca/STEP_LOG.md` plus 29 lane logs under dated
  homes.
- Action timeline span: 2026-06-24 to 2026-06-30.
- Graph: 57 nodes, 37 edges.

The mlops lane log contains a 2026-05-01 token inside an entry. That is a dataset
window reference, not an orchestration action, so the action timeline starts at
the first actor-log entry on 2026-06-24.

## Decisions

| decision id | date | kind | registry status | state artifact | repo anchor |
|---|---|---|---|---|---|
| orcast_system_state_baseline_v1_20260626 | 2026-06-26 | system_state_baseline | superseded | .sst/system_state_baseline_v1.json | 95a6d95 |
| orcast_gp_preflight_v1_20260626 | 2026-06-26 | gp_preflight_result | active | .sst/gp_preflight_v1.json | 95a6d95 |
| orcast_system_state_baseline_v2_20260627 | 2026-06-27 | system_state_baseline | superseded | .sst/system_state_baseline_v2.json | 5a7e2e8 backend, 77d4d0c frontend |
| orcast_adversarial_final_gate_v1_20260627 | 2026-06-27 | adversarial_final_gate_result | active | .sst/ax_adversarial_final_gate_v1.json | 87ff466 |
| orcast_hosting_consolidation_v1_20260628 | 2026-06-28 | hosting_topology_decision | active, re-registered | .sst/hosting_consolidation_v1.json | 6af4eeb |
| orcast_system_state_baseline_v3_20260628 | 2026-06-28 | system_state_baseline | active | .sst/system_state_baseline_v3.json | 6af4eeb |
| orcast_selfhost_decommission_v1_20260628 | 2026-06-28 | selfhost_decommission_result | active | .sst/selfhost_decommission_v1.json | 85675c0 |
| orcast_coldstart_mitigation_v1_20260628 | 2026-06-28 | coldstart_mitigation_result | active | .sst/coldstart_mitigation_v1.json | UNVERIFIED, no field in decision |
| orcast_tracked_limits_register_v1_20260628 | 2026-06-28 | tracked_limits_register | active | .sst/tracked_limits_register_v1.json | UNVERIFIED, no field in decision |

The hosting-consolidation decision has two registry entries under one decision id.
It was re-registered on 2026-06-28 at 15:11 UTC. The earlier registry entry is
superseded and the later is active.

## Dated timeline

| date | event |
|---|---|
| 2026-06-24 | Actor log opens. Vercel frontend deploy, Playwright agent path, whitepaper 1 build, figure audit, multi-panel figures. |
| 2026-06-25 | Search-cycle sources, scrutiny gates, uploads and account UI, primary-anchor claim gate, prose tightening, finalize pass. |
| 2026-06-26 | System-state baseline v1 ratified. GP preflight pass v1 ratified. Self-host cutover catalogued. Backend committed in logical commits, interest endpoint resolved, demo video pipeline run. |
| 2026-06-27 | System-state baseline v2 ratified. Adversarial final-gate clean pass ratified. Console journey, intent, scenic, bathy, trips, the twin, forecast candidates, mlops, wildlife sources, open-science integration catalogued. |
| 2026-06-28 | Hosting consolidation, system-state baseline v3, self-host decommission, cold-start mitigation, and tracked-limits register all ratified. Console perf and stream, visual pass, copy redaction, water-fx, orca twin, render host catalogued. |
| 2026-06-29 | B-side acoustic and behavior workbench, the BSW dispatch handoff, the BSW follow-up remediation, and the demo-production recut catalogued. |
| 2026-06-30 | Grounding-post lane opens. This catalog, schema finding, provenance ledger, and grounding post authored. |

## Step-log index

The actor log spans 2026-06-24 to 2026-06-26 with 64 dated lines. Lane logs by
first and last dated entry:

| lane log | first | last | dated lines |
|---|---|---|---|
| explore3d-handoff | 2026-06-26 | 2026-06-26 | 8 |
| orcast-selfhost-cutover | 2026-06-26 | 2026-06-26 | 1 |
| sd-deploy-handoff | UNDATED | UNDATED | 0 |
| 3d-twin | UNDATED | UNDATED | 0 |
| bside-build | 2026-06-27 | 2026-06-27 | 1 |
| console-journey-trips | 2026-06-27 | 2026-06-27 | 9 |
| console-ws-bathy | 2026-06-27 | 2026-06-27 | 8 |
| console-ws-intent | 2026-06-27 | 2026-06-27 | 4 |
| console-ws-scenic | 2026-06-27 | 2026-06-27 | 3 |
| console-ws-trips | 2026-06-27 | 2026-06-28 | 2 |
| demo-waveset | 2026-06-27 | 2026-06-27 | 3 |
| forecast-candidates | 2026-06-27 | 2026-06-27 | 2 |
| mlops-handoff | UNDATED | UNDATED | 0 |
| mlops | 2026-06-27 | 2026-06-28 | 29 |
| open-science-integration | 2026-06-27 | 2026-06-27 | 11 |
| orcast-handoff | UNDATED | UNDATED | 0 |
| os1-launch-handoff | 2026-06-27 | 2026-06-27 | 1 |
| signal-modeling-launch-handoff | UNDATED | UNDATED | 0 |
| terrain-bathymetry-twin | 2026-06-27 | 2026-06-27 | 2 |
| trips-launch-handoff | 2026-06-27 | 2026-06-27 | 1 |
| wildlife-sources | 2026-06-27 | 2026-06-27 | 1 |
| apprunner-coldstart | 2026-06-28 | 2026-06-28 | 4 |
| console-visual-pass | 2026-06-28 | 2026-06-28 | 9 |
| console-ws-perf | 2026-06-28 | 2026-06-28 | 12 |
| console-ws-stream-handoff | UNDATED | UNDATED | 0 |
| console-ws-stream | 2026-06-28 | 2026-06-28 | 11 |
| hosting-consolidation-followups | 2026-06-28 | 2026-06-28 | 5 |
| bsw-dispatch-handoff | UNDATED | UNDATED | 0 |
| grounding-post | 2026-06-30 | 2026-06-30 | 3 |

Seven lane logs are UNDATED. They are rotation and dispatch packets whose dated
entries live in the program homes they point to.

## Dependency and supersession graph

Supersession, decision replaces decision:

- system-state baseline v2 supersedes baseline v1.
- system-state baseline v3 supersedes baseline v2.
- hosting consolidation supersedes the prior deploy-decision items DD-1 and DD-2
  recorded in `.cca/DEPLOY_DEMO_DECISIONS.md`. Those are deploy-decision items,
  not registered decisions.

Parent and anchor, decision derives from decision:

- self-host decommission has parent hosting consolidation.
- cold-start mitigation has parent self-host decommission.
- tracked-limits register anchors on system-state baseline v3.

Reference, decision cites decision in its related block:

- GP preflight references baseline v1.
- baseline v2 references GP preflight.
- adversarial final gate references baseline v2 and GP preflight.
- hosting consolidation references baseline v2 and baseline v3.
- baseline v3 references hosting consolidation.

Lane to decision, a catalogued lane produced or drove a decision:

- orcast-selfhost-cutover produced baseline v1 and the GP preflight.
- console-ws-stream drove the hosting consolidation through its streaming
  benchmark.
- hosting-consolidation-followups produced the self-host decommission, wave
  WS-HOSTFOLLOWUP FW2.
- apprunner-coldstart produced the cold-start mitigation, wave WS-COLDSTART CS4.

State and receipt, each decision has one registered state artifact and one
subordinate receipt, as listed in the decisions table above.

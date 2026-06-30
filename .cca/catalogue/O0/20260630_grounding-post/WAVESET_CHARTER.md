# GP, grounding post, WAVESET_CHARTER

Family: GP. Home: `.cca/catalogue/O0/20260630_grounding-post/`. Actor: O0.
repo_state_verified_against: orcast `e794dbd`.

A documentation and reconciliation lane, aligned to the pax GP grounding-post
orchestrator. It stands up a per-project grounding post that presents a project
through nine fixed ordered perspectives, a charter index, and a code index
(each waveset to its landing commits and key files), plus a provenance ledger
(the decision ledger and every step log with dates, a timeline, and a
dependency and supersession graph), and one consolidated grounding surface that
indexes the project and all its wavesets.

Root work is reconciliation, not transcription. Enumerate every family in the
registry and every dated home, including unregistered lanes, map each waveset to
real code verified against the orcast git log, reconcile any inline STALE
corrections, and mark anything unverifiable UNVERIFIED.

In-scope instantiation for this lane: orcast. The same template is reusable for
other projects (pax, aimez, IST675, PHY600) as roadmap, filled when those repos
are local and in scope.

## The nine fixed perspectives

Named exactly, in this order, in every post, even when a section is "none
known":

1. Critical gap
2. Concept
3. Construction
4. Costs
5. Qualifications
6. Limits and tracked boundaries
7. Risks
8. Future direction
9. Outcomes

## Provenance sources (for GP-PROVENANCE and GP-LEDGER)

| What | Where (orcast) |
|---|---|
| The waveset list and statuses | `docs/devpost/waves.registry.yaml` (note: orcast uses this path, not `.cca/waves.registry.yml`) |
| Prose registry index | `docs/devpost/WAVES_REGISTRY.md` |
| The decision ledger | `.ddb/` (`decisions/` 9, `receipts/` 9, `registry.json`, `tools/`; orcast has no `PROTOCOL.md`, `decisiondb_bridge_refs.json`, or `cbp_pilot/`) |
| State surface | `.sst/` (9 state json files, read-only) |
| Step logs (actor-level) | `.cca/STEP_LOG.md` (orcast is single-actor O0; this is the root actor log) |
| Step logs (lane-level) | every `STEP_LOG.md` under a dated home, 28 files (`find .cca/catalogue -name STEP_LOG.md`) |

## Waves and phasing

### Wave 0, discovery (read-only)

- GP-INVENTORY. The authoritative waveset list across the registry families and
  the catalogued dated homes, including unregistered lanes. DONE: see
  `dispatch/CATALOG/CATALOG.md` coverage rollup.
- GP-CODE-MAP. Each waveset to its landing commits and key files, verified
  against the orcast git log. DONE: see the four area tables in
  `dispatch/CATALOG/CATALOG.md`.
- GP-SCHEMA. Resolve the schema fork. orcast carries a machine registry
  (`docs/devpost/waves.registry.yaml`) and a prose index
  (`docs/devpost/WAVES_REGISTRY.md`), plus catalogued dirs with no registry
  family and families with no dir. Declare the authoritative schema and record
  the resolution.
- GP-PROVENANCE. Inventory the decision ledger and every step log with dates and
  a timeline, as a pointer record of all references plus a dependency and
  supersession graph. Walk `.ddb/` (each decision id, date, supersession edge,
  and its `.sst` state file), the actor-level `.cca/STEP_LOG.md`, and all 28
  lane-level step logs (extract each dated entry). Emit
  `findings/GP-LEDGER.json` (machine-readable nodes and edges). Dates are
  America/New_York; anything undated is marked UNDATED and never invented.
- GP-ADV. Adversarial review of the Wave 0 findings: completeness, traceability,
  and any overclaim. Loops back to the relevant W0 member on a miss.

### Wave 1, build (new files)

- GP-TEMPLATE. Finalize `GROUNDING_POST_TEMPLATE.md` (the nine sections, the
  charter index, the code index).
- GP-POST. Author `orcast_grounding_post.md` on the derived reports surface,
  filling the nine sections for orcast against the catalog and the ledger.
- GP-INDEX. Author `INDEX.md`, the consolidated surface that indexes the project
  and all wavesets, with the other projects as roadmap entries.
- GP-LEDGER. Render `LEDGER.md` on the derived surface from
  `findings/GP-LEDGER.json`: the pointer record of all references, the dated
  timeline, and the dependency and supersession graph.

### Wave 2, GP-CONSOLIDATE (GATED)

Operator gate. Register the lane in `docs/devpost/waves.registry.yaml`, land
`INDEX.md`, `orcast_grounding_post.md`, and `LEDGER.md` on the derived surface
(candidate `docs/devpost/grounding/`, operator confirms), then commit and push.
The sub-orchestrator does not commit; it pauses here and reports the gate ask.

### Wave 3, GP-ACCEPT

Link-and-commit verification: every cited commit resolves in the orcast git log,
every internal link resolves, every waveset in the catalog appears in the index.

## Locked rules

1. All nine sections are named exactly, in order, even when the content is "none
   known".
2. Outcome means landed and verifiable. Aspiration is Future direction, never
   Outcomes.
3. Reconciliation, not transcription. Verify every waveset to code claim against
   the orcast git log. Reconcile inline STALE corrections. Mark anything
   unverifiable UNVERIFIED.
4. Honesty locks travel into the post unchanged: modeled-not-measured forecast
   labels, CV estimates labeled as estimates, simulated-user proxies labeled as
   proxies, no canonical sigma claimed, representativeness and presence-gating
   carried as written.
5. Dates are America/New_York. UNDATED is never invented.
6. Plain language. No promotional framing, no synthetic contrast, no em-dashes.

## Return contract to the dispatching O0

- Wave 0: the four findings (inventory, code map, schema resolution, provenance
  ledger), the authoritative waveset list, the code map, the resolved schema
  fork, and any ESCALATION TO O0.
- Wave 1: the grounding post plus the index plus the ledger, and the
  link-and-commit verification result.

## Escalation catch

Subagents escalate to the lane O0, the lane O0 escalates to the dispatching O0.
Never the operator.

## Files

- `WAVESET_CHARTER.md` this umbrella authority.
- `GROUNDING_POST_TEMPLATE.md` the post contract (nine sections, charter index,
  code index).
- `ORCHESTRATOR_DISPATCH_PROMPT.md` the cold one-liner plus the full dispatch.
- `README.md` overview.
- `STEP_LOG.md` the lane step log.
- `dispatch/CATALOG/CATALOG.md` the GP-INVENTORY and GP-CODE-MAP output.
- `dispatch/CATALOG/parts/` the four area fragments behind CATALOG.md.
- `findings/GP-LEDGER.json` the provenance ledger nodes and edges (GP-PROVENANCE
  output, written by the lane).

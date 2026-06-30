# GP, grounding post (orcast)

A grounding post for orcast, aligned to the pax GP orchestrator pattern. One
document a reader can stand on to understand the whole project through nine
fixed perspectives, backed by a charter index, a code index, and a provenance
ledger.

The project history is real but scattered across 38 catalogued programs under
`.cca/catalogue/O0/`, the machine registry `docs/devpost/waves.registry.yaml`,
the prose index `docs/devpost/WAVES_REGISTRY.md`, the decision ledger `.ddb/`,
the state surface `.sst/`, and 29 step logs. This lane reconciles all of it and
consolidates one surface.

## What it produces

1. A catalog (GP-INVENTORY and GP-CODE-MAP): every waveset to its code and
   outcome. Done at `dispatch/CATALOG/CATALOG.md`.
2. A provenance ledger (GP-PROVENANCE and GP-LEDGER): the decision ledger and
   every step log with dates, a timeline, and a dependency and supersession
   graph. Emits `findings/GP-LEDGER.json` and the rendered
   `docs/devpost/grounding/LEDGER.md`.
3. The grounding post (GP-POST): the nine perspectives filled for orcast.
4. The consolidated index (GP-INDEX): the project and all wavesets, other
   projects as roadmap.

## Nine perspectives

Critical gap, concept, construction, costs, qualifications, limits and tracked
boundaries, risks, future direction, outcomes. Named exactly, in order, in every
post.

## Files

- `WAVESET_CHARTER.md` umbrella authority: waves, phasing, locked rules, return
  contract, escalation catch, provenance sources.
- `GROUNDING_POST_TEMPLATE.md` the post contract.
- `ORCHESTRATOR_DISPATCH_PROMPT.md` the cold one-liner plus the full dispatch.
- `STEP_LOG.md` the lane step log.
- `dispatch/CATALOG/CATALOG.md` the inventory and code map.
- `findings/GP-LEDGER.json` the provenance ledger (written by the lane).

## Phasing

W0 discovery (GP-INVENTORY, GP-CODE-MAP, GP-SCHEMA, GP-PROVENANCE, GP-ADV; read
only) then W1 build (GP-TEMPLATE, GP-POST, GP-INDEX, GP-LEDGER; new files) then
W2 GP-CONSOLIDATE (GATED: register plus land plus commit and push) then W3
GP-ACCEPT (link and commit verification).

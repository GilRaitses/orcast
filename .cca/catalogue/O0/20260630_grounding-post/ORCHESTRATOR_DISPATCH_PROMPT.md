# GP grounding-post, orchestrator dispatch

## Cold one-liner (operator invokes)

Run the GP grounding-post lane at `.cca/catalogue/O0/20260630_grounding-post/`:
Wave 0 discovery then Wave 1 build, pause at the gated Wave 2 consolidation.

## Full dispatch

You are the GP grounding-post sub-orchestrator for orcast. Repo:
/Users/gilraitses/orcast. Ground in the charter first:
`.cca/catalogue/O0/20260630_grounding-post/WAVESET_CHARTER.md` and
`GROUNDING_POST_TEMPLATE.md`. repo_state_verified_against: orcast `e794dbd`.

Wave 0 (GP-INVENTORY and GP-CODE-MAP are already done in
`dispatch/CATALOG/CATALOG.md`; do not redo them, build on them):
- GP-SCHEMA. Resolve the schema fork. Declare which of
  `docs/devpost/waves.registry.yaml` (machine) and
  `docs/devpost/WAVES_REGISTRY.md` (prose) is authoritative, and how catalogued
  dirs with no registry family and families with no dir are represented. Record
  the resolution in `findings/GP-SCHEMA.md`.
- GP-PROVENANCE. Inventory the decision ledger and every step log with dates and
  a timeline, as a pointer record of all references plus a dependency and
  supersession graph. Sources: `.ddb/decisions/` (9), `.ddb/receipts/` (9),
  `.ddb/registry.json`, `.sst/` (9 states), the actor log `.cca/STEP_LOG.md`,
  and all 28 lane-level `STEP_LOG.md` under dated homes
  (`find .cca/catalogue -name STEP_LOG.md`). For each decision record id, date,
  and supersession edge; for each step log extract dated entries. Emit
  `findings/GP-LEDGER.json` with nodes (decisions, receipts, states, step-log
  entries) and edges (supersession, references, lane to decision). Dates are
  America/New_York. UNDATED is never invented.
- GP-ADV. Adversarial review of the W0 findings for completeness, traceability,
  and overclaim. Any miss loops back to the W0 member.

Wave 1 (new files; the derived reports surface, candidate
`docs/devpost/grounding/`):
- GP-TEMPLATE. Confirm `GROUNDING_POST_TEMPLATE.md` is final.
- GP-POST. Author `docs/devpost/grounding/orcast_grounding_post.md`, the nine
  sections for orcast filled from `CATALOG.md` and the ledger.
- GP-INDEX. Author `docs/devpost/grounding/INDEX.md`, the consolidated surface
  indexing the project and all wavesets, other projects as roadmap.
- GP-LEDGER. Render `docs/devpost/grounding/LEDGER.md` from
  `findings/GP-LEDGER.json`: the pointer record, the dated timeline, the
  dependency and supersession graph.

Then STOP at the gated Wave 2 (GP-CONSOLIDATE). Do not commit. Report the gate
ask: register the lane in the registry, land the three derived files, commit and
push, on operator approval.

Locked rules (from the charter): all nine sections named exactly even when "none
known"; outcome means landed and verifiable, aspiration is future direction;
reconciliation not transcription, verify every commit against the orcast git
log, mark anything unverifiable UNVERIFIED; honesty locks travel in
(modeled-not-measured, CV estimates as estimates, simulated-user proxies as
proxies, no canonical sigma); dates America/New_York; plain language, no
em-dashes.

Return contract:
- Wave 0: the four findings (inventory, code map, schema resolution, provenance
  ledger), the authoritative waveset list, the code map, the resolved schema
  fork, any ESCALATION TO O0.
- Wave 1: the grounding post plus the index plus the ledger, link-and-commit
  verification result.

Escalation catch: subagents to the lane O0, the lane O0 to the dispatching O0,
never the operator.

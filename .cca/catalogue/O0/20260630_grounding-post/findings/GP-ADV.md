# GP-ADV, adversarial review of the Wave 0 findings

Wave 0 closing review. Scope is the four W0 findings: GP-INVENTORY and
GP-CODE-MAP in `dispatch/CATALOG/CATALOG.md`, GP-SCHEMA in
`findings/GP-SCHEMA.md`, and GP-PROVENANCE in `findings/GP-LEDGER.json`.
Tests are completeness, traceability, and overclaim. repo_state_verified_against
orcast `e794dbd`. Dates America/New_York.

## Verdict

PASS with six reconciliations recorded below. No finding was dropped. No claim
of landed work survived without a trace. The loop-backs were applied in place,
not deferred.

## Completeness

- Inventory. CATALOG enumerates every catalogued program directory and every
  registry family. The working tree holds 39 program directories under
  `.cca/catalogue/O0/`. The four area tables enumerate all 39.
- Code map. Every resulting-code cell cites a path and at least one commit, or
  states that nothing landed.
- Schema. The fork is resolved and the authoritative surface is declared.
- Provenance. The ledger holds 9 decisions, 9 states, 9 receipts, and 30 step
  logs as nodes, with supersession, parent, anchor, reference, and
  lane-to-decision edges. 57 nodes, 37 edges.

## Traceability

- Commit resolution. Every commit cited in CATALOG resolves in the orcast git
  log. The step-log commits also resolve, with one exception explained below.
- Decision-to-state. Each of the 9 decisions points to a registered `.sst`
  artifact present on disk and listed in `.ddb/registry.json`.
- Supersession. v2 supersedes v1 and v3 supersedes v2, confirmed in both the
  decision YAML and the registry status fields. Two decisions are superseded,
  seven are active.

## Reconciliations applied

1. STALE pointer. The CATALOG GND row points at
   `.cca/catalogue/O0/20260630_project-grounding-surface/PROGRAM.md`. The lane
   home was renamed to `.cca/catalogue/O0/20260630_grounding-post/`. CATALOG was
   authored before the rename. Marked STALE, reconciled to the current home.
2. Directory count. The CATALOG coverage rollup states 38 catalogued
   directories. The working tree holds 39, and the area tables enumerate 39, 38
   prior programs plus the grounding program. The 38 line is STALE, reconciled
   to 39. All 39 are covered.
3. Step-log count. The dispatch states 28 lane-level step logs. The find returns
   29, the extra being this grounding lane's own log. Reconciled, 28 prior plus
   this lane.
4. The token `3ff9429` in the tracked-limits receipt is the registry decision id
   prefix `3ff942923bf3...` for the tracked-limits register, not a git commit.
   The git log has no such commit. This is correct as written, not a defect, and
   is recorded so the LEDGER does not read it as a commit.
5. Repo anchor gaps. The coldstart-mitigation and tracked-limits decisions carry
   no `repo_state_verified_against` field, unlike the other seven. Their repo
   anchor is marked UNVERIFIED in the ledger. The landing commits for the
   coldstart work, `b9e2e13` and `27e8a97`, resolve in git, so the work itself is
   traced even though the decision record omits the anchor.
6. Timeline outlier. The mlops step log contains a `2026-05-01` token inside an
   entry. That is a dataset window reference, not an orchestration action. The
   action timeline therefore starts `2026-06-24`, the first actor-log entry, and
   runs to `2026-06-30`.

## Overclaim check, honesty locks intact

- Forecast skill. The forecast is modeled, not measured against held-out skill
  at the promotion bar. The catalog records L2 measured no-go at 0 percent
  promoted and L3 withheld. Effective confidence is 0 percent. Carried as
  written.
- Detectability. The open-science detectability offset is a measured no-go,
  banked physics, confidence 0.0. Carried as written.
- Orca motion. The orca is a modeled animal with simulated DTAG kinematics, not
  measured animal motion. Carried as written.
- Cold-start gap. The gap-equals-zero claim is a measured result from
  `tools/testing/coldstart_gap_probe.py` under a forced transition, not a
  modeled estimate. The warm-pool cost delta is labeled an estimate.
- CV numbers and proxies. CV figures stay labeled as estimates and simulated-user
  paths stay labeled as proxies, no canonical sigma is introduced.

No loop-back to a W0 member changed a verdict from negative to positive. The
gates that decline to promote stay declined.

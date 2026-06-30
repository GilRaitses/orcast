# GROUNDING_POST_TEMPLATE

The contract for `<project>_grounding_post.md`. The post passes GP-ADV and
GP-ACCEPT only if every item here holds. Reusable across projects; the orcast
instance fills it.

## Structure

1. Header: project name, one-paragraph statement of what it is, the live
   surfaces (URLs), the repo, and `repo_state_verified_against` (the commit).
2. How to read this: the nine perspectives and a one-line pointer to the catalog
   and the ledger.
3. The nine sections, named exactly, in order. Present even when "none known".
   1. Critical gap
   2. Concept
   3. Construction
   4. Costs
   5. Qualifications
   6. Limits and tracked boundaries
   7. Risks
   8. Future direction
   9. Outcomes
4. Charter index: every catalogued program and every registry family, each
   linking to its charter and its catalog row.
5. Code index: each waveset to its landing commits and key files.
6. Provenance pointer: a link to `LEDGER.md` (the decision ledger and step-log
   timeline and dependency graph).

## Section rules

- Construction links to the catalog matrix and names the major code areas with
  representative paths.
- Costs names the real cloud services and the GPU render host instance type and
  the pricing basis. Any figure that is an estimate says so.
- Qualifications cites measured results and their source (the uncited-claim-rate
  benchmark, gate verdicts, cited data sources, held-out evaluation), with CV
  numbers labeled as estimates.
- Outcomes lists landed and verifiable work only, each with a commit and a live
  surface. Future direction lists not-yet-shipped work, labeled as such. The two
  never overlap.
- Limits and tracked boundaries, and Risks, are concrete and specific to the
  project, not generic.

## Locks carried into the post

- Outcome means landed and verifiable; aspiration is Future direction.
- Honesty locks travel in unchanged: modeled-not-measured, CV estimates labeled
  as estimates, simulated-user proxies labeled as proxies, no canonical sigma,
  representativeness and presence-gating as written.
- Every factual claim resolves to a charter path, a git commit, a code path, or
  a live surface. Unverifiable items are marked UNVERIFIED.

## Style

Plain, direct language. No promotional framing, no synthetic contrast, no
em-dashes. State properties directly (modeled-not-measured, representativeness,
gated) rather than asserting a quality word.

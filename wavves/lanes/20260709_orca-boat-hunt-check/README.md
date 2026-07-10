# HCHK: orca-boat-hunt-check

Adversarial sanity-check lane for the `HUNT` (orca-boat-hunt) lane's readiness
to run `HUNT-INT` (the gated integration wave). Read-only. No build, no
implementation plan, no code edits, no commits.

Artifact under review: `wavves/lanes/20260709_orca-boat-hunt/waveset.md`
(specifically the `HUNT-INT`/`HUNT-ACCEPT` sections, the two fresh
`decisions/HUNT-*.md` locks, and the acceptance criteria) plus the actual
delivered code in `web/lib/scene/{orcaPilot,boats,sonar}/` and the
`OrcaController.ts` diff, since a plan for integrating code that does not
actually match the plan's assumptions is not a safe plan.

Files:

- `waveset.md` - the check-lane authority doc.
- `dispatch.md` - the fenced paste block for the 4 parallel reviewers.
- `findings/` - one file per lens (grounding, contradictions, completeness,
  adversarial), plus the reconciled verdict.

Status: chartered, dispatching Wave 1 now. See `wavves/registry.yml` for the
registry entry (code `HCHK`).

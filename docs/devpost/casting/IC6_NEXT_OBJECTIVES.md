# Wave Set IC6/J — surface planner close dossier

**Date:** 2026-06-23  
**Preflight / charter:** [J0_SURFACE_PLANNER_CHARTER.md](J0_SURFACE_PLANNER_CHARTER.md)  
**Schema:** [UI_INTENT_SCHEMA.md](UI_INTENT_SCHEMA.md)

## IC6/J verdict

**Deployed to production.** App Runner `ic6-20260624` (via env-preserving `update-service`; CFN-only deploy rolled back). H0 Vercel `dpl_3gQ2U3yda89ymCxzKi1Vw9hzvEYp`. Keyed `/api/interactions/plan` returns `ui_intent` with `plan_output` step. `/explore?planner=1` shows surface planner mode.

## Deploy record

| Target | Artifact | Result |
|--------|----------|--------|
| App Runner | `orcast-aws-backend:ic6-20260624` | `/plan` live; panels on decision-audit message |
| DynamoDB | 4 cast roles seeded (`--all`) | `surface-planner-v1` + J1 roles |
| Vercel H0 | `dpl_3gQ2U3yda89ymCxzKi1Vw9hzvEYp` | `/explore?planner=1` planner banner live |

## Gate commands

```bash
./tools/waves/run-gate.sh ic6-local    # PASS
./tools/waves/run-gate.sh ic6-doc-grep # PASS
./tools/waves/run-gate.sh ic6-gate     # PASS 2026-06-24
./tools/waves/run-gate.sh ic-gate      # regression PASS
```

## Open (post-IC7)

1. ~~**Deploy** App Runner image with `/plan` route~~ — **done** (`ic6-20260624`, merge env on image updates)
2. **Step Functions callback** — invoke `promotion-clerk-v1` on human-wait (future)
3. **Structured LLM planner** — replace keyword rules with schema-validated Haiku output
4. **Deploy hygiene** — CFN `ContainerImage` param vs live tag; prefer `update-service` env merge after CFN

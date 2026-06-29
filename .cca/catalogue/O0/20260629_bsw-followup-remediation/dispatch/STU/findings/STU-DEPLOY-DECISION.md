# STU-ACCEPT deploy gate — O0 decision

- Lane `BSWR-STU` (studio-live-persistence). Decider: O0.
- Resolves the BLOCKED escalation in `STU-ACCEPT_VERDICT.md` (deploy path + table name).
- Repo base pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.

## Context

STU-ACCEPT mapped the real topology (read-only AWS calls, nothing created or
committed) and found the staged deploy is a production CloudFormation + CI
operation that collides with the no-commit lock. App Runner `orcast-aws-backend`
is image-based with `AutoDeploymentsEnabled:false`; the nine live tables and all
`ORCAST_*` env are CloudFormation-managed in `infra/aws/template.yaml`; live tables
use the `orcast-aws-backend-` prefix. The route is not live.

## Decisions

1. **Deploy method = Path A (commit-then-CI). Path B is REJECTED.**
   The STU backend passed STU-ADV at zero open P0/P1 (21 + 51 tests green, tsc
   clean). It goes to production the disciplined way: commit the backend route +
   the `infra/aws/template.yaml` change (the tenth `AWS::DynamoDB::Table`, the
   `ORCAST_DTAG_ANNOTATIONS_TABLE` env var, and the instance-role IAM grant for the
   new table), push, and let the existing `aws-deploy.yml` workflow build the
   committed SHA through CI + CloudFormation with the smoke test intact.
   Path B (local Docker build of the dirty working tree pushed to prod ECR +
   imperative `cloudformation deploy`) is rejected: it ships unreviewed code to
   production, bypasses CI/IaC/review, and risks IaC drift and a missing
   instance-role grant. The locks exist precisely to prevent that.

2. **Table name = `orcast-aws-backend-dtag-annotations`** (matches the live
   CloudFormation prefix). `ORCAST_DTAG_ANNOTATIONS_TABLE` is set to the same value.
   O0's earlier `orcast-dtag-annotations` shorthand is superseded.

3. **Provision via IaC, not imperative.** The table is created by the
   `template.yaml` change through `cloudformation deploy` in the CI workflow, not by
   a standalone `create-table`, so the instance-role grant and tags stay consistent.

## Sequencing consequence

Path A requires a commit, and commit/push is the operator's final gate. Therefore
**STU's deploy folds into the consolidated BSWR commit+deploy gate**, which O0
brings to the operator after the GPU/box ACCEPT captures (OCN, ENV, PRF, ACX
Path-B) are reconciled and Read-examined. The no-commit lock holds until then.

STU-ACCEPT is PARKED (not failed). The instant the consolidated commit lands and
`aws-deploy.yml` deploys the committed SHA + the new table + env, STU-ACCEPT runs
the staged create -> list -> get + idempotency + 401 checks against the live route
and rewrites `STU-ACCEPT_VERDICT.md` with the real responses. Everything else
(route, memory + AWS stores, offline tests, proxy doc line, agent-token script) is
ready.

## What STU does next

Nothing this rotation. Hold parked. When O0 opens the commit+deploy gate, STU:
1. confirms the `template.yaml` diff (tenth table + env var + IAM grant) is correct,
2. (post-CI-deploy) runs the staged live round-trip and writes the real verdict.

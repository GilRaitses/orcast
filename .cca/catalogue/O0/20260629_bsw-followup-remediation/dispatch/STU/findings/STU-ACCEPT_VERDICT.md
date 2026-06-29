# STU-ACCEPT verdict (studio-live-persistence)

Status: BLOCKED. The live round-trip did not run. No deploy, no provisioning,
no image build, no template edit, and no commit were performed. Only read-only
AWS describe and list calls were made. This file does not cite round-trip
responses because the route is not deployed and could not be deployed without
improvising past a locked constraint.

`repo_state_verified_against`: 61ba1d69ee36cf605f7ba741bdaa1defa8762834

## What the host window revealed

The deploy gate as staged in `STU-ACCEPT-PLAN.md` assumed two simple steps, a
route deploy and a table provision. The real environment makes both steps a
production CloudFormation and CI operation, which collides with the no-commit
lock. Evidence gathered read-only.

- App Runner service `orcast-aws-backend` is RUNNING in `us-west-2`. Service URL
  `pjrftm3bkv.us-west-2.awsapprunner.com`. ARN
  `arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9`.
- The service is image-based ECR with `AutoDeploymentsEnabled: false`. The
  running image is `198456344617.dkr.ecr.us-west-2.amazonaws.com/orcast-aws-backend:ws-stream-874f830`,
  an older commit that does not contain the `/api/dtag/annotations` route.
- `ORCAST_STORAGE_BACKEND=aws` is already set on the live service. There is no
  `ORCAST_DTAG_ANNOTATIONS_TABLE` and no annotations table.
- The nine live DynamoDB tables use the `orcast-aws-backend-` prefix, for example
  `orcast-aws-backend-sightings`, not the `config.py` defaults like
  `orcast-sightings`.
- All nine tables and every `ORCAST_*_TABLE` plus `ORCAST_STORAGE_BACKEND` env var
  are CloudFormation-managed in `infra/aws/template.yaml`. There is no annotations
  table or env var in the template.
- The backend image is built from `tools/deployment/aws/Dockerfile`, which copies
  only `src`, one archive JSON, the hydrophones JSON, and `data/geo`. Sibling-lane
  working-tree edits under `web/` and `modeling/` would not enter the backend
  image. The backend changes that would enter are the STU files only.
- Docker is running locally. AWS identity is account root `198456344617`, so
  credentials are not the blocker.

## Why this is a STOP, not an improvisation

1. No-commit lock versus deploying uncommitted code. The annotation route is
   uncommitted in the working tree. The deploy pipeline builds committed code. The
   GitHub Actions workflow `aws-deploy.yml` checks out the repo and builds the
   image at `github.sha`, then deploys the CloudFormation stack. To make the route
   live without a commit, the only path is to build the dirty working tree locally
   and push it to the production ECR repo, bypassing code review, CI, and the
   workflow smoke test, then redeploy the service. That ships un-reviewed,
   uncommitted code to production. The standing lock says commit and push are a
   separate final O0 gate after Read-examination, so shipping the code ahead of
   that gate is not mine to decide.

2. The table and env var are CloudFormation-managed, not ad hoc. Provisioning the
   table and setting `ORCAST_DTAG_ANNOTATIONS_TABLE` correctly means editing
   `infra/aws/template.yaml` to add a tenth `AWS::DynamoDB::Table`, the env var on
   the App Runner task, and the instance-role IAM grant for the new table, then
   running `aws cloudformation deploy`. That is a production stack deploy and an
   edit to a shared infra template. Doing it imperatively with `create-table` and
   `apprunner update-service` would drift from the IaC source of truth and may
   omit the instance-role grant the running task needs to read and write the new
   table.

3. Table-name convention mismatch. The plan and the methodology named the table
   `orcast-dtag-annotations`. The live convention is `orcast-aws-backend-<name>`,
   so the table and the env value should be `orcast-aws-backend-dtag-annotations`
   to match the existing nine. This needs an O0 confirmation before anything is
   created.

## Decision needed from O0

Pick the deploy path, then I execute that path only.

- Path A, respects the locks. O0 lifts the no-commit lock for STU just enough to
  commit the backend route and the `template.yaml` change, push, and run the
  existing `aws-deploy.yml` workflow so CI builds the committed SHA and deploys the
  stack. This keeps review, CI, the smoke test, and IaC intact. It requires O0 to
  authorize a commit, which is currently forbidden, and to authorize the
  `infra/aws/template.yaml` edit.
- Path B, no commit but bypasses CI and IaC discipline. O0 authorizes a one-off
  local Docker build of the working tree, a push to the production ECR repo, a
  `template.yaml` edit to add the table, env var, and IAM grant, and a
  `cloudformation deploy`. This deploys uncommitted code to production ahead of the
  commit gate. Higher risk.

Also confirm the table name. I recommend `orcast-aws-backend-dtag-annotations`
with the env value set the same, to match the deployed nine-table convention.

## What is ready the moment a path is approved

The backend route, the memory and AWS stores, the offline tests, the proxy
documentation line, and the agent-token round-trip script in `STU-ACCEPT-PLAN.md`
are all in place. Once the route is deployed and the table and env exist, the
staged create, list, get, idempotency, and 401 checks run as written and this
verdict is rewritten with the real responses.

# STU-ACCEPT verdict (studio-live-persistence)

Status: PASS. The DTAG annotation write path is live and the full agent-token
round-trip through the Vercel same-origin proxy passes every pass criterion on
the captured live responses. No commit and no push were performed by this
automation.

`repo_state_verified_against`: 2ac3d78 (HEAD = main)

## Real annotation cited

- `id`: `359004b98cb84dbf843af066d8faaf70`
- `created_at`: `2026-06-29T19:57:38.649295+00:00`
- `deployment_id` / `dataset`: `cascadia_2010_k33_test`

## Deploy and packaging-fix confirmation

- Workflow `aws-deploy.yml` run `28398460857`. Infra steps (ECR push,
  CloudFormation deploy, frontend deploy) all succeeded. The run is marked
  `failure` by GitHub only because of the pre-existing final smoke-test step
  (`GET /api/reports/probability` -> 401 on the auth-gated App Runner origin),
  which is unrelated to this route.
- App Runner `orcast-aws-backend`: `Status = RUNNING` on image tag
  `2ac3d782f3d797be9e21a389e782a75bb060486f` (HEAD `2ac3d78`), which carries the
  Dockerfile fix that ships `data/dtag_analysis_results.json`.
- DynamoDB table `orcast-aws-backend-dtag-annotations`: ACTIVE.
- Packaging fix confirmed live: an authenticated read probe now returns
  `available_deployments: ["cascadia_2010_k33_test"]` (it was empty before the
  redeploy), so the backend loads the bundled simulated deployment.

## Pass criteria, evaluated on live responses

| check | result |
| --- | --- |
| create -> HTTP 200 with `simulated: true` | PASS (`200`, `status:created`, `simulated:true`) |
| every list item and the get response have `simulated: true` | PASS |
| `provenance.license_status == "simulated-example"` | PASS |
| `provenance.dataset == provenance.deployment_id == "cascadia_2010_k33_test"` | PASS |
| `source == "community"`, `annotator_id == "agent_orcast_automation"`, no reviewer email anywhere | PASS |
| idempotency: repeat create -> same id with `status:"duplicate"`, list still one item | PASS (same id, `status:duplicate`, list count 1) |
| unauthenticated POST -> 401 | PASS (re-confirmed `401`) |

All seven checks PASS.

## No reviewer email leaked

A scan of every captured response body for an email pattern found none. The
stored identity is the opaque agent reviewer id `agent_orcast_automation` with
`annotator_role: reviewer`; no email field appears in the create, list, get, or
idempotency responses. The agent key value also appears in no capture.

## Evidence

- `dispatch/STU/gate_captures/roundtrip_metrics.json` (verdict summary)
- `dispatch/STU/gate_captures/step1_create.status` (`200`), `step1_create.json`
- `dispatch/STU/gate_captures/step2_list.status` (`200`), `step2_list.json`
- `dispatch/STU/gate_captures/step3_get.status` (`200`), `step3_get.json`
- `dispatch/STU/gate_captures/step4_create_repeat.status` (`200`),
  `step4_create_repeat.json` (`status:duplicate`, same id)
- `dispatch/STU/gate_captures/step4b_list_after.status` (`200`),
  `step4b_list_after.json` (one item)
- `dispatch/STU/gate_captures/negative_unauth_post.status` (`401`),
  `negative_unauth_post.json`
- `dispatch/STU/gate_captures/request_body.json`

# ORCAST AWS Handoff — Coordination Status

**Last updated:** 20260614T040142Z

## Live URLs

```
BACKEND_URL=https://pjrftm3bkv.us-west-2.awsapprunner.com
CLOUDFRONT_URL=https://d2gslju5drx74c.cloudfront.net
FRONTEND_BUCKET=198456344617-us-west-2-orcast-aws-backend-frontend
DISTRIBUTION_ID=E3BMZQLRHZ0Y83
AWS_REGION=us-west-2
```

Run `bash scripts/inject-backend-url.sh` before any production build.

## Stream status

| Stream | Status |
|--------|--------|
| A — AWS infra | complete — App Runner, Lambda schedulers, CORS, smoke test passed |
| B — CI pipelines | complete — Firebase Node 20, aws-deploy.yml, angular-test.yml, cloudflare-deploy.yml |
| C — Stash reconcile | complete — RxJS fixes, map bounds, OBIS data, no GPU URLs |
| D — Frontend AWS | complete — multi-host envs, live-ai-demo, CSV download |
| E — Cypress | complete — env vars, legacy isolation, aws-backend-smoke + probability-report |
| F — Cloudflare | complete — wrangler.toml, worker proxy, docs |
| Wave 1.5 gate | complete — URL injected, pytest + ng test + local smoke passed |
| Wave 2 deploy | AWS CloudFront complete; Firebase/Cloudflare builds verified (deploy via CI secrets) |

## Verification

- pytest tests/aws_backend: 7 passed
- npm run test:ci: 35 passed
- test_aws_backend_smoke.py (local + deployed): passed
- No orcast-gemma3-gpu in orcast-angular/src/







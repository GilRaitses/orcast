# orcast — coordination status

**Project title:** Physical world model fusion for orca encounter forecasting and community platform for field researchers

**Waves registry:** [docs/devpost/WAVES_REGISTRY.md](docs/devpost/WAVES_REGISTRY.md)

**Last updated:** 20260624T000000Z

## Wave Set A (agent demo automation)

| Item | Evidence |
|------|----------|
| H0 deploy | `dpl_E6g6wkkTSntzEUcZvWwgkotjqa1m` — maps key + same-origin agent auth |
| Gate | `./tools/waves/run-gate.sh a-gate` PASS |
| Video | [figures/_demo-run/demo-walkthrough.webm](docs/devpost/figures/_demo-run/demo-walkthrough.webm) (~134s) |
| Charter | [docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md](docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md) |
| Beat PNGs | [docs/devpost/figures/_demo-run/](docs/devpost/figures/_demo-run/) |

**Next wave:** H1 manual Devpost submit.

## Live URLs

```
WEB=https://orcast-h0.vercel.app
BACKEND_URL=https://pjrftm3bkv.us-west-2.awsapprunner.com
PARTNER_GATEWAY=https://orcast-h0.vercel.app/api/v1
CLOUDFRONT_URL=https://d2gslju5drx74c.cloudfront.net
FRONTEND_BUCKET=198456344617-us-west-2-orcast-aws-backend-frontend
DISTRIBUTION_ID=E3BMZQLRHZ0Y83
AWS_REGION=us-west-2
CLOUDFRONT_BUNDLE=main.6f6b24cbe9659840.js
EXPLORE_URL=https://orcast-h0.vercel.app/explore
EXPLORATION_DATABASE_CFN=EnableExplorationDatabase=true
EXPLORATION_RDS=orcast-aws-backend-explore.cjymkcu2uzi1.us-west-2.rds.amazonaws.com
EXPLORATION_ENV=ORCAST_DATABASE_URL on App Runner from Secrets Manager
```

Run `bash scripts/inject-backend-url.sh` before any production Angular build (updates Live URLs only; other sections are preserved).

## Demo surfaces

| Surface | URL | Role |
|---------|-----|------|
| H0 hackathon web | `orcast-h0.vercel.app` | Gates, moderation, provenance, explore guide, partner `/api/v1` |
| Angular pilot maps | `d2gslju5drx74c.cloudfront.net` | Reports, historical/realtime maps, trip planner |
| orcast.org | Firebase (may lag CloudFront) | Do not use as primary Devpost link |

## Remediation campaign (2026-06-23)

| Channel | Status |
|---------|--------|
| Alpha governance | done — trusted-proxy reviewer auth, DDB conditional moderation |
| Beta partner API | done — `/api/v1`, hashed keys, rate limits |
| Gamma snapshot | done — `frozen_data` pin, ASL wire |
| Delta docs | done — truth table honest labels |
| Foxtrot infra | done — partner key seeded, Vercel env |
| Echo verify | done — partner gates 200, agent_smoke dry-run green |

## Verification

- CloudFront `/` — lowercase **orcast**, pilot copy, no zero-trust / multi-agent taglines
- CloudFront `/reports` — live API report (85 hotspots, maps render)
- CloudFront `/automated-demo` — client redirect to `/` (legacy route quarantined)
- Backend health + CORS from CloudFront origin: 200
- pytest remediation suite: 36 passed

Production partner smoke:
```bash
curl -s -H "X-ORCAST-Partner-Key: $ORCAST_PARTNER_DEV_KEY" \
  https://orcast-h0.vercel.app/api/v1/api/gates | jq .status
```

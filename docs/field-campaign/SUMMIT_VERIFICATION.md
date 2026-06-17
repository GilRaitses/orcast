# Summit verification — 2026-06-16

## Backend (live)

- URL: `https://pjrftm3bkv.us-west-2.awsapprunner.com`
- Smoke test: **passed** (health, sightings, hotspots, hydrophones, environmental, forecast, reports, CSV)
- CORS: updated to include `https://d2gslju5drx74c.cloudfront.net`

## CloudFront (primary booth URL)

- URL: `https://d2gslju5drx74c.cloudfront.net/`
- Deploy: **complete** (S3 sync + invalidation)
- Landing page: new honest `/` (not live-ai demo)
- Bundle API URL: `pjrftm3bkv.us-west-2.awsapprunner.com` verified in `704.*.js`
- Demo routes: `/reports`, `/partners`, `/historical`, `/ml-predictions`, `/live-demo`

## orcast.org (Firebase custom domain)

- Status before deploy: **stale July 2025 shell** (804 bytes)
- Firebase build: **ready** (`npm run build -- --configuration=firebase`)
- Local `firebase deploy`: **blocked** — needs `firebase login` or CI secret
- After merge to `main`: GitHub Action `firebase-hosting-merge.yml` deploys with backend URL inject

Manual deploy:

```bash
firebase login
bash tools/deployment/firebase/deploy.sh
```

## Cloudflare worker

- `wrangler.toml` API_BASE_URL: **updated** to live App Runner
- `environment.cloudflare.ts`: same-origin `apiBaseUrl: ''` for `/api/*` proxy
- Local `wrangler deploy`: needs `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`
- Worker still returns plain text for `/` until Pages hosts static assets (Firebase serves homepage today)

## Offline demo

- `bash scripts/demo-start.sh` → cache on `:8080` **passed**
- `demo-start.sh` now only injects localhost into `environment.ts` (production envs preserved)

## QR codes

Generated in `docs/field-campaign/qr/`:

- `cloudfront-landing.png`
- `cloudfront-reports.png`
- `orcast-org-landing.png` (valid after Firebase deploy)
- `orcast-org-partners.png`

Regenerate: `bash scripts/generate-summit-qr.sh` (requires `.venv` with `qrcode[pil]`)

## Booth recommendation

1. Primary QR: CloudFront landing
2. Demo flow: `/` → `/reports` → CSV download
3. Laptop backup: `demo-start.sh` + `npm start`
4. Honest line: agent chat is prototype; fusion pipeline is live on AWS

# Deploy the ORCAST web app to Vercel

The app lives in [web/](../../web) (Next.js App Router). It is production-ready and builds clean. Pick one path.

## Environment variables (set all three in the Vercel project)

| Var | Scope | Value |
|---|---|---|
| `ORCAST_API_BASE` | Server | `https://pjrftm3bkv.us-west-2.awsapprunner.com` |
| `ORCAST_API_KEY` | Server (secret) | the production API key (do not expose to the browser) |
| `NEXT_PUBLIC_MAPS_KEY` | Public | `GOOGLE_API_KEY_REDACTED` |

Retrieve the production API key:

```bash
SVC=$(aws apprunner list-services --region us-west-2 \
  --query "ServiceSummaryList[?ServiceName=='orcast-aws-backend'].ServiceArn" --output text)
aws apprunner describe-service --region us-west-2 --service-arn "$SVC" \
  --query "Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.ORCAST_API_KEY" \
  --output text
```

## Option A: Vercel dashboard (no CLI)

1. Push this repo to GitHub (or use the existing remote).
2. Vercel dashboard -> Add New -> Project -> import the repo.
3. Set **Root Directory = `web`** (important; the app is in a subdirectory). Framework auto-detects as Next.js.
4. Add the three environment variables above.
5. Deploy. Copy the production URL.

## Option B: Vercel CLI

```bash
cd web
npx vercel login
npx vercel link            # create/link the project
npx vercel env add ORCAST_API_BASE production
npx vercel env add ORCAST_API_KEY production
npx vercel env add NEXT_PUBLIC_MAPS_KEY production
npx vercel --prod          # deploy
```

## Agent-assisted deploy

If you set a `VERCEL_TOKEN` (Vercel -> Account Settings -> Tokens) in the shell, the deploy can be run non-interactively:

```bash
cd web
npx vercel pull --yes --environment=production --token "$VERCEL_TOKEN"
npx vercel deploy --prod --token "$VERCEL_TOKEN"
```

## After deploy

1. Add the production domain (e.g. `your-project.vercel.app`) to the Google Maps key's HTTP-referrer allowlist (Google Cloud Console -> APIs & Services -> Credentials) so the map renders.
2. Grab the **Vercel Team ID** for the submission: dashboard -> Settings -> General -> Team ID, or `npx vercel teams ls`.
3. Smoke-test: open `/gates` (should show the live fit), `/moderation` (the DynamoDB queue), and the home map.

Because the browser only talks to the same-origin `/api/be` proxy (which injects the key server-side), no backend CORS change is needed for the Vercel origin.

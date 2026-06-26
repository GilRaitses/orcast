# orcast web (Vercel surface)

Next.js (App Router) front end for orcast kernel forecasting. Surfaces:
forecast map with provenance, **sighting check** (`/ask`), fitness gates, glossary,
review dossier, and community moderation.

## Architecture

The browser never talks to the backend directly. All calls go through the
same-origin proxy at `app/api/be/[...path]/route.ts`, which injects the
`X-ORCAST-Key` header server-side. Because the proxy runs server-to-server,
no backend CORS entry for the Vercel origin is required.

## Local dev

```bash
cp .env.example .env.local   # set ORCAST_API_BASE, ORCAST_API_KEY, NEXT_PUBLIC_MAPS_KEY
npm install
npm run dev
```

Run the FastAPI backend locally (see repo root) for `/ask` to return live gate data.

### Sighting-check narration (Amazon Bedrock)

Production uses **Amazon Bedrock** (default: Claude 3 Haiku) via the App Runner IAM role — no laptop, no public LLM endpoint, pay-per-request.

On deploy, `ORCAST_ENABLE_BEDROCK=true` is the default in `tools/deployment/aws/deploy.sh`. The stack sets:

- `ORCAST_ENABLE_BEDROCK=true`
- `ORCAST_BEDROCK_SIGHTING_MODEL=anthropic.claude-3-haiku-20240307-v1:0`

Promotion supervisor can use a separate model via `ORCAST_BEDROCK_MODEL_ID` (default Sonnet). If Bedrock fails or is disabled, sighting check falls back to the deterministic template (still grounded in live gates).

Local dev without AWS credentials: leave `ORCAST_ENABLE_BEDROCK=false` (template fallback). Optional dev-only Ollama: `ORCAST_LLM_ENABLED=true` + Ollama on localhost.

## Environment

See `.env.example` for the full list. Required for production:

- `ORCAST_API_BASE` (server): App Runner backend base URL. **Missing → proxy returns 500.**
- `ORCAST_API_KEY` (server): shared key for keyed endpoints (moderation, promotion, orchestrator run).
- `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_COOKIE_PASSWORD` (server): AuthKit session for protected routes.
- `NEXT_PUBLIC_WORKOS_REDIRECT_URI` (public): OAuth callback URL.
- `NEXT_PUBLIC_MAPS_KEY` (public): Google Maps JS API key, restricted by HTTP referrer.

Optional / feature-gated: `ORCAST_DEFAULT_AGENT_ID` (default `explore-guide-v1`), `AI_GATEWAY_API_KEY` + `ORCAST_EXPLORE_GATEWAY_MODEL(S)` (gateway path; falls back to App Runner Bedrock), `ORCAST_PARTNER_DEV_KEY`, `ORCAST_AGENT_KEY` + reviewer id/email (automation/CI).

Backend (App Runner): `ORCAST_ENABLE_BEDROCK`, `ORCAST_BEDROCK_SIGHTING_MODEL`, `ORCAST_BEDROCK_MODEL_ID`.

## Deploy

This app deploys with the Vercel project **Root Directory set to `web`** (dashboard setting; see [../docs/devpost/DEPLOY_VERCEL.md](../docs/devpost/DEPLOY_VERCEL.md)). With that set, Vercel runs install/build inside `web/` and auto-detects Next.js. The tracked [vercel.json](vercel.json) only declares `framework: nextjs` and does not pin install/build/output commands. Set the environment variables above in the Vercel project settings.

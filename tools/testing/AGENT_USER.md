# ORCAST automation agent

Lets Cursor / CI hit **protected** Vercel proxy routes (journal, moderation, dossier, decisions) without a WorkOS browser session.

## How it works

1. `ORCAST_AGENT_KEY` is set on Vercel (server-only).
2. Requests to `/api/be/...` with header `X-ORCAST-Agent-Key` matching that secret are treated as reviewer `agent@orcast.dev` (`agent_orcast_automation`).
3. The same header on `/api/interactions/plan` authenticates the surface planner proxy (Playwright demo path).
4. The key is **never** used in frontend code — only local scripts, Playwright, and CI.

Direct App Runner calls can also pass `X-ORCAST-Reviewer-Id` headers, but that bypasses the Vercel proxy path; the agent key tests the full stack.

## Setup (once)

```bash
export VERCEL_TOKEN=...
bash tools/testing/setup_agent_user.sh
cd web && npx vercel deploy --prod --token "$VERCEL_TOKEN"
```

Writes gitignored `.agent-credentials.env` at repo root.

Optional: the script also creates a WorkOS user `agent@orcast.dev` (email verified) so you can sign in manually in a browser with the password in the creds file.

## Run smoke test

```bash
python3 tools/testing/agent_smoke.py
```

Covers: journal list/create/publish, moderation queue, dossier, decision records, sighting assist, surface planner (`/api/interactions/plan`).

## Playwright demo recording (no manual WorkOS sign-in)

Full storyboard automation: [docs/devpost/DEMO_NO_CRED_STORYBOARD.md](../docs/devpost/DEMO_NO_CRED_STORYBOARD.md)

```bash
source .agent-credentials.env
cd web && npm install && npx playwright install chromium
PW_SLOW_MO=500 npm run demo:walkthrough
npm run demo:screenshots
./tools/waves/gates/h1-demo-walkthrough.sh
```

Playwright injects `X-ORCAST-Agent-Key` on **same-origin** requests only (via route hook — never on Google Maps CDN). Nav shows `agent@orcast.dev · Automation` during headed demo.

```bash
./tools/waves/run-gate.sh a-gate
```

Produces `docs/devpost/figures/_demo-run/demo-walkthrough.webm` when A5 passes.

## Manual curl example

```bash
source .agent-credentials.env
curl -s -H "X-ORCAST-Agent-Key: $ORCAST_AGENT_KEY" \
  "$ORCAST_WEB_BASE/api/be/api/journal/entries" | jq .
```

# Demo storyboard — agent automation (no manual WorkOS sign-in)

**Project:** Physical world model fusion for orca encounter forecasting and community platform for field researchers

Record the **same narrative** as [DEMO_STORYBOARD.md](DEMO_STORYBOARD.md) on https://orcast-h0.vercel.app without clicking WorkOS sign-in. Playwright (or curl scripts) inject `X-ORCAST-Agent-Key` so protected routes behave like a signed-in reviewer.

Manual alternative: sign in with WorkOS before recording ([DEMO_STORYBOARD.md](DEMO_STORYBOARD.md) setup).

## Prerequisite

```bash
bash tools/testing/setup_agent_user.sh   # writes .agent-credentials.env
bash tools/testing/setup_demo_maps.sh    # NEXT_PUBLIC_MAPS_KEY + GCP referrer checklist
cd web && npx vercel deploy --prod
```

See [tools/testing/AGENT_USER.md](../../tools/testing/AGENT_USER.md).

## Automation recording

```bash
source .agent-credentials.env
cd web && npm install && npx playwright install chromium
PW_SLOW_MO=500 npm run demo:walkthrough    # headed — narrate live
npm run demo:screenshots                   # beat PNGs → figures/_demo-run/
npm run demo:record                        # reference video
```

Nav may still show **Sign in** for public browsers. With Playwright agent key, nav shows **agent@orcast.dev · Automation** instead.

## Beats (~3 minutes)

Tagged: **[PROBLEM]**, **[WORKING APP]**, **[DATABASE]**.

| Beat | Time | Screen | Auth |
|------|------|--------|------|
| 1 | 0:00–0:20 | `/` — map, confidence, **orcast** hero | public |
| 2 | 0:20–0:45 | `/?lat=48.5465&lng=-123.03&provenance=1` — provenance modal | public (URL deep link) |
| 3 | 0:45–1:10 | `/gates` — integrity conditions + Level 1 PSTH | public |
| 4 | 1:10–1:35 | `/explore?planner=1&lat=48.5465&lng=-123.03` — **Continue exploration** → `ui_intent` panels | agent key on `/api/interactions/plan` |
| 5 | 1:35–1:55 | `/ask` — **Check sighting** | public |
| 6 | 1:55–2:15 | `/journal` save → **Publish to community** → `/moderation` **Approve** | agent key on `/api/be` |
| 7 | 2:15–2:35 | [`figures/dynamodb-proof.png`](figures/dynamodb-proof.png) or live AWS console | operator capture |
| 8 | 2:35–3:00 | [`figures/architecture.png`](figures/architecture.png) | static slide |

### Beat 1 — [PROBLEM] Home

**Say:** "Wildlife forecasts usually show a confident map that hides how thin the evidence is. For endangered orcas watched from shore and kayak, that's misleading. **orcast** always shows the forecast — but only the confidence its gates have earned. You're seeing 0% right now. That's the honest answer: the model fitted, but the gate battery says the fit isn't sharp enough to display high confidence without a human promotion decision. That gate is the product."

### Beat 2 — [WORKING APP] Provenance

**Say:** "Every cell traces back to data. Each kernel shows whether it beat a statistical null. Outside the pilot region it says so honestly — that's the product."

### Beat 3 — [WORKING APP] Gates

**Say:** "These are fitness gates on a negative-binomial fit — plus integrity conditions: single station, unreviewed acoustic candidates, covariates excluded when data doesn't support them. The system declines to oversell. The promoted badge and 0% confidence are not a contradiction — the promotion was authorized, but the effective confidence gate caps the displayed value because deviance skill is negative. The gate is doing exactly what it should."

### Beat 4 — [WORKING APP] Surface planner

**Say:** "Central Casting plans which panels to open before narration — same prepare-then-narrate pattern, keyed surface planner. This step-log reduces the unsupported scientific claim rate to 0% — measured live against the Gemini API. Maps grounding alone leaves 91% of orca science claims uncited."

*Beat 4b (grounding benchmark slide) excluded from recording — benchmark referenced in Devpost description only. Demo target: under 3 minutes.*

### Beat 5 — [WORKING APP] Sighting check

**Say:** "Sighting check separates what the temporal model knows from whether your dorsal fin was an orca. It's grounded in the same gates — not a yes/no oracle."

### Beat 6 — [WORKING APP][DATABASE] Journal → moderation

**Say:** "Field notes stay private in a per-user journal in DynamoDB until you publish. Shore reports hit a moderation queue — signed-in reviewers approve before low-weight attribution."

### Beat 7 — [DATABASE] DynamoDB

**Say:** "DynamoDB is the backbone: nine on-demand tables including managed agent configs. The approval I just made lives here."

### Beat 8 — Close

**Say:** "Vercel frontend, App Runner API, DynamoDB system of record, Central Casting interactions, Step Functions orchestrator, Bedrock for sighting narration. **orcast** — a forecast you can use in the field and defend in public."

## Playwright spec

[`web/e2e/demo-no-cred-walkthrough.spec.ts`](../../web/e2e/demo-no-cred-walkthrough.spec.ts) drives beats 1–6 live and opens static figures for 7–8.

## Security

`ORCAST_AGENT_KEY` is server-only on Vercel. Playwright reads it from gitignored `.agent-credentials.env` locally — never commit or bundle in client code.

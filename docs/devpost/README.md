# H0, Hack the Zero Stack, submission package

orcast is a two-sided loop around Salish Sea killer whales. Encounter forecasting is the grounding layer that a public visitor console and a behavior-analysis research workbench both stand on, and an AI managed-orchestration layer is set up for shared benefit across three parties, the tourists who visit, the researchers who study whale behavior, and the whales themselves. The visitor console transduces stated intent into planning objects on top of the forecast. The research workbench carries collaborative review today and is extending toward dtag modeling replay and a terrain and bathymetry 3D twin. The orchestration bridge follows the pax Friend console direction tracked in the LGC lane, which is chartered and not yet shipped.

Everything needed to submit **orcast** to the H0 hackathon, Open-innovation track, primary AWS database DynamoDB, frontend on Vercel. Deadline **June 29, 2026 5:00 PM**.

## Core artifacts

| Doc | Purpose |
|-----|---------|
| [SUBMISSION.md](SUBMISSION.md) | Full write-up + demo script |
| [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md) | Copy/paste into Devpost fields |
| [DEMO_STORYBOARD.md](DEMO_STORYBOARD.md) | ~3 min video beats |
| [WHITEPAPER_HYPOTHESIS.md](WHITEPAPER_HYPOTHESIS.md) | **Gap + hypothesis** the platform bridges |
| [DYNAMODB_PROOF.md](DYNAMODB_PROOF.md) | Seven-table proof + console screenshot guide |
| [HACKATHON_SUBMIT_CHECKLIST.md](HACKATHON_SUBMIT_CHECKLIST.md) | Pre-publish smoke + your action items |
| [API_AGENTS.md](API_AGENTS.md) | Partner OpenAPI + Claude/OpenAI tool schemas |
| [figures/architecture.png](figures/architecture.png) | Architecture diagram (upload) |
| [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) | Vercel deploy reference |

## Live demo

- **URL:** https://orcast-h0.vercel.app
- **Vercel Team ID:** `team_dQQph8zC78tTPHDnGnvawdKo`
- **Routes to show:** `/`, `/gates`, `/ask`, `/journal`, `/moderation` (signed in)

## Status (June 2026)

**Wave Set A complete (A0–A5).** Next: **H1** manual Devpost submit — [submission/H1_MANUAL_SUBMIT.md](submission/H1_MANUAL_SUBMIT.md).

Charter: [submission/A0_AGENT_DEMO_CHARTER.md](submission/A0_AGENT_DEMO_CHARTER.md). Gate: `./tools/waves/run-gate.sh a-gate`.

**Done**

- Backend on App Runner; **nine DynamoDB tables** (incl. partner-api-keys + managed-agents); Bedrock sighting check; field journal; WorkOS auth
- Central Casting + surface planner (`/explore?planner=1`, `POST /api/interactions/plan`)
- Submission pack synced: architecture.png, ERD pages 1–5, copy, `s-gate` PASS
- Wave Set A: Playwright no-cred demo path, `AuthStatus` automation chip, `a-gate` PASS
- Whitepaper hypothesis drafted

**Remaining (your actions)** — see [HACKATHON_SUBMIT_CHECKLIST.md](HACKATHON_SUBMIT_CHECKLIST.md) and [submission/H1_MANUAL_SUBMIT.md](submission/H1_MANUAL_SUBMIT.md)

1. Record ~3 min video ([DEMO_STORYBOARD.md](DEMO_STORYBOARD.md))
2. Capture DynamoDB console screenshot → `figures/dynamodb-console.png` (nine tables)
3. Publish Devpost from [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md); attach diagram, screenshot, video
4. (Optional) Attach [WHITEPAPER_HYPOTHESIS.md](WHITEPAPER_HYPOTHESIS.md) as supplementary PDF for judges

## Submission field cheat-sheet

- **Project name:** orcast
- **Track:** Open innovation
- **AWS Database:** DynamoDB (9 tables, us-west-2)
- **Live URL:** https://orcast-h0.vercel.app
- **Vercel Team ID:** team_dQQph8zC78tTPHDnGnvawdKo
- **Architecture:** figures/architecture.png
- **DB proof:** console screenshot or figures/dynamodb-proof.png
- **Video:** ~3 min (script in DEMO_STORYBOARD.md)

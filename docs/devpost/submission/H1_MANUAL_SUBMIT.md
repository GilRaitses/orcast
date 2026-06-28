# H1 — Manual Devpost submit (operator)

**Project title:** Physical world model fusion for orca encounter forecasting and community platform for field researchers

Wave set: **H** (Hackathon)  
Predecessor: Wave Set **A** complete (A4 `a-gate` PASS); Wave Set **S** (S4 `s-gate` PASS)  
Deadline: **June 29, 2026 5:00 PM**

## Narrative spine for the Devpost copy

Lead the description with the two-sided loop. orcast is a loop around Salish Sea killer whales where encounter forecasting is the grounding layer, not the end product. The A side is the visitor console that transduces stated intent into planning objects on top of the forecast. The B side is a behavior-analysis research workbench that carries collaborative review today and is extending toward dtag modeling replay and a terrain and bathymetry 3D twin. The bridge is an AI managed-orchestration layer set up for shared benefit across three parties, the tourists, the researchers, and the whales themselves. Frame the LGC liquid-glass console as the orchestration direction, because it is chartered and not yet shipped. Keep the honesty locks intact. The forecast is a modeled probability not an observed sighting, detection is a confidence score not ground truth, probability zones are predictions not guarantees, and the 3D twin is modeled not measured.

## Gates before you publish

```bash
./tools/waves/run-gate.sh H0
./tools/waves/run-gate.sh s-gate
./tools/waves/run-gate.sh a-gate          # maps + walkthrough + demo-walkthrough.webm
./tools/waves/run-gate.sh ic6-gate   # optional casting regression; needs ORCAST_API_KEY
```

Required artifact from `a-gate`: [figures/_demo-run/demo-walkthrough.webm](../figures/_demo-run/demo-walkthrough.webm) (~3 min, all map beats clean).

All automated submission docs are synced. Attach these artifacts to Devpost:

| Artifact | Path |
|----------|------|
| Architecture diagram | [figures/architecture.png](../figures/architecture.png) |
| Submission copy | [DEVPOST_DRAFT.md](../DEVPOST_DRAFT.md) |
| Demo script | [DEMO_STORYBOARD.md](../DEMO_STORYBOARD.md) |
| DynamoDB proof doc | [DYNAMODB_PROOF.md](../DYNAMODB_PROOF.md) |
| Grounding benchmark scope diagram | [docs/figures/fig-mp3-benchmark-scope/figure.png](../../figures/fig-mp3-benchmark-scope/figure.png) |
| Whitepaper PDF (paper 1) | [docs/whitepaper/Build/Raitses_orcast_2026.pdf](../../whitepaper/Build/Raitses_orcast_2026.pdf) |

## Your three manual steps

### 1. Record ~3 min demo video

**Option A — automation (no WorkOS click):** [DEMO_NO_CRED_STORYBOARD.md](../DEMO_NO_CRED_STORYBOARD.md)

Per-beat recording (Wave Set V — preferred):
```bash
source .agent-credentials.env
cd web && npm install && npx playwright install chromium
npm run demo:beat-all           # records each beat separately (headed)
./tools/waves/run-gate.sh v-beat    # verify all beat webms
./tools/waves/run-gate.sh v-stitch  # → demo-final.webm (~3 min)
```

Single-take recording (original):
```bash
PW_SLOW_MO=800 npm run demo:walkthrough
npm run demo:record
```

Final video: `docs/devpost/figures/_demo-run/demo-final.webm` (per-beat) or `demo-walkthrough.webm` (single-take).

**Option B — manual:** [DEMO_STORYBOARD.md](../DEMO_STORYBOARD.md) (sign in with WorkOS first).

Recommended beats (both paths):

- Home map + provenance
- `/gates` integrity conditions
- `/explore?planner=1` — surface planner
- Journal → moderation approve
- DynamoDB proof slide or console — **nine** tables
- Close on [architecture.png](../figures/architecture.png)

Live URL: https://orcast-h0.vercel.app

### 2. Capture DynamoDB console screenshot

AWS Console → DynamoDB → Tables (us-west-2) showing all nine tables including `managed-agents` and `partner-api-keys`.

Save as `docs/devpost/figures/dynamodb-console.png` (or use fallback `figures/dynamodb-proof.png`).

```bash
python3 tools/testing/capture_dynamodb_table_list.py   # if available
```

### 3. Publish Devpost

Copy fields from [DEVPOST_DRAFT.md](../DEVPOST_DRAFT.md):

- **Project name:** orcast
- **Track:** Open innovation
- **AWS Database:** DynamoDB (9 tables, us-west-2)
- **Live URL:** https://orcast-h0.vercel.app
- **Vercel Team ID:** team_dQQph8zC78tTPHDnGnvawdKo
- Attach: architecture.png, dynamodb screenshot, video link

Full checklist: [HACKATHON_SUBMIT_CHECKLIST.md](../HACKATHON_SUBMIT_CHECKLIST.md)

## After publish

- Mark H1 complete in operator notes
- Optional next wave set: **IC8** ([casting/IC8_NEXT_OBJECTIVES.md](../casting/IC8_NEXT_OBJECTIVES.md)) or **P1** adversarial probes

# Demo video storyboard (~3 minutes)

**Project:** Physical world model fusion for orca encounter forecasting and community platform for field researchers

**Narrative spine.** orcast is a two-sided loop. Encounter forecasting is the grounding layer, and the demo walks the A side, the visitor console that turns intent into planning objects, plus the stewardship seam. The B side research workbench and the AI orchestration bridge are named as the direction the build is heading, not as shipped surfaces. The same recorded beats below carry that spine. No new beats are added.

Record one take of https://orcast-h0.vercel.app plus one AWS Console tab. Tagged: **[PROBLEM]**, **[WORKING APP]**, **[DATABASE]**.

**Recording paths:**

- **Manual:** sign in with WorkOS before recording (setup below).
- **Automation (no sign-in friction):** [DEMO_NO_CRED_STORYBOARD.md](DEMO_NO_CRED_STORYBOARD.md), Playwright injects `X-ORCAST-Agent-Key` for journal, moderation, and surface planner.

## Setup

- Tabs: (1) https://orcast-h0.vercel.app, (2) AWS Console → DynamoDB → Tables (us-west-2), (3) `docs/devpost/figures/architecture.png`.
- Sign in to orcast before recording (WorkOS, Google or email+password) so moderation/journal work on camera.
- Moderation queue should show pending items (seed + any journal publishes).

## Beats

### 1. (0:00–0:20) [PROBLEM] Home

**Screen:** `/`, map, confidence meter, **orcast** hero (lowercase).

**Say:** "Wildlife forecasts usually show a confident map that hides how thin the evidence is. For endangered orcas watched from shore and kayak, that's misleading. **orcast** always shows the forecast, but only the confidence its gates have earned. This forecast is the grounding layer that a visitor console and a research workbench both stand on. 0% is the honest answer right now: the model fitted, the gates said the fit isn't sharp enough yet, and no confidence gets displayed without a human promotion decision."

---

### 2. (0:20–0:45) [WORKING APP] Provenance

**Screen:** Click a water cell in the pilot region (~48.55, −123.15). Provenance modal: kernels, gate verdicts, nearby sample.

**Say:** "Every cell traces back to data. Each kernel shows whether it beat a statistical null. Outside the pilot region it says so honestly, that's the product."

---

### 3. (0:45–1:10) [WORKING APP] Gates + integrity conditions

**Screen:** `/gates`, confidence meter, integrity conditions list, Level 1 PSTH section. Optional: hover a glossary term.

**Say:** "These are fitness gates on a negative-binomial fit, plus integrity conditions: single station, unreviewed acoustic candidates, covariates excluded when data doesn't support them. The system declines to oversell. The promoted badge alongside 0% confidence is not a contradiction, promotion was authorized, but the effective confidence gate caps it at 0% because deviance skill is negative. That gate is working correctly."

---

### 4. (1:10–1:30) [WORKING APP] Explore planner (optional)

**Screen:** Sign in → `/explore?planner=1`, ask "show gates and decisions for this region." Show planner banner + `ui_intent` panels (map, gates summary).

**Say:** "Central Casting plans which panels to open before narration, same prepare-then-narrate pattern, keyed surface planner. The step-log from this interaction reduces the unsupported scientific claim rate to 0% when used as grounding context, measured live against the Gemini API. Maps grounding alone leaves 91% of orca science claims uncited."

*Beat 4b excluded from recording. Benchmark in Devpost text only.*

---

### 5. (1:45–2:05) [WORKING APP] Sighting check (optional)

**Screen:** `/ask`, pin on map, example question, click **Check sighting**. Show **Bedrock · haiku** badge and reply.

**Say:** "Sighting check separates what the temporal model knows from whether your dorsal fin was an orca. It's grounded in the same gates, not a yes/no oracle."

---

### 6. (1:50–2:15) [WORKING APP][DATABASE] Journal → moderation

**Screen:** `/journal`, create entry with a place name → **Save** → **Publish to community**. `/moderation` → **Approve** one card.

**Say:** "Field notes stay private in a per-user journal in DynamoDB until you publish. Shore reports hit a moderation queue, signed-in reviewers approve before low-weight attribution."

---

### 7. (2:15–2:40) [DATABASE] DynamoDB console

**Screen:** AWS Console table list, **nine** `orcast-aws-backend-*` tables. Optionally open `community-submissions`, `managed-agents`, or `user-journal` explore view.

**Say:** "DynamoDB is the backbone: sightings, moderation queue, decision audit log, field journal, hotspots, reports, ingestion runs, partner keys, and managed agent configs. The approval I just made lives here."

---

### 8. (2:40–3:00) Architecture + close

**Screen:** `figures/architecture.png`.

**Say:** "Vercel frontend, App Runner API, DynamoDB system of record, Central Casting interactions, Step Functions orchestrator, Bedrock for sighting narration. The forecast is the grounding layer under a visitor console and a research workbench, and the orchestration direction serves three parties, tourists, researchers, and the whales themselves. **orcast**, a forecast you can use in the field and defend in public."

---

## Tips

- State problem, show working app, name **DynamoDB**, scored requirements.
- Don't expose secrets in the console tab.
- Fallback slides: `docs/devpost/figures/demo-*.png`.
- Whitepaper for judges: `WHITEPAPER_HYPOTHESIS.md`.

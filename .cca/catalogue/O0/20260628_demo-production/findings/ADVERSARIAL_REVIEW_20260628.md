# Adversarial demo review - 20260628

Deep frame-level review of the **currently rendered** demo (the old A-side cut,
`docs/devpost/figures/_demo-run/demo-final-narrated.mp4`, 190s). Method: 5 fps frames
extracted per beat (969 frames total), one read-only reviewer subagent per beat scanning a
contact sheet + sampling full-res frames, cross-checked against the spoken narration in
`tools/testing/tts_narrate.py`, the rubric (R1-R5) and 8 honesty locks in `PROGRAM.md`.
Plus live-service cold-start telemetry.

Note: the rendered beats follow the OLD storyboard (home/provenance/gates/planner/ask/
journal/moderation/dynamodb/architecture). The NEW two-sided-loop script in `NARRATION.md`
has not been recorded yet (that is the DEMO-PROD SET/BLK/CAM/SCR chain). This review judges
what exists so the new capture does not repeat the same defects.

## Verdict: all 9 beats RETAKE

| Beat | Surface | Verdict | Worst issue |
|---|---|---|---|
| beat-01 home | `/` | RETAKE | ~4s loading/white open; red pins look like sightings (lock 2 FAIL); reviewer chrome |
| beat-02 provenance | `/` modal | RETAKE | nearby detections + out-of-region honesty never shown; modal clipped; method jargon |
| beat-03 gates | `/gates` | RETAKE | gate verdict cards never scrolled into view; raw evidence-chain IDs on screen |
| beat-04 planner | `/explore` | RETAKE | **worst CXR leak**: `ui_intent`, reviewer-sign-in banner, raw skill manifest, CAST slugs |
| beat-05 ask | `/ask` | RETAKE | raw Bedrock model ARN leak; section (b) verification never shown; ~6s model wait |
| beat-06 journal | `/journal` | RETAKE | "Demo automation entry" seed copy; submission hex IDs; claims approval not shown |
| beat-06 moderation | `/moderation` | RETAKE | the one-click approve never shown on camera; smoke-test card copy |
| beat-07 dynamodb | slide | RETAKE | **AWS account ID `198456344617` on screen**; "approval I just made" not shown (count=9 PASS) |
| beat-08 architecture | slide | RETAKE | f_0002 render failure (slide 80% obscured); "Central Casting" codename unglossed |

## Cross-cutting BLOCKERS (fix once, applies to most beats)

1. **Loading / white-flash open on every beat.** f_0001-f_0002 (and often through ~f_0004)
   are blank white, gray-obscured, or skeleton on all 9 beats. Capture rolled before the
   page was ready. Fix: pre-warm the route and start each take after the ready signal
   (`waitForHomeReady` / `waitForProvenanceLoaded` / `waitForJournalReady` etc.), or trim
   the head in post. beat-08 f_0002 is a true mid-render failure (re-capture, do not trim).

2. **Reviewer/automation chrome on public beats (CXR lock 8).** `agent@orcast.dev` and the
   `Automation` nav item are visible on beats 01-07. The capture ran under the automation
   session. Fix: record the public beats under a neutral/anonymous session, or hide auth
   chrome + the `Automation`/`Dossier`/`Decisions`/`Moderation` nav in the `DEMO_RECORD`
   profile.

3. **Internal jargon on screen (CXR lock 8).** See blocklist below. beat-04 and beat-07 are
   the most severe (raw `ui_intent`, skill manifest, schema/agent slugs; AWS account ID).

4. **Say-vs-Show drift (R1).** Most beats narrate a capability the footage does not show:
   modeled-probability label (01), nearby detections + out-of-region (02), gate verdict
   cards (03), the narrate half + "Central Casting" (04), section (b) verification (05),
   reviewer approval (06-journal), the click (06-moderation), the specific approval record
   (07). Either re-capture to show it, or cut the claim.

5. **Pacing.** Nearly every beat holds ~15-18s static after the action. beat-05 adds ~6s of
   dead model-wait. The cut is padded; tighten each beat to its action.

## Internal-jargon blocklist (redact from on-screen copy and/or narration)

### A. On-screen strings that must not appear on a public capture
- `agent@orcast.dev` (automation/dev account) - beats 01-07
- `Automation` nav item - beats 01-07
- beat-01: `Spike-train fit uses unreviewed acoustic candidates; Level 0 QC reports reviewed outcome mix separately.`; `human-promoted` (green badge)
- beat-02: `s_space`; `held-out PIT`; `fold-majority CV pass`; `log-rate` (column header); `Spike-train fit`
- beat-03: `Fit repr_46c561feb18ef281 -> gates run_fb8f0acab5bd91ee -> decision decision_b35d8103d4f4 -> promoted` (raw pipeline IDs); `Open review dossier`; `calibration is assessed via held-out PIT`; `McFadden pseudo-R^2 vs climatology: 0.045`; `Level 1: PSTH vs phase-shuffle null`
- beat-04: `Surface planner mode - requires reviewer sign-in. Renders active panels from ui_intent.`; `CAST: SURFACE-PLANNER-V1 (KEYED)`; `SURFACE-PLANNER-V1 . SCHEMA 1.0.0`; skill manifest `fetch_gates, fetch_supervisor_recommendation, fetch_pending_approval, fetch_provenance`; trace steps `resolve_agent / plan_output / skill_invocation`; `Which gates block promotion right now?`; `CAST: EXPLORE-GUIDE-V1`; footer `Narration: Vercel AI Gateway (anthropic/claude-haiku-4.5)`
- beat-05: `Narration: bedrock . global.anthropic.claude-haiku-4-5-20251001-v1:0` (raw model ARN); `Level 0 QC`; raw stats `mean deviance skill = -0.018`, `p = 0.002`
- beat-06-journal: `Demo automation entry for moderation queue.` (seed text on 3 of 4 cards); `Published - moderation queue (f8c4e54a...)` (raw `community_submission_id` hex); behavior `unknown`; `Logging for review by reviewer.`
- beat-06-moderation: `Automated agent smoke test entry.` (seed copy on every card)
- beat-07: `orcast . us-west-2 . account 198456344617` (**AWS account ID - BLOCKER**); `accessed via the AwsStorage backend`; `Private field journal (WorkOS-scoped)`; `Central Casting configs`; header overlap `ITEMS (APPROX)TATUS`
- beat-08: `Central Casting` (codename, no public gloss)

### B. Spoken-narration terms to soften or cut (per reviewer C-sections)
- "gates" -> "the quality checks the evidence passed" (keep if UI matches)
- "kernels" -> "the timing patterns behind each cell (diel, lunar, season)"
- "gate verdicts" -> "whether each part passed the quality checks"
- "negative-binomial fit" -> "the count-based wildlife model"
- "phase-shuffled null tests" -> "checked against a randomized baseline so noise can't fool it"
- "held-out skill" -> "accuracy on data the model never trained on"
- "calibration" -> "whether predicted probabilities match what actually happened"
- "Central Casting" -> cut, or "the interactions service" / on slide: "Interactions service (Central Casting)"
- "prepare-then-narrate pattern" -> "it plans the layout first, then answers in plain language"
- "keyed surface planner" -> cut -> "a built-in planner picks the right panels"
- "allow-listed, tier-verified skills" -> cut -> "only approved data sources run behind the answer"
- "Every claim is bound to its producing skill and artifact" -> cut unless citations are shown -> "each part links back to the data that produced it"
- "temporal model" -> "the forecast model" / "when orcas are likely nearby"
- "grounded in the same gates" -> "checked against the same evidence rules as the forecast"
- "low-weight attribution" -> cut -> "approved reports count at lower confidence than instrumented sightings"
- "the decision record is immutable" -> cut from moderation beat (wrong surface)
- "alongside every gate verdict" -> cut from moderation beat (not shown there)
- "system of record" -> "DynamoDB holds the live data - nine tables"
- "backbone" -> "DynamoDB holds the data behind everything you just saw"
- "on-demand tables" -> "nine pay-per-request tables"
- KEEP (public-clear): "confidence", "modeled probability", "Bedrock", "Step Functions",
  "App Runner", "Vercel", "DynamoDB", "yes-or-no oracle", "moderation queue".

## Service telemetry (live cold-start, captured 20260628)

Backend App Runner (`pjrftm3bkv.us-west-2.awsapprunner.com`) was **warm**: `/` 409ms,
`/health` 744ms, warm re-hit ~360-390ms. Not a current bottleneck. Client JS loads fast
from the Vercel CDN (<30ms/chunk, FCP ~340-464ms). The cold cost is the Vercel server
function on `/` plus data fetches.

| Beat | Surface | Cold TTFB | Warm TTFB | Dominant bottleneck |
|---|---|---|---|---|
| 01 home | `/` | **1.96s** | 0.34s | Vercel fn cold start ~1.6s; then `events` 0.8-1.5s + `live-hydrophones` 0.5-1.0s data fetch; RSC prefetch storm (signup/login/latest/decisions/ask/about/journal/account/gates all fired on load); map held on "Initializing..." |
| 02 provenance | `/` modal | (same `/` page) | - | provenance fetch ("Tracing provenance..." ~2.4s in capture) |
| 03 gates | `/gates` | 0.32s | 0.28s | server fine; ~1s client skeleton |
| 04 planner | `/explore` | 0.42s | 0.39s | App Runner explore prepare+turn round-trip ("Thinking...") |
| 05 ask | `/ask` | 0.28s | 0.20s | **Bedrock reply ~5.8s model wait** (longest single wait in the whole demo) |
| 06 journal | `/journal` | 0.25s | 0.21s | fast; auth hydration race on open |
| 06 moderation | `/moderation` | 0.23s | 0.25s | fast; full-list reload flash on approve |
| 07 dynamodb | static slide | n/a | n/a | - |
| 08 architecture | static slide | n/a | n/a | - |

Cold-start bottleneck ranking:
1. **`/` Vercel server-function cold start (~1.6s)** - the "loads too slowly" landing complaint.
2. **beat-05 Bedrock reply (~5.8s)** - model latency, not cold start, but the longest on-screen wait.
3. **Home data fetches** (`events`, `live-hydrophones`) 0.8-1.5s + the RSC prefetch storm competing for connections.
4. **beat-04 explore round-trip** through App Runner.

Recommended mitigations (separate from the demo, per the operator's "after the demo" priority):
- Keep `/` warm (App Runner min-instances is already warm; the Vercel fn cold start needs
  ISR/edge or a warming ping); defer/parallelize `events` + `live-hydrophones`; drop or
  gate the home RSC prefetch storm; render the map shell before data resolves so the page
  is not stuck on "Initializing...".

## What passed
- beat-07: on-screen table count = **9**, matches narration and the nine-table fix; item
  counts are real and specific (229/28/3/26/113/302/554/1/4).
- beat-08: slide is legible and sharp from f_0003 on; narration stack list matches the slide
  labels (Vercel/Next.js, App Runner, DynamoDB, Step Functions, Bedrock); honesty locks hold.

## Reviewer agents
beat-01 [68f2c5d8], beat-02 [83f6da67], beat-03 [0c053a88], beat-04 [390dfe9a],
beat-05 [2e18cdad], beat-06-journal [8d444291], beat-06-moderation [70d980bf],
beat-07 [a90619e1], beat-08 [079bd988].

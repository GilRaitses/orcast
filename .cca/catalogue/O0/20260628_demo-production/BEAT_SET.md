# orcast demo beat set (two-sided-loop arc)

The canonical beat set for the new submission video. Grounded in
`docs/devpost/PRODUCT_NARRATIVE_2026.md` (the two-sided loop) and the honesty locks in
`PROGRAM.md`. Each beat carries Say / Show / Evidence / Honesty / Film-state. Two classes:
**live** beats run the full chain (SET dependency, BLK, CAM, SCR); **slide** beats skip
BLK and CAM and go straight to SCR scored as slide content.

Narrative spine: encounter forecasting is the grounding layer. The A side is the visitor
console that turns intent into planning objects on top of the forecast. The B side is the
behavior-analysis research workbench. The bridge is an AI managed-orchestration direction.
The three parties served are the tourists who visit, the researchers who study whale
behavior, and the whales themselves.

Legend: Film-state is `live` or `slide`; readiness is `capturable-now` or
`needs-build:<what>`.

---

## A side, the visitor console (forecast as grounding)

### A1, forecast as the grounding layer (home)
- Say: "Wildlife forecasts show a confident map that hides how thin the evidence is. orcast shows the forecast anyway, but only the confidence its gates have earned, and that grounding layer is what a visitor console and a research workbench both stand on."
- Show: `/` map, confidence meter, lowercase orcast hero, the honest 0% promoted.
- Evidence: the live forecast render showing 0% promoted confidence.
- Honesty: "0% promoted is the honest answer: the model fitted, the gates judged the fit not sharp enough, and no confidence displays without a human promotion decision. Modeled probability, not an observed sighting." (locks 1, 2)
- Film-state: live, capturable-now.

### A2, intent becomes planning objects (console plan turn)
- Say: "Tell the console what you are doing, and it turns that intent into planning objects: the map, gates, decision, and provenance panels you act on, all built on the same forecast."
- Show: the public console; enter "How do I plan a trip to the San Juans?"; the planning panels render.
- Evidence: the rendered public planning panels (CXR-redacted public tier).
- Honesty: planning panels carry the modeled-probability label; no reviewer-only copy on the public path. (locks 2, 8)
- Film-state: live, capturable-now.

### A3, one forecast grounds many trips (trip branches)
- Say: "A visit, being here now, or a kayak outing are different trips on one grounding forecast, so the forecast is the substrate, not a separate feature."
- Show: pick a trip branch; the console routes it.
- Evidence: the trip-branch route rendering on the live console.
- Honesty: each trip reads the same modeled forecast. (lock 2)
- Film-state: live, capturable-now.

### A4, provenance and the gates (nothing asserted without a back-link)
- Say: "Tap any cell and it traces back to kernels, gate verdicts, and a nearby sample. The gates publish their integrity conditions instead of hiding them in a footnote."
- Show: a map-cell provenance modal, then `/gates` integrity conditions and Level 1 PSTH.
- Evidence: kernel contributions, gate verdicts, the integrity-conditions list.
- Honesty: "single station, unreviewed acoustic candidates, covariates excluded when data does not support them." (locks 1, 3)
- Film-state: live, capturable-now.

### A5, sighting check (likelihood vs verification)
- Say: "The sighting check separates how likely an encounter was from whether what you saw was an orca, grounded in the same gates."
- Show: `/ask`, drop a pin, ask, Check sighting, the Bedrock Haiku reply.
- Evidence: the Bedrock badge and the grounded reply.
- Honesty: detections are confidence scores, not ground truth; the check is not a yes/no oracle. (lock 3)
- Film-state: live, capturable-now.

### A6, journal to moderation (stewardship seam)
- Say: "Field notes stay private until you publish. Shore reports enter a quarantined moderation queue, and a signed-in reviewer approves before low-weight attribution."
- Show: `/journal` save then publish; `/moderation` approve one card.
- Evidence: the DynamoDB-backed queue and the approval write.
- Honesty: approved reports carry low reliability weight; sightings are effort-biased. (lock 6)
- Film-state: live, capturable-now (reviewer session needed; SET dependency).

---

## B side, the behavior-analysis research workbench

### B1, ask-the-console orchestrator trace (reviewer)
- Say: "On the research side the console plans which surfaces to open before it narrates, and the reviewer sees that trace."
- Show: the reviewer console; a plan turn; the orchestrator trace.
- Evidence: the live trace on the reviewer tier.
- Honesty: narration is grounded in live context; outputs are estimates, not labels. (lock 2)
- Film-state: live, needs-build:reviewer-session (SET dependency: agent/reviewer key).

### B2, provenance and hydrophone annotation
- Say: "Reviewers annotate hydrophone detections and review community reports, and that work sharpens the forecast that grounds the visitor trips."
- Show: the hydrophone-detection annotation surface and its provenance lineage.
- Evidence: the annotation UI and the lineage record.
- Honesty: a detection is a model confidence score, not reviewed ground truth; lineage caveats hold. (locks 3, 6)
- Film-state: live, capturable-now (reviewer session; SET dependency).

### B3, modeled terrain and bathymetry 3D twin (sandbox)
- Say: "A modeled terrain and bathymetry twin of the San Juan Islands gives the research side a shared frame to close a gap that advances both sides."
- Show: the twin in the research sandbox; a short choreographed pan across labeled places (post W-CAM), land meeting the waterline (post W2.6).
- Evidence: the rendered twin scene.
- Honesty: "modeled, not measured; a research-sandbox surface, not a shipped route." (lock 4)
- Film-state: live, needs-build:twin (SET dependency: twin build state; W2.6 datum + W-PERFUX-BUILD framing landed; W-CAM labels/choreography and the deployed route are direction).

---

## Bridge and close (slides)

### C1, the AI managed-orchestration bridge (direction)
- Say: "An AI orchestration layer is being built to run the routines across both sides, following the pax Friend liquid-glass console direction, for the shared benefit of visitors, researchers, and the whales themselves."
- Show: an LGC concept slide.
- Evidence: the LGC charter (`.cca/catalogue/O0/20260628_liquid-glass-console/`).
- Honesty: "direction, chartered and not yet shipped." (lock 5)
- Film-state: slide.

### C2, close (the loop and the three parties)
- Say: "Vercel frontend, App Runner API, DynamoDB system of record across nine tables, Central Casting interactions, Step Functions orchestration, Bedrock narration. The forecast grounds a visitor console and a research workbench, and the orchestration direction serves three parties: tourists, researchers, and the whales. A forecast you can use in the field and defend in public."
- Show: the architecture slide and the nine-table DynamoDB proof slide.
- Evidence: `docs/devpost/figures/architecture.png` and `figures/dynamodb-proof.png` (nine tables).
- Honesty: all locks; figures keep their real values. (all locks)
- Film-state: slide.

---

## Stage mapping

- Live beats (full chain): A1, A2, A3, A4, A5, A6, B1, B2, B3.
- Slide beats (SCR only, scored as slide content): C1, C2.
- SET prerequisites implied: web dev server (or prod target), agent/reviewer session for
  A6/B1/B2, Google Maps for A1/A4/A5, the twin build state for B3.

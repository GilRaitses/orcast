# Locked narration (two-sided-loop arc)

The narration script the render lane wires into `tools/testing/tts_narrate.py` (XTTS clone)
once SCR signs `APPROVED_TAKES.md`. One line block per beat, keyed to `BEAT_SET.md`. Lines
hold the honesty locks (real 0%, modeled probability, confidence scores, direction). No
em-dashes. Slide beats (c1, c2) are narrated over the slide.

```
NARRATION = {
  "a1": "Wildlife forecasts show a confident map that hides how thin the evidence is. orcast shows the forecast anyway, but only the confidence its gates have earned. That grounding layer is what a visitor console and a research workbench both stand on. Right now the honest answer is zero percent promoted: the model fitted, the gates judged the fit not sharp enough, and nothing displays without a human decision.",
  "a2": "Tell the console what you are doing and it turns that intent into planning objects: the map, the gates, the decision, and the provenance, all built on the same forecast.",
  "a3": "A visit, being here now, or a kayak outing are different trips on one grounding forecast, so the forecast is the substrate, not a separate feature.",
  "a4": "Tap any cell and it traces back to kernels, gate verdicts, and a nearby sample. The gates publish their integrity conditions: a single station, unreviewed acoustic candidates, covariates excluded when the data does not support them.",
  "a5": "The sighting check separates how likely an encounter was from whether what you saw was an orca. A detection is a confidence score, not ground truth.",
  "a6": "Field notes stay private until you publish. Shore reports enter a quarantined queue, and a signed-in reviewer approves before low weight attribution.",
  "b1": "On the research side the console plans which surfaces to open before it narrates, and the reviewer sees that trace.",
  "b2": "Reviewers annotate hydrophone detections and review community reports, and that work sharpens the forecast that grounds the visitor trips.",
  "b3": "A modeled terrain and bathymetry twin of the San Juan Islands gives the research side a shared frame. It is modeled, not measured, and it lives in the research sandbox.",
  "c1": "An orchestration layer is being built to run the routines across both sides, following the pax Friend console direction. It is chartered, not yet shipped.",
  "c2": "Vercel frontend, App Runner API, DynamoDB system of record across nine tables, Central Casting, Step Functions, and Bedrock narration. The forecast grounds a visitor console and a research workbench, and the direction serves three parties: tourists, researchers, and the whales. A forecast you can use in the field and defend in public.",
}
```

Each line maps one to one to the beat's Say in `BEAT_SET.md`. The render lane must not add
a claim the approved take does not show; if a take was cut at SCR, its narration line is
cut with it.

# BLK-A5, sighting check (likelihood vs verification)

Verdict: CLEARED. Advances to CAM.

Prereqs: SET-web READY, SET-maps READY.

## Moving parts

1. `/ask` pin present — CLEARED. The pin renders at "Pin 48.5465, -123.0300. Click
   the map to move it." on the painted Google Map. File:
   `web/app/components/SightingCheckPanel.tsx`.
2. Describe + Check sighting -> Bedrock-badged grounded reply — CLEARED. Typed a fin
   description, clicked Check sighting; the reply rendered with the Bedrock badge
   ("Narration: bedrock · global.anthropic.claude-haiku-4-5-20251001-v1:0") and the
   grounded answer: "(a) Encounter likelihood from the temporal model" (19.4%
   baseline intensity, "treat this 19% as a rough reference, not a forecast") and
   "(b) Was your sighting likely an orca?" (harbor-porpoise/seal/log misID caveats,
   nearby verified sightings). Backed by `/api/be/api/sighting-assist` 200 (source
   bedrock, glossary links to gates/integrity/provenance/level1-psth, submit_path
   `/moderation`). Backend: `src/aws_backend/routers` sighting-assist.

## Honesty caption

Presentable. The reply separates encounter likelihood (modeled, "rough reference,
not a forecast") from sighting verification ("Evidence-backed interpretation, not a
yes/no oracle"), cites gates/provenance/Level 0 QC, and labels detections as model
output. Lock 3 holds.

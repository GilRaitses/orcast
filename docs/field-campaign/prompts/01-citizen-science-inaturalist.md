# Citizen science → iNaturalist → hotspot pipeline

## Purpose

Explain how public observations enter the same validation pipeline as research-grade sightings.

## Narrative

An observer on San Juan Island spots orcas and logs the sighting in iNaturalist with a photo, location, and timestamp. ORCAST ingests that record through the iNaturalist adapter, normalizes it to the common sighting schema, and runs cross-validation against nearby verified OBIS records and other sources.

Validated citizen observations increase hotspot probability in their grid cell. Unvalidated or conflicting records receive lower confidence scores. The probability report lists reason codes such as source count, recency, and validation status so readers can judge trust themselves.

## Data to cite

- Backend endpoint: `POST /api/sightings/ingest` (scheduled Lambda)
- Source adapter: `src/aws_backend/sources/inaturalist.py`
- Report output: `POST /api/reports/probability`
- Demo route: `/historical`

## Infographic brief (for LLM)

**Headline:** Citizen science feeds the same pipeline as research data

**Layout:** Left-to-right flow: Observer → iNaturalist app → ORCAST ingest → cross-validation → hotspot grid

**Bullets:**
- Public photos and GPS pins become normalized sightings
- Cross-validation checks against OBIS and other sources
- Confidence scores reflect validation, not just volume
- Reports show reason codes for every hotspot

**Chart type:** Horizontal process diagram with one small map inset showing a hotspot cell brightening after validation

**Colors:** Navy background, teal accents, white text (match ORCAST site)

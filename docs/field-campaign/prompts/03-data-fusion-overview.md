# Multi-source data fusion overview

## Purpose

Summarize how ORCAST combines four data families into one probability report.

## Narrative

ORCAST does not treat any single feed as ground truth. Instead, ingestion pulls from OBIS verified sightings, NOAA environmental conditions, OrcaHello detections where enabled, and Orcasound hydrophone metadata. Each source implements a common adapter interface and writes normalized sightings or context records to AWS storage (DynamoDB in production).

The probability report endpoint merges current hotspots, environmental correlation, and cross-validated sightings into ranked output with CSV export. One button on `/reports` triggers the full fusion path.

## Data to cite

- Status: `GET /api/status` (lists active sources)
- Report: `POST /api/reports/probability`
- Adapters: `src/aws_backend/sources/`
- Demo route: `/reports`

## Infographic brief (for LLM)

**Headline:** Four data sources, one probability report

**Layout:** Four input boxes (OBIS, NOAA, OrcaHello, Orcasound) converging on a central ORCAST report card

**Bullets:**
- Each source has a documented adapter
- Cross-validation before scoring
- Ranked hotspots with confidence
- CSV export for field use

**Chart type:** Sankey or funnel diagram

**Colors:** One color per source, teal for merged output

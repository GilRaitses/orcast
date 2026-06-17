# Cross-validation and trust scoring

## Purpose

Explain how ORCAST scores trust without hiding the logic.

## Narrative

When sightings arrive from different sources, ORCAST deduplicates by spatial proximity and time window, then assigns validation status based on agreement with verified OBIS records and multi-source corroboration. Each hotspot inherits aggregate metrics: detection count, validated detection count, source count, and recency.

Reason codes on the probability report translate these metrics into plain language (for example: multiple validated sources, recent activity, environmental alignment). Users can download CSV and audit every field.

## Data to cite

- Module: `src/aws_backend/validation.py`
- Scoring: `src/aws_backend/scoring.py`
- Report reasons: `src/aws_backend/reports.py`
- Demo: generate report at `/reports`, download CSV

## Infographic brief (for LLM)

**Headline:** Confidence comes from validation rules, not black-box AI

**Layout:** Decision tree: single source → low confidence; multi-source agreement → higher confidence

**Bullets:**
- Deduplication by space and time
- OBIS alignment raises validation tier
- Reason codes on every hotspot
- CSV export for audit trails

**Chart type:** Flowchart with green/yellow/red confidence bands

**Colors:** Green for validated multi-source, yellow for single-source, muted red for conflicting

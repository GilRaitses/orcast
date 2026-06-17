# Verified OBIS backbone

## Purpose

Show why verified OBIS sightings are the trusted baseline for ORCAST scoring.

## Narrative

Southern Resident Killer Whale research relies on curated sighting catalogs. ORCAST loads verified OBIS records from the local OBIS adapter at startup and after each ingestion run. These records anchor the cross-validation step: newer observations are compared against this backbone for spatial and temporal consistency.

Hotspots with multiple validated OBIS-aligned sightings score higher than cells with only unverified single-source pins. The historical map at `/historical` displays this backbone so users see the difference between verified research data and provisional reports.

## Data to cite

- Endpoint: `GET /api/verified-sightings`
- Adapter: `src/aws_backend/sources/local_obis.py`
- Data file: `archive/public-templates-backup-20250720/api/verified-sightings.json`
- Demo route: `/historical`

## Infographic brief (for LLM)

**Headline:** Verified OBIS sightings are the trust anchor

**Layout:** Central column of verified pins on a Salish Sea map; arrows from OBIS database into ORCAST storage

**Bullets:**
- Research-grade catalog loaded at ingestion
- New sightings validated against this backbone
- Validation status drives confidence scores
- Transparent attribution in every report row

**Chart type:** Map with two pin styles (verified vs provisional) plus a small legend

**Colors:** Gold pins for verified OBIS, blue for provisional

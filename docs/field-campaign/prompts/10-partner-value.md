# Partner value proposition

## Purpose

Articulate what research groups, tour operators, and citizen science networks gain from a pilot.

## Narrative

Partners receive ranked hotspot reports with transparent reason codes, CSV export, and documented data sources at no cost during the pilot. ORCAST handles ingestion, cross-validation, and scoring on AWS so partners do not maintain separate ETL pipelines. Research groups gain audit trails for methodology papers; tour operators gain a daily briefing format; citizen science networks see their observations reflected in validation status rather than disappearing into a black box.

Agent chat and GPU demos are optional research UI layers, not prerequisites for partnership.

## Data to cite

- Partners page: `/partners` on the live site
- Doc: `docs/PARTNERSHIP_SUMMARY.md`
- Report endpoint: `POST /api/reports/probability`

## Infographic brief (for LLM)

**Headline:** What partners get from an ORCAST pilot

**Layout:** Three columns — Research / Tours / Citizen science — each with 3 bullet outcomes

**Bullets:**
- Transparent reports with reason codes
- No ETL burden on partners during pilot
- CSV + API for integration
- Open methodology for co-authored validation

**Chart type:** Three-column value card layout

**Colors:** Navy background, teal headers, white body text

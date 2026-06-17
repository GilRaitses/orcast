# Probability report sample

## Purpose

Walk through a real probability report output for field and partner conversations.

## Narrative

The probability report is ORCAST's primary deliverable for the August field pilot. A user sets a minimum confidence threshold and clicks Generate. The backend returns a report ID, summary text, region metadata, and a ranked list of hotspots. Each hotspot includes probability, confidence, coordinates, detection counts, and reason codes.

Users can download CSV for offline sharing on boats or in meetings. Sample output lives in `demo/cache/` for offline demos when AWS is torn down.

## Data to cite

- Endpoint: `POST /api/reports/probability`
- Sample CSV: `demo/cache/` (recorded during cache refresh)
- Demo route: `/reports`
- Cypress spec: `cypress/e2e/probability-report.cy.ts`

## Infographic brief (for LLM)

**Headline:** One report, ranked hotspots, exportable CSV

**Layout:** Mock report card with top 3 hotspots and a CSV download button callout

**Bullets:**
- Report ID and generation timestamp
- Ranked hotspots with coordinates
- Reason codes explain each ranking
- CSV for field partners

**Chart type:** Document mockup with table rows and highlight on reason codes column

**Colors:** White report card on navy background

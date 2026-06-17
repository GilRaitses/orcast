# Hotspot heatmap scoring

## Purpose

Describe how grid clusters become probability and confidence surfaces.

## Narrative

After ingestion, ORCAST generates hotspots by clustering normalized sightings in a spatial grid over the Salish Sea and San Juan archipelago. Each cell receives a probability score and confidence interval based on validated counts, source diversity, and environmental modifiers from NOAA data.

The ML predictions view and spatial forecast endpoint expose this grid as a heat surface rather than isolated pins. Tour operators and researchers can compare cells side by side using the same numbers that appear in the probability report.

## Data to cite

- Endpoint: `GET /api/hotspots`
- Spatial grid: `POST /forecast/spatial`
- Demo routes: `/ml-predictions`, `/agent-spatial-demo`

## Infographic brief (for LLM)

**Headline:** From scattered pins to ranked heat cells

**Layout:** Map transitioning from point sightings to colored grid cells with a probability legend

**Bullets:**
- Grid clusters normalize density
- Probability and confidence per cell
- Environmental modifiers from NOAA
- Same scores in reports and maps

**Chart type:** Before/after map pair with shared legend (0–100% probability)

**Colors:** Blue low → teal mid → warm high probability

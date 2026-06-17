# Spatial forecast grid

## Purpose

Explain the `/forecast/spatial` endpoint and how it powers map heat surfaces.

## Narrative

The spatial forecast endpoint accepts a center point, radius, grid resolution, and forecast horizon. It returns a grid of probability values over the Salish Sea study area. The ML predictions component visualizes this grid as a heat surface; the agent spatial demo uses the same backend data with interactive overlays.

This is deterministic scoring in v1, not a neural network inference service. Label it honestly in public materials: physics-informed grid scoring with documented inputs.

## Data to cite

- Endpoint: `POST /forecast/spatial`
- Module: `src/aws_backend/scoring.py` (`spatial_forecast_grid`)
- Demo routes: `/ml-predictions`, `/agent-spatial-demo`

## Infographic brief (for LLM)

**Headline:** Spatial probability grid over the archipelago

**Layout:** Map with semi-transparent heat overlay and grid lines; inset showing API request parameters

**Bullets:**
- Configurable radius and resolution
- Returns lat/lng/probability tuples
- Powers ML map and agent demo
- Same backend as probability reports

**Chart type:** Map heatmap with parameter callout box

**Colors:** Teal gradient heat on dark bathymetry-style base

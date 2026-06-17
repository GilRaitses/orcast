# San Juan archipelago coverage

## Purpose

Show geographic scope and map bounds for the field pilot.

## Narrative

ORCAST focuses on the Salish Sea with emphasis on the San Juan archipelago and surrounding waters. Map components use expanded bounds so users see context from the Strait of Georgia through Haro Strait. Hotspot scoring uses the same coordinate reference system as ingestion adapters.

Field week conversations should reference this map extent so partners know which waters are in scope for v1 scoring versus future expansion.

## Data to cite

- Map bounds: `agent-spatial-demo.component.ts` (expanded Salish Sea bounds)
- Default forecast center: San Juan Island vicinity (48.5465, -123.0307)
- Demo routes: `/historical`, `/agent-spatial-demo`, `/main-map`

## Infographic brief (for LLM)

**Headline:** San Juan archipelago in Salish Sea context

**Layout:** Regional map with highlighted pilot zone box and labeled waterways

**Bullets:**
- San Juan Islands core pilot area
- Salish Sea context for migration routes
- Shared bounds across demo maps
- v1 scoring covers this extent

**Chart type:** Regional map with shaded pilot polygon

**Colors:** Teal outline on muted blue-green water background

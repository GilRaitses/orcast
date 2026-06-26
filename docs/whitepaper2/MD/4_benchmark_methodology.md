# Section 4: Benchmark methodology and 8-scenario results

## Setup

The benchmark uses the Gemini Interactions API (endpoint: `generativelanguage.googleapis.com/v1beta/interactions`, Api-Revision: 2026-05-20, model: gemini-3.5-flash) with the `google_maps` tool enabled at San Juan Islands coordinates (48.5465, -123.03). Eight scenarios run in parallel via Python asyncio, each submitting a distinct query with a distinct RAG context type. Run date: 2026-06-24. The benchmark tool is `tools/testing/grounding_parallel_rag.py`.

## Scenarios

| # | Label | Context injected | Query type |
|---|-------|-----------------|------------|
| 1 | Maps-only orca evidence | None | Where are SRKWs seen + evidence |
| 2 | + gates context | Live gate data via `/api/be/api/gates` | Same + gate framing |
| 3 | + provenance context | Cell provenance via `/api/be/api/provenance` | Cell intensity + kernels |
| 4 | + surface planner step-log | Full planning step-log from `/api/interactions/plan` | Gates blocking promotion |
| 5 | Maps-only sighting check | None | Black dorsal fin, encounter likelihood |
| 6 | + sighting-assist context | Live sighting-assist output | Same + orcast data |
| 7 | Maps-only trip planning | None | Shore-based whale watching plan |
| 8 | + hotspots context | Live hotspot probability data | Same + orcast forecast |

## Results

| Scenario | $R_\text{uncited}$ | Scientific claims | Interpretation |
|----------|-------------------|------------------|----------------|
| 4 (planner step-log) | **0%** | 0 | Full grounding: artifact-reference transformation |
| 8 (+ hotspots) | 75% | 4 | Partial lift: structured data substitutes partially |
| 1 (Maps-only orca) | 60% | 10 | Maps baseline (variable across runs) |
| 7 (Maps-only trip) | 100% | 4 | Maps baseline for planning queries |
| 2 (+ gates) | 100% | 4 | No lift: gate data too narrow |
| 3 (+ provenance) | 100% | 4 | No lift: provenance too specific |
| 5, 6 | 100% | 2-7 | Sighting check: high baseline |

## Key observations

**Scenario 4 achieves 0% by artifact transformation, not citation generation.** When the surface planner step-log is injected as context, the model does not produce new science claims. The query ("Which gates block promotion right now?") is answered from the step-log artifact references — gate IDs, skill invocations, and panel assignments — rather than from world knowledge. The query type shifts from open-domain science to closed artifact-reference. This is not an improvement in citation generation; it is a change in what kind of claims the model makes.

**Scenario 8 achieves partial lift through partial substitution.** Hotspot probability data provides the model with specific numerical claims (encounter probability, hotspot location) that partially replace generic science claims. The remaining 75% uncited rate corresponds to scientific claims the model makes about orca ecology that the hotspot data does not cover.

**Scenarios 2 and 3 achieve no lift despite data injection.** Gate data and cell provenance data are too narrowly structured relative to the science claims the model independently generates about orca ecology. Injecting these data types does not change what science claims the model makes; it only adds the gate data as a separate context that the model doesn't draw science claims from.

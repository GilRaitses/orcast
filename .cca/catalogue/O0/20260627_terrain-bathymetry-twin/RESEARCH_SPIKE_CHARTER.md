# Research spike: how to build this environment correctly

Home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`
Trigger: operator observed that the current surface-plus-water look is wrong. The water
is always present but the land renders inconsistently and vanishes. Operator asked for a
wave of agents to research the literature on setting up a geospatial terrain and
bathymetry ocean environment correctly, to ground the bathymetry in real sounding
measurements rather than a map, to consider a chart or map cartographic style, and to
find out whether AI material and shader generation is real and usable.

This spike is read-mostly. Each agent writes ONE brief under `research/`. No code edits,
no commits. Each brief must cite real sources with URLs or paper references, state
concrete recommendations, and end with a section "implications for orcast" that maps the
findings onto our actual stack and decisions.

Stack context for every agent: Next.js + react-three-fiber + three@0.169 +
`3d-tiles-renderer@0.4.28`. The pilot is OGC 3D Tiles 1.1 baked from NOAA NCEI CUDEM 1/9
arc-second topobathy, NAVD88 m, EPSG:32610, currently a SINGLE root tile with no LoD.
Agent A realism adds a Gerstner water plane at scene Y 0. Study area is the San Juan
Islands and Haro Strait, including the Canadian side. Honesty constraint: modeled outputs
are labeled "modeled, not measured".

Hold: the W2 Phase-B integrator (wiring into the live scene) is ON HOLD pending this
spike. W2 Phase-A module producers continue, since they are reusable either way.

## Agents (parallel, 6, each owns one brief in research/)

| Agent | Owns | Question |
|---|---|---|
| R1 terrain-rendering-sota | `research/R1_terrain_rendering_sota.md` | how is large-area DEM plus bathymetry terrain rendered correctly on the web; LoD, tiling, streaming; why do tiles vanish |
| R2 bathymetry-soundings | `research/R2_bathymetry_soundings.md` | authoritative real sounding and multibeam sources; soundings vs gridded DEM; datums; how to ingest |
| R3 chart-cartography | `research/R3_chart_cartography.md` | nautical chart and topo cartographic portrayal of a 3D bathymetry model; isobaths, depth-area tints, S-52 and S-101, hypsometry |
| R4 ocean-water-rendering | `research/R4_ocean_water_rendering.md` | real-time ocean rendering literature; how water and terrain coexist correctly; shoreline, depth sorting, underwater |
| R5 ai-materials-shaders | `research/R5_ai_materials_shaders.md` | is AI material and shader generation real and usable; tools, papers, pipelines; feasibility for our terrain, seafloor, water |
| R6 orcast-render-diagnosis | `research/R6_orcast_render_diagnosis.md` | grounded diagnosis of why our land tiles vanish, against our actual code, cross-referenced to R1 and R4 |

Synthesis: the orchestrator merges the six briefs into a recommendation that updates the
visual program decision record and the W2 frame decision before the integrator runs.

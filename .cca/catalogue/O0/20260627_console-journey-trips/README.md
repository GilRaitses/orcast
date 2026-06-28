# Console Journey + Trips waveset

Home for the console-journey program: a continuous intent loop on the live 3D console
(`web/` Next.js + react-three-fiber) where camera motion, a place-search affordance, and the
orchestrator chat slot transduce user intent into served forecasts and a real Trips planner
grounded in open transit data (ferries, flights, road traffic).

Lane: O0 forecast ML-ops (console/orchestrator surface). Status: CHARTERED, pending operator GO.

## File set

| File | Role |
|------|------|
| `WAVESET_CHARTER.md` | Canonical prose charter (waves, roles, gates, return contract) |
| `VISUAL_PROGRAM_CHARTER.md` | The cinematic camera + search fly-through program (East Sound beat) |
| `wave_shape.yml` | Machine-readable shape (waves, agents, beats, sources) |
| `DECISION_RECORD.md` | Operator-confirmed decisions (answer before launch) |
| `W1_DISPATCH.md` | Wave 1 producer prompts (camera, search, geocode, atmosphere, connections recon) |
| `W2_DISPATCH.md` | Wave 2 integrator prompts (map_viewport->camera bridge, intent loop, fly-through, transit clients) |
| `W3_DISPATCH.md` | Wave 3 journey prompts (trips planner branches, kayak, sidequests, charter-auth chip) |
| `CONNECTIONS_RESEARCH.md` | Open-source transit data screen + honesty labels (WSF, WSDOT, OpenSky, gazetteer) |
| `STEP_LOG.md` | Orchestrator synthesis trace (newest last) |

## Premise

Intent today arrives only in discrete bursts (a chat message or a click). If the camera is always
gently moving (a slow orbit around the last focus), camera state becomes a continuous intent signal
(target, altitude, dwell, subject). The chat slot reads that stream plus explicit input, the
orchestrator serves into motion (fly / descend / route / orbit), and the loop closes. Trips is the
first journey built on that loop, grounded in real transit data so "get me to the islands and back
for my flight" is answerable, not decorative.

## Honesty labels (carried on every served surface)

- Forecast on the map stays the hotspot heuristic; `effective_confidence` honesty is unchanged.
- Ferry sailings / vessel positions / sailing space: MEASURED (WSF API real-time).
- Road ETA now: MEASURED (WSDOT real-time). Future-departure ETA: MODELED (self-collected history).
- Seaplane times: PUBLISHED schedule (static), not live.
- Geocoding: open (gazetteer + self-hosted Photon), no proprietary dependency.

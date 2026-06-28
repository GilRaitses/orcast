# STEP_LOG (newest last)

## 2026-06-27 — Charter authored

- O0 grounded the program in the live code via two recon passes: the console is `/` ->
  `AdaptiveExplore` -> `SalishScene` (react-three-fiber + three + 3d-tiles-renderer); camera is
  OrbitControls only (no fly-to / orbit / search); the orchestrator `map_viewport` ui_intent exists
  but is text-only (the seam to make real); Trips exist only in legacy Angular `/plan` and unused
  `js/agentic/`.
- Operator confirmed: full 3-wave scope; real Trips planner (lift trip-hierarchy); connections
  grounding for Anacortes ferry, seaplane, and SeaTac road traffic.
- Connections sources screened and confirmed (2026-06-27): WSF API (open, free; vessel locations,
  schedule, sailing space, wait times) = measured; WSDOT Traveler API (open, free; travel times +
  flow) = measured realtime, with future-departure ETA MODELED from a self-collected history log
  (API has no history); flights via OpenSky (live positions, may block AWS IPs) + SkyLink/AviationStack
  (freemium boards) + Kenmore Air static seaplane schedule (published); geocoding via curated gazetteer
  + self-hosted Photon (open), no Google.
- Authored: README, DECISION_RECORD, WAVESET_CHARTER, VISUAL_PROGRAM_CHARTER, wave_shape.yml, W1/W2/W3
  dispatches, CONNECTIONS_RESEARCH.
- Status: CHARTERED, pending operator GO on DECISION_RECORD items 4-8 and the WSDOT access code, then
  W1 launch.

## 2026-06-27 — Launch thread hydrated; operator GO; W1 dispatched

- New launch-orchestrator thread hydrated from files (HANDOFF_CHARTER, HYDRATION_PACKET, DECISION_RECORD,
  WAVESET_CHARTER, VISUAL_PROGRAM_CHARTER, CONNECTIONS_RESEARCH, W1/W2/W3 dispatches, wave_shape.yml) and
  returned the §H ack. Confirmed the live surface files exist (`SalishScene.tsx`, sandbox
  `tiles3d/TilesSandboxScene.tsx`, `js/agentic/trip-hierarchy-model.js`, `realism/atmosphere.ts`).
- Operator GO on DECISION_RECORD items 4-8 (all proposed defaults accepted): gazetteer-first geocoding;
  WSDOT + self-built corridor model for traffic; SkyLink + OpenSky + static seaplane for flights; extend
  the live home console in place; no ML promotion.
- Corridor history posture decided: START real WSDOT travel-time collection NOW (no synthetic bootstrap
  unless still thin at W3). Needs the access code + W2 WSDOT client + a poller, so the poller is the
  earliest W2 task once the code lands.
- WSDOT access code: operator registering (assisted) at https://wsdot.wa.gov/traffic/api/; store in
  `.env` as `WSDOT_ACCESS_CODE`. Gates W2, not W1.
- W1 launched: six parallel producer subagents per W1_DISPATCH.md (camera-director, search-affordance,
  geocode-gazetteer, atmosphere-transition, connections-recon, trips-schema). Discipline enforced:
  one-file-one-owner, no dev server, type-check / unit-test validation, no commit/deploy/promote,
  return diff + validation only.

## 2026-06-27 — W1 gate PASSED

All six W1 producers returned clean. Deliverables (new, uncommitted):
- A camera-director: `web/lib/scene/camera/{director,types,easing,index}.ts` + sandbox
  `web/app/(sandbox)/journey/{page,JourneyHost,JourneyScene}.tsx`. Pure ref-driven director,
  per-frame `update(dt)`, reuses `projectToScene`/`unprojectFromScene` + sandbox fit radius.
- B search-affordance: `web/app/components/scene/SearchAffordance.tsx` (self-contained overlay, `osa-`
  scoped styles, `onSearch`/`idleCollapseMs`; left a typed `__SearchAffordanceStory` ref export to
  strip during W2 wiring). NOT wired into SalishScene (correct).
- C geocode-gazetteer: `web/lib/geo/gazetteer.ts` + test (40 places; `resolvePlace` fuzzy; Photon
  gated off unless `PHOTON_URL`; `PlaceBounds` structurally == `HeightmapBounds` in sceneIntent).
- D atmosphere-transition: `web/lib/scene/atmosphere/transition.ts` (`rollInFog`, `descentLighting`
  over caller-supplied fog/light; reads realism public surface only: `FogOptions`/`skyColor`/`fogColorForSky`).
- E connections-recon: finalized `CONNECTIONS_RESEARCH.md` (endpoints+fields confirmed; access-code
  casing pinned `apiaccesscode` WSF vs `AccessCode` Traffic; OpenSky OAuth2; SkyLink 12h window;
  adapter signatures for wsf/wsdot_traffic/flights/seaplane).
- F trips-schema: `web/lib/trips/model.ts` + test (Trip->Day->DayTrip->Stop->Activity->ViewingZone,
  `JourneyBranch` union, constructors/validators; sample trip validates + round-trips).

Gate evidence:
- Combined `cd web && npx tsc --noEmit` => exit 0, zero diagnostics (all six owners together).
- `/journey` compiles (HTTP 200) and renders the real CUDEM tileset.
- East Sound choreography verified live via browser HUD `getState()` sampling: followPath beat
  (subject "Anacortes to Orcas ferry", alt ~61->26 m) -> orbit (subject "East Sound", target
  48.6600,-122.9050, orbiting=yes). Motion real; getState feeds subject/altitude/target/isOrbiting.
- Recon doc lists confirmed endpoints + the SeaTac<->Anacortes TravelTime route candidates.

W1 findings carried forward:
- HONESTY/SCOPE (W3): WSDOT TravelTimes covers I-5 only to ~Arlington (MP 208). The final ~40 mi
  (Arlington->Mount Vernon->SR20->Anacortes) has NO realtime route, so even "now" that leg is
  MODELED, not measured. Corridor model + connections planner must emit a composite measured+modeled
  label, never blanket "measured" (B.6).
- W3 schema foot-gun: trip metadata rollups (totalCost/overallProbability/confidence) are LAZY
  (recompute only on addDay/addDayTrip); planner must call updateTripMetadata before serving panels.
- W2 cleanup: strip the `__SearchAffordanceStory` throwaway export when the Viewport Bridge mounts it.

Status: W1 COMPLETE. W2 is unblocked for its web phase-A producers (intent transducer, fly-through
choreography). W2 backend clients (WSF, WSDOT) + the corridor history poller wait on the WSDOT access
code (operator registering). Dev server stopped (W2 is a parallel wave: no dev server).

## 2026-06-27 — W1 visual gate CORRECTION + Director remediation launched

Operator reviewed /journey and reported: no sky, no fog, no water, wrong land materials, and the ferry
POV is too fast and "dunks into the water." Correct. The prior W1 gate verified camera MOTION and
getState but did NOT critically judge the rendered image (visual-verification rule not satisfied in
spirit). Gate reopened: motion PASS, visual coherence FAIL.

Root cause (read both scenes): the live SalishScene.tsx already renders sky/fog/water/lit terrain via
RealismRig (applyRealism = lights + atmosphere/fog + sky) and Water2Rig (makeWater2 = depth-driven
Beer-Lambert ocean). Agent A's sandbox JourneyScene.tsx omitted BOTH rigs (only 3 basic lights + bare
tileset + flat gradient background), so no water/sky/fog and default tile materials. The shot
descendTo(15 m) then followPath(25 m) over 9 s is far too low/fast, so the POV plunges at the waterline.

Decision: do NOT switch engines. B.1 locks the engine and the assets already exist and render in
SalishScene. Google Earth Studio is an offline keyframe->video tool, not a live engine (cannot drive
map_viewport / show the CUDEM twin / carry beacons). CesiumJS would discard the working
3d-tiles-renderer + CUDEM + water2 + picking + beacon stack to re-reach where SalishScene already is.
Escalate to an engine switch ONLY if the Director cannot reach visual coherence on three/r3f.

Launched: a DIRECTOR subagent (cinematography + provisioning) owning the sandbox journey files + camera
director tuning + a tracked VISUAL_DEFICIENCY_REGISTER.md. It composes the SAME realism modules
SalishScene uses (read-only on realism/ and water2/), wires the W1 atmosphere transition (rollInFog /
descentLighting), re-choreographs with sane altitudes (camera clamped above the water surface, slower
eased pacing, proper look-at), and verifies by reading rendered screenshots across the beats.

WSDOT access code received from operator and stored in gitignored .env (WSDOT_ACCESS_CODE); one code
serves WSF (apiaccesscode) and Traffic (AccessCode). This unblocks W2 backend clients + the poller.
Launched the WSF + WSDOT fixture clients in parallel (collision-free with the web Director work). Held
the web intent-transducer + journey-controller until the Director lands the visual foundation, since
they compose the same journey scene/camera.

## 2026-06-27 — W2 backend clients in; W1 visual gate PASSED (independently verified)

W2 backend (WSF + WSDOT), both live-validated with the operator access code:
- src/aws_backend/sources/wsf.py + tests/aws_backend/test_wsf.py (19 passed). Live smoke: 200,
  13 terminals, recon fields matched the wire format field-for-field. sailing_space suppresses
  drive-up/reservable counts to None (not a misleading 0) when display flags are false (B.6 at the
  data layer). apiaccesscode lowercase. Graceful + no network when code absent.
- src/aws_backend/sources/wsdot_traffic.py + tests/aws_backend/test_wsdot_traffic.py (20 passed).
  Live smoke: 163 travel-time routes, 1465 flow stations; corridor resolves SeaTac-Seattle(43),
  Seattle-Lynnwood(27), Seattle-Everett(4), Everett-Marysville(268), Everett-Arlington(267), HOV
  variants excluded. Real feed uses RoadName "005" + Direction "N"/"NB" so resolution keys on Name.
  Coverage-gap test asserts no corridor route reaches Mount Vernon/Anacortes/SR20. History log live
  at data/external/traffic_corridor/seatac_anacortes.jsonl (gitignored). AccessCode PascalCase.

Journey Director remediation (the operator-reported visual fix):
- Reworked web/app/(sandbox)/journey/JourneyScene.tsx to compose the SAME rigs as SalishScene:
  RealismRig (applyRealism: sun+ambient+hemisphere lights, distance fog, elevation-driven sky
  background), Water2Rig (makeWater2 with the per-frame depth pre-pass before auto-render, amplitude
  0.18), pinned midday sun. Wired W1 atmosphere transition: rollInFog as the opening cut mask, a
  second rollInFog clears during descent, descentLighting on the descent beat.
- Re-choreographed: flyTo establishing ~2400 m (4.5 s) -> descendTo 230 m (4.5 s) -> followPath
  Anacortes->Orcas 17 s (alt eases 240->182 m, lookAhead 0.1 forward-and-down) -> orbit East Sound
  fitRadius*0.4 @ 820 m, speed 0.05.
- Added an additive no-dunk clamp in web/lib/scene/camera/director.ts (enforceAltitudeClamp): eye
  lifted to the higher of 40 m metric clearance and 0.5-unit wave headroom above max(waterY=0,
  getSurfaceY), applied every tween/orbit/move-start frame. Exported API + getState shape unchanged.
- New tracked artifact: VISUAL_DEFICIENCY_REGISTER.md (every element missing->present with source
  module, fix, and verifying screenshot; honesty note: real CUDEM at Y=0, depth-driven water, fog
  labeled as atmosphere, no invented bathymetry/places).

Gate evidence (orchestrator-verified, not taken on the subagent's word):
- Read all four Director beat screenshots (establishing/descent/follow/orbit): real sky, depth-driven
  water with shoreline foam, lit islands, sea haze; camera above water in every frame.
- Independent live run on a fresh dev server (port 3012) via browser: sampled getState across the full
  ~25 s sequence -> MIN ALTITUDE 207 m (no dunk anywhere), settles into East Sound orbit at 820 m.
- Combined `cd web && npx tsc --noEmit` => exit 0 after the Director's edits.
- Decision NOT to switch engines stands: three/r3f reaches the needed visual quality; assets already
  existed in-repo and now compose into the journey scene.

Status: W1 visual gate PASSED. W2 phase-A backend DONE. Remaining for W2 phase A: the two held web
producers (intent transducer, fly-through controller) can now build on the proven visual foundation,
then W2 phase B (Viewport Bridge, single editor of SalishScene.tsx) wires it into the live console.
The W1 Search Affordance __SearchAffordanceStory throwaway export still to be stripped at W2 wiring.

## 2026-06-27 — Program expanded to multi-waveset; R+D waves launched; orchestrator decisions

Operator expanded scope: each remaining work stream becomes a waveset running a six-wave lifecycle
(Research, Discovery, Implementation, Adversarial, Remediation, Acceptance). Authored
PROGRAM_WAVESETS_CHARTER.md. Operator confirmed: four wavesets (WS-INTENT, WS-SCENIC, WS-BATHY,
WS-TRIPS); topology = one program orchestrator (this thread) + one background suborchestrator per
waveset + a convergence calendar (SalishScene edited INTENT -> SCENIC -> BATHY; planner.py +
ActiveSurfaceHost = TRIPS only); start all four Research+Discovery in parallel (read-only). Added
roles: Terrain Stylist + Scenic Decorator (under the Director, WS-SCENIC); bathy special teams
(WS-BATHY). Corridor poller relaunched as a tracked background job (the nohup child was reaped when its
launcher shell exited); history accruing again.

Orchestrator decisions recorded:
- WS-INTENT: granted web/app/components/AdaptiveExplore.tsx to WS-INTENT (phase B, additive, single
  editor) to close the planner-initiated map_viewport->camera loop. No other waveset touches it.
- WS-SCENIC defaults accepted (suborchestrator recommendations, all lock-respecting): land = derived
  elevation/slope biome tint via material.onBeforeCompile/TSL (no external data; ESA WorldCover CC BY
  4.0 drape deferred as optional); horizon = true-scale decorative DEM ring from AWS Terrain Tiles
  (labeled decorative, not surveyed); sky = vendored three.js Sky (Preetham) addon, no new dependency,
  sun-driven; Sky dome owns background (realism background:false); discrete vegetation deferred.
- Cross-waveset notes to carry into gating: WS-INTENT lighting-dim deferred to WS-SCENIC; carry a
  no-dunk water-amplitude note to WS-BATHY if amplitude rises above ~0.32 units (clamp headroom).

R+D status: WS-INTENT done (dispatch proposed). WS-SCENIC done (dispatch proposed). WS-BATHY and
WS-TRIPS R+D still running.

## 2026-06-27 — All four R+D done; implementation phase-A fanned out

WS-BATHY R+D: the served CUDEM tileset is ALREADY topobathy (NCEI CUDEM 1/9 arc-sec wash_bellingham,
-376..+734 m NAVD88; per infra/3dtwin/host/WIRING-host.md), so the modeled seafloor is baked into the
render geometry and water2 already reads it. WS-BATHY is a styling + provenance build, not a new
seabed. WS-TRIPS R+D: four branches map onto the existing JourneyBranch contract; composite weakest-leg
honesty label; corridor model fits the live history; kayak reuses modeling/tide_harmonic.py (modeled).

Operator decisions:
- Flights: launch with Kenmore seaplane (published static) + SeaTac board only; DEFER live OpenSky
  positions until an off-AWS proxy + SkyLink/AviationStack keys exist.
- Bathymetry: ship modeled-only with a clear "modeled" label now; stage BlueTopo (US) + NONNA (BC)
  measured-coverage overlay as a fast-follow (NONNA is chart-datum, never rendered as seabed).
- Orchestrator defaults: TRIPS 5-file panel registration kept with the single phase-B editor; kayak
  tide via server-side props (no new route); connections as panel props (not a gated skill); BATHY
  water2 absorption upgrade allowed only as a reviewed request to the water2 owner.
- Implementation: GO, all non-colliding phase-A producers in parallel.

Phase-A fan-out (all disjoint files, no convergence files touched, no dev server; type-check / fixture
validation; producers commit/deploy/promote nothing):
- WS-INTENT: Intent Transducer (web/lib/intent/transducer.ts + additive adaptiveConsole.ts),
  Fly-through Controller (web/lib/journey/controller.ts).
- WS-SCENIC: Terrain Stylist (web/lib/scene/terrain/), Scenic Decorator (web/lib/scene/decor/).
- WS-BATHY: Depth Stylist (web/lib/scene/bathy/style/), Honesty Labeler (web/lib/scene/bathy/honesty/);
  measured-overlay provenance producer deferred (modeled-only scope).
- WS-TRIPS: Connections Planner (casting/trips/connections.py), Flights+Seaplane
  (sources/seaplane.py + sources/flights.py, board+seaplane only), Corridor Model
  (modeling/traffic/corridor.py), Kayak Panel (console/KayakPanel.tsx), Sidequests+Auth
  (console/SidequestPanel.tsx).
Phase B (convergence, serialized, held): SalishScene INTENT->SCENIC->BATHY; planner.py +
ActiveSurfaceHost = TRIPS. Each waveset then runs Adversarial -> Remediation -> Acceptance.

## 2026-06-27 (late) — Implementation + convergence COMPLETE; visual acceptance PASSED

All 11 phase-A producers + 4 phase-B convergence editors landed type-clean / fixture-green
(backend pytest 306 passed; web tsc exit 0 throughout). Convergence order honored: SalishScene
INTENT -> SCENIC -> BATHY; TRIPS planner+registry in parallel. Corridor<->connections field/assembly
seam reconciled in a planner.py adapter (eta_minutes->eta, dict interval->[low,high], basis dict->
flat string, per-route summation + always-modeled northern Arlington->Anacortes leg).

Director live visual acceptance gate (dev server :3020, Playwright capture, frames read by both the
Director and O0): ALL 5 original complaints PASS + bathy depth/shoreline seam PASS + horizon
coherence PASS. Screenshots in acceptance_screenshots/ (gate_rest, gate_search_00..05,
gate_zoom_rest_canvas, gate_trips_panels). O0 independently verified gate_rest, gate_zoom_rest_canvas,
gate_search_02/04, gate_trips_panels.

Open items (NOT gate blockers):
- TRIPS live-route end-to-end gap: trip panels were verified via a throwaway harness mounting the
  real ActiveSurfaceHost components, NOT through the live anonymous-public home route, because the
  served anonymous planner's allowed_panels excludes the trip panels and the dev backend
  /api/be/...plan returned 500s. The seed surface-planner-v1.json was updated with the 5 panel ids,
  but the SERVED planner config + the backend plan endpoint need wiring/redeploy to surface trips to
  an anonymous visitor. Recommended next remediation.
- Cosmetic: faint white glitter specks near the horizon at very low grazing altitude (sun glitter +
  a few horizon-ring high points). Low-priority polish wave.
- Deferred fast-follows: BlueTopo/NONNA measured bathy overlay; live OpenSky positions (needs
  off-AWS proxy + keys); server-side kayak tide computation from tide_harmonic; descentLighting dim
  (lights handle now exposed, rig not yet wired).

Discipline held throughout: sub-agents committed/deployed/promoted nothing; no git add; secrets in
.env only. Operator commits.

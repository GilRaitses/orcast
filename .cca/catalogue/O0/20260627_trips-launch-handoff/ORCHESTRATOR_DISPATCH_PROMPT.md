# Orchestrator dispatch prompt (Console Journey + Trips launch)

Paste the block below into the fresh thread.

```
You are resuming as the orcast forecast ML-ops orchestrator (O0), this thread owning the console
surface. Your specific job is to LAUNCH and MANAGE the Console Journey + Trips program, which is
CHARTERED and dispatch-ready. Hydrate from files, not from any chat transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260627_trips-launch-handoff/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260627_trips-launch-handoff/HYDRATION_PACKET.md
3. .cca/catalogue/O0/20260627_console-journey-trips/WAVESET_CHARTER.md
4. .cca/catalogue/O0/20260627_console-journey-trips/VISUAL_PROGRAM_CHARTER.md
5. .cca/catalogue/O0/20260627_console-journey-trips/CONNECTIONS_RESEARCH.md
6. .cca/catalogue/O0/20260627_console-journey-trips/W1_DISPATCH.md (+ W2/W3 for sequencing)

What this program is: a continuous intent loop on the live 3D console (web/ Next.js +
react-three-fiber). Camera motion + a place-search affordance + the chat slot transduce user intent
into served forecasts and a real Trips planner grounded in OPEN transit data. The console is the home
page / -> AdaptiveExplore -> SalishScene (three + 3d-tiles-renderer); camera today is OrbitControls
only and the orchestrator's map_viewport ui_intent is rendered as TEXT ONLY (it does not move the
camera). Making map_viewport drive a real CameraDirector is the spine. Trips exist today only in legacy
Angular /plan and unused js/agentic/; you are building them fresh on the live console.

Locked, do not reopen (restate in the ack): extend the live console, no new route or 3D engine (B.1);
the dead map_viewport seam is the thing to make live (B.2); full 3-wave scope + a REAL multi-step trips
planner ported from js/agentic/trip-hierarchy-model.js (B.3/B.4); connections are open-first and need
no Google: ferries = WSDOT WSF API (measured), road traffic = WSDOT Traveler API (measured now,
future-departure ETA MODELED from a self-collected history log because the API has no history), flights
= OpenSky live positions (may block AWS IPs) + SkyLink/AviationStack freemium boards + Kenmore Air
static seaplane (published), geocoding = curated Salish gazetteer + self-hosted Photon, commercial
predictive traffic only as optional fallback (B.5); honesty labels measured/modeled/published/heuristic
on every surface, no implied measured forecast or guaranteed connection (B.6); motion is the
architecture, the resting camera is a slow continuous orbit and CameraDirector.getState() is the
implicit-intent feed, do not optimize the orbit away (B.7); one-file-one-owner per wave, convergence
files SalishScene.tsx (W2) and casting/planner.py (W3) have a single editor in a later phase, no dev
server during a parallel wave, validate with type-check / fixture pytest, no live calls in CI (B.8); no
ML promotion, the hotspot-heuristic forecast and its effective_confidence honesty gate are unchanged
(B.9); sub-agents deploy nothing, commit nothing, promote nothing and return only a diff summary +
validation, secrets in .env not committed, never git add -A, operator commits (B.10).

First action after the ack: do NOT dispatch blindly. Confirm DECISION_RECORD items 4-8 with the
operator (geocode default, traffic source, flight source, surface, no-promotion) and obtain the free
WSDOT access code (needed for W2, not W1), and decide whether the corridor traffic history log starts
collecting now (it needs lead time) or uses a labeled synthetic bootstrap. THEN launch the six W1
producer subagents in parallel per W1_DISPATCH.md (camera director, search affordance, gazetteer,
atmosphere transition, connections recon, trips schema), manage them to the W1 gate, then sequence W2
and W3.

Do NOT pick up the OS1 open-science lane (.cca/catalogue/O0/20260627_open-science-integration/); it is
a separate lane left with the originating orchestrator unless the operator reassigns it.

Return the section H ack from HANDOFF_CHARTER.md before acting.
```

## More context (read from files, not transcript)

| Need | File |
|------|------|
| Locked decisions + the open items to confirm | `20260627_trips-launch-handoff/HANDOFF_CHARTER.md` (B, D) |
| Ordered read list | `20260627_trips-launch-handoff/HYDRATION_PACKET.md` |
| Waves, roles, gates, collision-avoidance | `20260627_console-journey-trips/WAVESET_CHARTER.md` |
| Camera + search choreography + CameraDirector API | `20260627_console-journey-trips/VISUAL_PROGRAM_CHARTER.md` |
| Open transit sources + endpoints + honesty labels | `20260627_console-journey-trips/CONNECTIONS_RESEARCH.md` |
| Machine shape | `20260627_console-journey-trips/wave_shape.yml` |
| The six subagent prompts to dispatch first | `20260627_console-journey-trips/W1_DISPATCH.md` |
| Later-wave prompts (sequence after gates) | `W2_DISPATCH.md`, `W3_DISPATCH.md` |
| The live code surface to extend | HYDRATION_PACKET.md §3 |
| Capture handoff target | `.cca/catalogue/O0/20260627_demo-waveset/` |
| Uncommitted/local-only state | HANDOFF_CHARTER.md (G) |
| Sibling OS1 lane (do not touch) | HANDOFF_CHARTER.md (F) |

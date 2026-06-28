# Decision record (answer before launch)

Operator-confirmed choices that lock the charter. Confirmed items are marked CONFIRMED; the rest are
proposed defaults awaiting operator GO.

## Confirmed

1. Scope: full 3-wave program (camera + search + atmosphere, the intent loop, the Trips branches).
   CONFIRMED.
2. Trips depth: real multi-step planner (lift the `js/agentic/trip-hierarchy-model.js` schema into
   the live backend), grounded in real transit data, not a scripted demo shell. CONFIRMED.
3. Connections grounding requested: Anacortes ferry times, seaplane times, and SeaTac road-traffic
   prediction for catching / returning from a flight. CONFIRMED.

## Confirmed by operator 2026-06-27 (items 4-8 GO; all proposed defaults accepted)

4. Geocoding: curated Salish-Sea gazetteer (offline, deterministic, ~40 named places with bounds) as
   the core, plus self-hosted Photon for live typeahead. No Google. Default: gazetteer-first. CONFIRMED.
5. Road-traffic prediction source: WSDOT Traveler API for real-time, plus a self-collected
   historical travel-time log feeding a time-of-day / day-of-week corridor model for future-departure
   prediction (open, project-consistent). Commercial predictive API (Google / HERE / TomTom) left as
   an optional fallback only. Default: WSDOT + self-built model. CONFIRMED.
   - 5b. Corridor history posture: START COLLECTING REAL WSDOT TRAVEL-TIME HISTORY NOW (begins
     accruing lead time immediately; requires the access code + the W2 WSDOT client + a scheduled
     poller). No synthetic bootstrap unless real history is still too thin at W3. CONFIRMED.
6. Flight schedule source: SkyLink free tier (1000 req/mo) for SeaTac departure/arrival boards;
   OpenSky for live positions (proxied off-AWS); Kenmore Air seaplane as a published static schedule.
   Default: SkyLink + OpenSky + static seaplane table. CONFIRMED.
7. Target surface: extend the live home console (`/` -> `AdaptiveExplore` -> `SalishScene`), not a new
   route or engine. Default: extend in place. CONFIRMED.
8. No new ML model promoted by this program. The map forecast stays the hotspot heuristic with its
   existing honesty gate. Default: no promotion. CONFIRMED.

## Access code status

- WSDOT Traveler API access code: operator is registering (assisted). Register email at
  https://wsdot.wa.gov/traffic/api/ -> code arrives by email -> store in `.env` as
  `WSDOT_ACCESS_CODE`, never committed. Gates W2 (WSF + WSDOT clients) and the W2/W3 corridor poller;
  does NOT gate W1. W1 launches in parallel while the code arrives.

## Hard rails (non-negotiable)

- One file, one owner per wave. No two agents edit the same file in the same wave.
- No dev server during a parallel wave; validate with type-check (`npm run build` / `tsc`).
- No deploy, no promotion, no commit by sub-agents. Operator commits.
- Large media (capture videos, tilesets) go to object storage, never the repo.
- Secrets (API access codes) live in `.env` / deploy config, never committed.

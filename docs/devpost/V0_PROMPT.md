# v0.app prompt + integration contract (polished submission UI)

Use this to generate the polished submission UI on [v0.app](https://v0.app). The functional baseline is already in [web/](../../web); v0 produces a nicer skin that wires to the same backend through the same keyed proxy. After v0 generates, follow "Porting" below.

## Paste this into v0.app

> Build a Next.js (App Router) + Tailwind dashboard called "orcast". Dark, modern, data-forward, marine theme (deep navy, teal accent). It visualizes a whale-encounter forecast whose confidence is governed by automated fitness gates and a human promotion step. Four routes:
>
> 1. `/` Forecast: a full-width map hero (Google Maps via @vis.gl/react-google-maps, key from NEXT_PUBLIC_MAPS_KEY) centered on the San Juan Islands (48.55, -123.05, zoom 10). Above or over it, a confidence meter (0-100%) with a "human-promoted / unpromoted" badge and the line: "The forecast is always shown. Its sharpness is governed by the fitness gates and a human promotion step, not hidden behind an experimental label." A "Run re-fit" button. Tapping a water cell opens a provenance modal.
> 2. `/gates` Fitness gates: a dashboard of cards. A header card (status, confidence %, promoted badge, McFadden pseudo-R2, covariates). A "human promotion decision" card (shown only when a pending approval exists) with the supervisor recommendation + Promote/Hold/Reject buttons. A Level-1 table (covariate, modulation, null z, null p, beats-null pass/fail badge). A 2x2 grid of cards: held-out CV, time-rescaling GOF, PIT calibration, PSTH-vs-kernel consistency, each with pass/fail badges.
> 3. `/moderation` Community moderation queue: a list of pending shore sightings (place, datetime, behavior, count, observer, notes, coordinates, pending badge) with Approve/Reject buttons.
> 4. Provenance modal: shows modeled intensity, confidence, a table of kernel contributions (kernel, phase, log-rate, gate badge), and a nearby-evidence table (source, distance, date).
>
> All data comes from a same-origin proxy at `/api/be/<backend-path>` (GET and POST). Do NOT call the backend directly and do NOT use an API key in the browser. Use pass/fail color badges (green pass, red fail, amber n/a). Make it look production-ready.

## Backend integration contract

The polished app must talk to the backend exactly like [web/lib/api.ts](../../web/lib/api.ts): all calls go through `/api/be/<path>`.

Endpoints (all relative to the proxy, e.g. `GET /api/be/api/gates`):

- `GET /api/gates` -> `{ status, confidence, promoted, pending_approval, data_inventory, baseline_scorecard, level0_detector_qc, gates: { level1_psth, cross_validation, time_rescaling, pit, consistency }, metrics, covariates_fit, repr_id, run_id }`. `pending_approval` is public-safe and never includes a task token.
- `GET /api/provenance?lat&lng[&station&tide_phase]` -> `{ intensity, confidence, kernel_contributions:[{kernel,available,phase,log_rate_contribution,beats_null,null_p}], nearby_evidence:[{sighting_id,distance_km,source,timestamp}], trace_note }`
- `GET /api/realtime/events` -> `{ events:[{id, location:{lat,lng}, source}] }` (map overlay)
- `GET /api/community/submissions?status=pending` -> `{ submissions:[{id,place,latitude,longitude,observed_at,behavior,count,notes,observer_name,status}] }` (keyed; proxy injects the key)
- `POST /api/community/submissions/{id}/approve` and `/reject` (keyed)
- `POST /api/decision-records` body `{ verdict:"promote"|"hold"|"reject", reason }` (keyed). The proxy/backend stamp WorkOS reviewer identity and resolve the task token server-side.
- `POST /api/orchestrator/run` (keyed) - triggers a re-fit
- `GET /api/decision-records` -> `{ records:[...] }`
- `GET /api/review-dossier/latest` and `/api/review-dossier/{id}/export` -> review dossier and audit packet JSON (keyed)

## Porting (after v0 generates)

1. Copy these two files from the baseline into the v0 project unchanged:
   - [web/app/api/be/[...path]/route.ts](../../web/app/api/be/[...path]/route.ts) (the keyed server proxy)
   - [web/lib/api.ts](../../web/lib/api.ts) (typed client helpers)
2. Point the v0 components at `getJSON` / `postJSON` from `lib/api.ts` (already same-origin).
3. Set the three env vars in the Vercel project: `ORCAST_API_BASE`, `ORCAST_API_KEY` (server-only), `NEXT_PUBLIC_MAPS_KEY`.
4. Add the Vercel production domain to the Google Maps key HTTP-referrer allowlist.
5. Deploy. Because the proxy is server-to-server, no backend CORS change is needed.

The baseline `web/` already implements all of the above, so if v0 stalls, ship `web/` and treat v0 as a cosmetic upgrade.

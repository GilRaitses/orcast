# Stage 0 SET, readiness manifest

Director: DEMO-PROD. Stage: SET (DSET). Assembled from `findings/SET-*.md`, each
asserted only from a Read-examined runtime observation against the live target.

## Locked capture target

`https://orcast-h0.vercel.app` (prod alias). No local dev server started. No
long-lived processes; no ports/pids recorded.

## Prerequisite table

| id | Prerequisite | Serves | Status | Read-examined evidence |
|---|---|---|---|---|
| SET-web | Capture target reachable | all | READY | GET `/` 200; hero `h1.hero-title` "orcast. Explore the Salish Sea" in HTML; 3D scene paints in frame `set_home.png` |
| SET-maps | Google Maps usable | A1, A4, A5 | READY | `/ask` frame `set_ask_map.png`: gm-style mounted, 12 Google tiles painted, "Map data ©2026 Google", no Maps error |
| SET-session | Reviewer/agent session | A6, B1, B2 | READY | `/api/be/api/community/submissions` 401 unauth vs 200 with `X-ORCAST-Agent-Key` returning the 6-item reviewer queue; key matches prod |
| SET-forecast | Live forecast + gates, honest 0% promoted | A1, A4 | READY | `/gates` renders "Status: fitted · confidence 0% · promoted" + integrity conditions + evidence chain |
| SET-twin | Sandbox twin route renders land at waterline | B3 | READY | `/journey` 200; frame `set_journey.png` shows land at waterline + W1 Camera Director HUD; canvas 641x564 |

## Advance gate

All 5 prerequisites READY from real observations. Every live beat's prerequisites
are READY, so beats A1-A6, B1, B2, B3 may enter BLK. No NOT-READY blockers. No
operator gate hit during SET (the agent credential was reachable locally and
matched the prod-deployed key; no paid surface needed standing up).

## Carried notes for BLK (not blockers)

1. SET-maps: `/` primary surface is the 3D `SalishScene`, not Google Maps (Maps is
   the `SceneHost` fallback). Maps tile painting is proven on `/ask`. A1 "map" is the
   3D scene; confidence-meter/0% on the home surface to be confirmed in BLK A1.
2. SET-session: in-browser reviewer-pane rendering for capture uses Playwright
   route injection (`web/e2e/loadAgentCreds.ts:installAgentAuth`); the session itself
   is verified working in prod.
3. SET-twin: B3's labeled-place pan and a deployed (non-sandbox) twin route are
   direction per BEAT_SET; the sandbox route renders land at waterline now.

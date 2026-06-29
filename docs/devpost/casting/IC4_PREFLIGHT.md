# IC4 preflight — G5 remediation probe

**Date:** 2026-06-23  
**Production base:** https://pjrftm3bkv.us-west-2.awsapprunner.com  
**Baseline gates:** `./tools/waves/run-gate.sh ic` PASS

## PF-1 — Reproduce G3-D-01 (CV badge vs negative skill)

```bash
curl -s "$BASE/api/gates" | jq '{gate_pass: .gates.cross_validation.gate_pass, mean_skill: .gates.cross_validation.mean_deviance_skill, n_pass, n_folds, caveats}'
```

**Result (2026-06-23 prod):**

| Field | Value |
|-------|-------|
| `gate_pass` | `true` |
| `mean_deviance_skill` | `-0.018` |
| `n_pass` / `n_folds` | `3` / `5` |
| Matching caveat | "Mean held-out deviance skill is negative; fold-majority CV pass should be treated cautiously." |

**Verdict:** G3-D-01 **confirmed**. UI showed pass badge while mean skill negative; backend caveat already present.

## PF-2 — API.md inventory diff

**Documented in Supported table today:** read paths, forecast, reports (partial), ingest/recompute.

**Missing from Supported (live in `main.py`):**

| Group | Paths |
|-------|-------|
| Kernel | `GET /api/gates`, `GET /api/provenance` |
| Governance | `GET/POST /api/decision-records`, `POST /api/promotion/draft`, `POST /api/promotion/apply`, `POST /api/orchestrator/run` |
| Review | `GET /api/review-dossier/latest`, `GET /api/review-dossier/{id}`, `GET /api/review-dossier/{id}/export` |
| Community / journal | `/api/community/*`, `/api/journal/*` |
| Exploration | `/api/explore/*`, `/api/sighting-assist/*` |
| Casting | `/api/managed-agents/*`, `/api/interactions`, `/api/interactions/prepare`, `/api/interactions/status` |
| Timeseries | `GET /api/data-status`, `POST /api/timeseries/backfill`, `POST /api/timeseries/refresh` |
| Partner | `POST /api/partner/verify`, `GET /api/partner/tiers` |

**Wrong auth in API.md:**

| Path | Documented | Actual |
|------|------------|--------|
| `POST /api/reports/probability` | none | `require_api_key` when `ORCAST_API_KEY` set |

## PF-3 — Reports auth on prod

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE/api/reports/probability" ...
```

**Result:** HTTP **503** (`ORCAST_API_KEY is not configured` on App Runner at probe time). When key is set, route requires `X-ORCAST-Key` (see `reports.py`).

## PF-4 — Angular badge audit (G3-C-01)

| Route | Current badge | Truth label (target) |
|-------|---------------|----------------------|
| `/reports` | Live API | Live API |
| `/historical` | Live API | Live API |
| `/ml-predictions` | Live API | Live API |
| `/realtime` (extra card) | Live API | Historical data |

## PF-5 — Regression baseline

| Gate | Result |
|------|--------|
| `./tools/waves/run-gate.sh ic` | PASS |
| `./tools/waves/run-gate.sh H0` | PARTIAL — governance curls 503 (App Runner `ORCAST_API_KEY` unset); journal/sighting-assist OK |

## IC4 exit bar

- [x] Gates CV card shows **caution** when `gate_pass=true` and `mean_deviance_skill<0` (local dev `http://localhost:3460/gates`, 2026-06-23)
- [x] `docs/API.md` lists governance, kernel, explore, casting routes with correct auth
- [x] Angular landing uses per-route truth badges
- [x] `./tools/waves/run-gate.sh ic4` PASS (2026-06-23)

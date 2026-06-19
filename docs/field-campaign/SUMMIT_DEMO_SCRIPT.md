# AWS Summit NYC — booth demo script

**Duration:** 2 minutes · **Audience:** AWS visitors, potential partners, technical reviewers

## URLs to share

| Use | URL |
|-----|-----|
| Primary (CloudFront) | https://d2gslju5drx74c.cloudfront.net/ |
| Custom domain | https://orcast.org/ |
| Backend health | https://pjrftm3bkv.us-west-2.awsapprunner.com/health |
| API catalog | [docs/API.md](../API.md) |

Generate QR codes for CloudFront and orcast.org landing pages.

## Opening (20 sec)

> "orcast is a pilot study on forecast durability for orca sighting probabilities on the San Juan islands: San Juan, Orcas, Lopez, and Shaw. It supports maps and planning tools by integrating sighting catalogs, hydrophone and crowd sound tags."

Show landing page `/`. Point out the four live demo cards and the demo disclaimer.

## Demo flow (2 min)

### 1. Home → Probability report (45 sec)

- Navigate to `/reports`
- Set confidence slider → **Generate report**
- Point out named places (Friday Harbor, Lime Kiln, Rosario Strait) — not decimal coordinates
- Mention CSV download as an optional export for field partners — not the hero moment

### 2. Historical sightings (45 sec)

- Navigate to `/historical`
- Show sighting markers on the map
- "Cross-validated sightings from OBIS and other catalogs anchor the maps."

### 3. Partners CTA (30 sec)

- Navigate to `/partners`
- August field week in San Juan archipelago
- mailto contact@orcast.org

## Disclaimers

- The chat-style map demos are scripted. The report page and CSV export call the live API on AWS.
- Map demos (`/live-demo`, `/agent-demo`) use scripted UI; report summaries are not from a chatbot
- `/realtime` shows recent sightings and a static hydrophone catalog — no live acoustic stream
- Legacy Cloudflare prediction/analysis/DTAG routes return **410 Gone** on AWS — use probability reports (see [docs/API.md](../API.md))
- Live iNaturalist ingestion may be disabled; OBIS + NOAA + hydrophones are core

## Offline fallback

If venue Wi‑Fi blocks AWS:

```bash
bash scripts/demo-start.sh
cd orcast-angular && npm start
# Demo at http://localhost:4200/reports
```

## After the summit

```bash
bash scripts/teardown.sh   # optional — stop AWS charges
```

See `FIELD_WEEK_RUNBOOK.md` for August prep.

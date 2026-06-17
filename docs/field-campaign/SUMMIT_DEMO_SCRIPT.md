# AWS Summit NYC — booth demo script

**Duration:** 5 minutes · **Audience:** AWS visitors, potential partners, technical reviewers

## URLs to share

| Use | URL |
|-----|-----|
| Primary (CloudFront) | https://d2gslju5drx74c.cloudfront.net/ |
| Custom domain | https://orcast.org/ |
| Backend health | https://pjrftm3bkv.us-west-2.awsapprunner.com/health |
| API catalog | [docs/API.md](../API.md) |

Generate QR codes for CloudFront and orcast.org landing pages.

## Opening (30 sec)

> "ORCAST fuses whale sightings from research catalogs, environmental data, and hydrophones into transparent probability reports for the Salish Sea. The fusion pipeline runs on AWS App Runner with DynamoDB and S3. Agent chat is a research prototype — the reports are live."

Show landing page `/`.

## Demo flow

### 1. Probability report (90 sec)

- Navigate to `/reports`
- Set confidence slider → **Generate report**
- Point out: region, model version, hotspot list, **reason codes**
- Click **Download CSV** — "This is what field partners take on a boat."

### 2. Historical backbone (60 sec)

- Navigate to `/historical`
- "Verified OBIS sightings anchor trust. Citizen science goes through the same validation."

### 3. Spatial score grid (60 sec)

- Navigate to `/ml-predictions` (labeled **Score grid** in nav)
- "Deterministic hotspot probability surface — `POST /forecast/spatial`, not ML inference."

### 4. AWS architecture (30 sec)

- App Runner API, DynamoDB storage, S3 reports, CloudFront frontend
- Scheduled Lambda ingestion (optional detail if audience is technical)

### 5. Field pilot CTA (30 sec)

- August field week in San Juan archipelago
- `/partners` for collaboration
- mailto contact@orcast.org

## Honest disclaimers

- Agent demos (`/live-demo`, `/agent-demo`) use simulated agent UX; `queryAgent()` returns report summaries, not LLM output
- `/realtime` shows recent sightings and a static hydrophone catalog — not live acoustic detection
- v1 scoring is deterministic fusion (`aws-deterministic-hotspot-v1`), not GPU PINN inference
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

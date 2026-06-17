# ORCAST field week runbook (August 2026)

Last week of August · San Juan archipelago · Southern Resident orca context

## Before you leave

- [ ] Confirm AWS stack status: `cat infra/aws/state/deployment-manifest.json`
- [ ] Run smoke test: `python3 tools/testing/test_aws_backend_smoke.py --base-url <BACKEND_URL>`
- [ ] Refresh offline cache: `bash scripts/rebuild.sh --local-only` or full `bash scripts/rebuild.sh`
- [ ] Test offline demo: `bash scripts/demo-start.sh` + `cd orcast-angular && npm start`
- [ ] Print sample CSV from `demo/cache/`
- [ ] QR codes for CloudFront and orcast.org landing pages

## Demo order (5 minutes)

1. **Landing `/`** — honest overview: fusion pipeline live, agents prototype
2. **`/reports`** — Generate report → show reason codes → Download CSV
3. **`/historical`** — Verified OBIS backbone on map
4. **`/ml-predictions`** — Spatial probability grid
5. **Offline proof** — Wi‑Fi off, cached API on `:8080`, same reports flow

## Commands in the field

```bash
# Live AWS API (if stack is up)
open https://d2gslju5drx74c.cloudfront.net/reports

# Laptop-only fallback
bash scripts/demo-start.sh
cd orcast-angular && npm start
# Browse http://localhost:4200/reports

# Stop demo server
bash scripts/demo-start.sh stop
```

## What to ask partners

- Do hotspot rankings match your local knowledge?
- Are reason codes understandable on a phone screen?
- What data source is missing (vessel AIS, hydrophone detections, etc.)?
- Would you use CSV on a daily basis during whale season?

## After field week

```bash
bash scripts/teardown.sh   # stop AWS charges
```

Keep `demo/cache/` in git for winter outreach. Record notes in a new `docs/field-campaign/field-notes-YYYY-MM-DD.md` file.

## Cost reminder

- AWS live: ~$71–81/mo idle; tear down between events
- Offline demo: $0
- Firebase/Cloudflare hosting: low traffic ≈ $0

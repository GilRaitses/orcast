# ORCAST self-contained demo

Everything needed to demo ORCAST without AWS after teardown lives here.

## Quick commands

```bash
# Rebuild AWS + refresh cache (costs ~$71–81/mo while running)
bash scripts/rebuild.sh

# Rebuild cache only from local memory backend (free)
bash scripts/rebuild.sh --local-only

# Tear down AWS; keep offline demo
bash scripts/teardown.sh

# Start offline demo API on :8080
bash scripts/demo-start.sh

# Start live in-memory backend instead of frozen cache
bash scripts/demo-start.sh --live

# Stop demo server
bash scripts/demo-start.sh stop
```

## What is cached

`demo/cache/` holds frozen JSON (and sample CSV) for:

- `/health`, `/api/sightings`, `/api/hotspots`, `/api/live-hydrophones`
- `/api/environmental`, `/forecast/quick`, `/forecast/spatial`
- `/api/reports/probability` plus a sample report + CSV

`manifest.json` records when and where the cache was captured.

## Angular

Point at local demo (automatic after `demo-start.sh` or `teardown.sh`):

```bash
cd orcast-angular && npm start
```

`environment.ts` uses `http://127.0.0.1:8080`.

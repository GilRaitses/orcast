# C-GAP coverage report (live)

Generated from the live ingest run on 2026-06-27 (America/New_York), window_h=24.
Read-only feasibility pass. Answers "can we find 40 candidates near hydrophones?".

## Reachable confirmed sightings

- In-region sightings in store: 93
- Confirmed (verified/likely) in-region: 91 (visual)
- OrcaHello history records indexed (live): 1359 (cached to orcahello_index.cache.json)
- OrcaHello confirmed acoustic candidates: 166
- Combined candidate pool: 257

## Hydrophone / tier feasibility

- Within 5 km of an in-region hydrophone: 184
- Within 10 km: 200 (cap)
- Tier A (<=5 km AND OrcaHello overlap): 166
- Tier B: 34
- Tier C: 0

## Verdict

- Target >= 40 candidates with >= 20 tier-A. Reachable: 257 in the pool, 166 tier-A.
  Comfortably met. The build caps at 200 (tier-A-first), all four in-region hydrophones
  represented.

## External blocker (recorded)

- The OrcaHello history API (aifororcasdetections.azurewebsites.net) intermittently returns
  HTTP 403 / SSL EOF, especially after heavy paging. A successful fetch is cached locally
  (`orcahello_index.cache.json`) and reused so the build is reproducible while the API is
  flaky. This is the same external intermittency recorded in G4_DATA_WIRING_STATUS.md.

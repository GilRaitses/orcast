# C-VERIFY report

Verified 2026-06-27 (America/New_York) against `candidates.targets.json`.

## Exit bar

- Candidates: 200 (target >= 40). PASS.
- Tier A (within 5 km of a hydrophone AND >= 1 OrcaHello overlap): 166 (target >= 20). PASS.
- Required join keys present on every candidate: PASS.
- Every candidate `cross_validation_status` in {verified, likely}: PASS.

## Adversarial checks

- Every OrcaHello-sourced row labeled `source_kind: acoustic` (hydrophone position, not whale GPS): PASS.
- No fabricated rows: candidates derive only from live-ingested confirmed sightings and
  reviewed-confirmed OrcaHello detections.

## Composition

- source_kind: acoustic 166, visual 34.
- sources: orcahello_history 166 (reviewed-confirmed detections), obis_verified 34.
- nearest hydrophone: orcasound_lab 146, andrews_bay 21, north_san_juan_channel 17, haro_strait 16.
- The 200 cap is tier-A-first, so it keeps the hydrophone-aligned candidates the charter
  prioritizes; the lower-scored visual sightings farther from hydrophones were dropped by the
  cap (the full reachable pool was 257).

## Provenance and honesty

- OrcaHello index provenance: live (1359 records), cached to `orcahello_index.cache.json` for
  reproducibility while the external API is intermittent (403s on heavy paging).
- No model trained. Effective confidence remains 0%. Acoustic detections remain acoustic
  context, not whale tracks.
- `noaa_tide_coverage` reflects NOAA CO-OPS prediction availability for the pilot region, not
  an observed-current span.

## Reproduce

```bash
.venv/bin/python tools/forecast_candidates/build_candidates.py build --live --max 200
# then the validation block in CANDIDATE_CHARTER.md
```

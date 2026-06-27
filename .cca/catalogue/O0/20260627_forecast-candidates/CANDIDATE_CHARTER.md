# CAND, forecast candidate-preparation waveset charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orcast-lane orchestrator
Home: `.cca/catalogue/O0/20260627_forecast-candidates/`
Family id: CAND

## Purpose

Assemble about 40 candidate confirmed sightings, each a coordinate plus a timestamp, that
join cleanly across the external data sources the system already collects, so they can seed
the forecasting feature pipeline and sharpen the B-side data-lineage demo beat (B-DATA in
`.cca/catalogue/O0/20260627_demo-waveset/W-STORY.md`). Candidates that sit near an in-region
hydrophone and overlap an OrcaHello annotation window are the top priority, because those are
the points where a visual sighting can be cross-referenced against an acoustic annotation
record.

This waveset prepares candidates. It does not train a model and does not claim forecasting
skill. The current fit earns 0% effective confidence and that does not change here.

## Grounding (what actually exists)

Confirmed in the live AWS backend and the committed data:

- Sighting sources: live OBIS with local seed fallback (`sources/obis.py`, `local_obis.py`),
  iNaturalist (`sources/inaturalist.py`), OrcaHello acoustic detections (`sources/orcahello.py`),
  and moderator-approved community submissions (`sources/community.py`). All normalize to
  `latitude`, `longitude`, `timestamp` in `NormalizedSighting` (`models.py`).
- "Confirmed" means `cross_validation.status` of `verified` or `likely`
  (`/api/verified-sightings`); community rows must be `approved`.
- In-region hydrophones (San Juan bounds 48.40 to 48.70, -123.25 to -122.75), from the
  Orcasound catalog `src/integrations/orcasound_hydrophones_for_orcast.json`:
  - Orcasound Lab, 48.5583362, -123.1735774
  - North San Juan Channel, 48.591294, -123.058779
  - Andrews Bay, 48.5500299, -123.1666492
  - Lime Kiln / Haro Strait, about 48.516, -123.152 (ONC `LKWA`; OrcaHello acoustic history
    keyed `haro_strait`)
- OrcaHello annotation records (the cross-reference target): cached reviewed labels (334) at
  stations `andrews_bay`, `haro_strait`, `north_san_juan_channel`, `orcasound_lab`, and an
  acoustic detection history of 761 records at `haro_strait` spanning 2020 to 2021
  (`data/models/snapshot_manifest.json`, `fit_report.json`). Live moderator outcomes via
  `sources/orcahello_history.py`.
- Covariates computable at any candidate point and time: diel and lunar (`covariates.py`),
  season (`modeling/design.py`), depth (`sources/bathymetry.py`, `data/geo/san_juan_bathymetry.json`),
  shore distance (`spatial_enrichment.py`), tide and currents (NOAA, `sources/noaa.py`),
  salmon prey index (`sources/salmon.py`, climatology fallback).

Feasibility check run at charter time:

- The committed static sighting files are sparse: `archive/.../api/verified-sightings.json`
  has 8 records, `.../data/verified-obis-sightings.json` has 10, `demo/cache/sightings.json`
  has 8. Of the 8 in the verified seed, 4 are within 5 km and 7 within 10 km of an in-region
  hydrophone.
- Therefore 40 distinct confirmed sightings cannot come from the committed static data alone.
  Reaching 40 requires the live OBIS plus iNaturalist pull and the OrcaHello acoustic
  detection history (the 761-record `haro_strait` snapshot is the densest in-region source,
  and it concentrates exactly in the hydrophone-and-annotation priority area). This is the
  honest answer to "can we find 40": yes, but only by pulling the live and cached feeds, and
  the acoustic-sourced candidates must stay labeled acoustic, not whale GPS.

## Locked decisions, do not reopen

1. Confirmed equals `cross_validation.status` in {verified, likely}; community equals approved.
2. Acoustic detections are at hydrophone coordinates, not whale positions. Candidates sourced
   from OrcaHello are tagged `source_kind: acoustic` and kept distinct from visual sightings.
3. "Source alignment" is scored only on real external overlaps: hydrophone proximity,
   OrcaHello annotation or detection temporal-window overlap, NOAA tide and current span
   overlap, and OBIS or iNaturalist membership. Universally computable features (diel, lunar,
   season, depth, shore) are recorded on each candidate but do not count as source alignment,
   because they are computable everywhere and would inflate the score.
4. No model training and no forecasting-skill claim in this waveset. Effective confidence
   stays 0% with the gate caveat.
5. Live network ingest (OBIS, iNaturalist, OrcaHello) needs operator approval before
   C-BUILD runs it. Commits and pushes need explicit operator approval.

## Waves

| Wave | Mode | Surface | Exit bar |
|------|------|---------|----------|
| C-GAP | discovery (read-only) | `GAP_COVERAGE.md` in this home | A coverage table: how many confirmed sightings are reachable per source, their spatial spread relative to the four hydrophones, the OrcaHello annotation and detection spans, the NOAA coverage spans, and a feasibility count for tier A. Read-only; no writes outside this home. |
| C-BUILD | build (bounded) | `candidates.targets.json` in this home | At least 40 candidates, each with the required join keys in `candidate_targets.schema.yml`; at least 20 in priority tier A (near a hydrophone and overlapping an OrcaHello annotation window). Validates with `make`-style check below. |
| C-VERIFY | verify | `CAND_VERIFY.md` in this home | Re-run the join and scoring check across all candidates, confirm the tier-A count and the join-key completeness, and flag any acoustic-sourced candidate not labeled as such. |

C-GAP runs first as a read-only gate and hands its coverage table to C-BUILD. C-BUILD writes
the targets file. C-VERIFY is adversarial and re-checks the file.

## Machine-verifiable exit (C-BUILD and C-VERIFY)

```bash
python3 - <<'PY'
import json
d = json.load(open(".cca/catalogue/O0/20260627_forecast-candidates/candidates.targets.json"))
c = d["candidates"]
req = {"sighting_id","source","source_kind","latitude","longitude","timestamp",
       "cross_validation_status","nearest_hydrophone","nearest_hydrophone_km",
       "orcahello_overlap_count","priority_tier"}
assert len(c) >= 40, f"need >=40 candidates, have {len(c)}"
for x in c:
    miss = req - set(x)
    assert not miss, f"{x.get('sighting_id')} missing {miss}"
    assert x["cross_validation_status"] in ("verified","likely"), x["sighting_id"]
tierA = [x for x in c if x["priority_tier"] == "A"]
assert len(tierA) >= 20, f"need >=20 tier-A, have {len(tierA)}"
print(f"OK: {len(c)} candidates, {len(tierA)} tier-A")
PY
```

## Out of scope

- Model training, retraining, or any change to the fitted kernels.
- pax surfaces and pax data.
- The whale-tagger / DTAG annotation store (separate B-side build; DTAG is 410 today).
- Writing candidates into the live `orcast-sightings` store. This waveset writes only the
  targets file in its home; promotion into any store is a separate, operator-approved step.

## Cross-links

- Feeds demo beat B-DATA in `.cca/catalogue/O0/20260627_demo-waveset/W-STORY.md`.
- Registered as family `CAND` in `docs/devpost/waves.registry.yaml` and `WAVES_REGISTRY.md`.

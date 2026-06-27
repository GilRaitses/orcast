# CAND dispatch prompts (self-contained subagent prompts)

Each prompt is self-contained per the wave methodology. The orchestrator owns verification.
Subagents do not commit or push.

## C-GAP (discovery, read-only)

> Read-only exploration of the orcast repo at `/Users/gilraitses/orcast`. Do not write any
> file except `.cca/catalogue/O0/20260627_forecast-candidates/GAP_COVERAGE.md`.
>
> Goal: quantify how many confirmed orca sightings (cross_validation status verified or
> likely) are reachable per source and how they align with the four in-region hydrophones, so
> the C-BUILD wave can assemble 40 candidates with at least 20 in tier A.
>
> Inventory and report, with counts and spans (not prose):
> 1. Per sighting source (OBIS `sources/obis.py` + seed `local_obis.py`, iNaturalist
>    `sources/inaturalist.py`, OrcaHello `sources/orcahello.py`, community `sources/community.py`):
>    how many records are reachable in-region (bounds 48.40 to 48.70, -123.25 to -122.75),
>    whether live or cached, and the lat/lng/timestamp field names.
> 2. For the OrcaHello annotation records (reviewed labels and acoustic detection history in
>    `data/models/snapshot_manifest.json` and `sources/orcahello_history.py`): the per-station
>    record counts and the time spans, keyed to orcasound_lab, north_san_juan_channel,
>    andrews_bay, haro_strait.
> 3. NOAA tide/current coverage spans (`sources/noaa.py`, ingested streams) that a candidate
>    timestamp could fall inside.
> 4. A feasibility count: estimated candidates reachable total, within 10 km of a hydrophone,
>    and tier A (within 5 km of a hydrophone AND overlapping an OrcaHello annotation window).
>
> Output the coverage table to GAP_COVERAGE.md. Do not run live network calls unless the
> parent has confirmed live ingest is approved; otherwise report cached/committed counts and
> mark live counts as pending-approval.

## C-BUILD (build, bounded; operator-gated on live ingest)

> Repo `/Users/gilraitses/orcast`. Write only
> `.cca/catalogue/O0/20260627_forecast-candidates/candidates.targets.json`.
>
> Using the coverage table in GAP_COVERAGE.md and the schema in
> `candidate_targets.schema.yml`, assemble at least 40 candidate confirmed sightings, at least
> 20 in tier A. For each candidate populate every required key, compute nearest_hydrophone and
> nearest_hydrophone_km (haversine to the four hydrophones in `wave_shape.yml`),
> orcahello_overlap_count (reviewed labels or acoustic detections at the nearest station within
> +/- 24 h), noaa_tide_coverage, the computable covariates, and the priority_score and
> priority_tier per `wave_shape.yml` priority_scoring. Tag OrcaHello-sourced candidates
> source_kind=acoustic. Set generated_at and status=populated in _meta.
>
> Honesty: confirmed equals cross_validation verified or likely only. Do not invent records;
> if a source is unavailable write null and set the matching coverage flag false. Do not write
> into any sighting store; only this targets file.
>
> Exit: the validation block in CANDIDATE_CHARTER.md prints OK. Iterate until it does. Do not
> commit or push.

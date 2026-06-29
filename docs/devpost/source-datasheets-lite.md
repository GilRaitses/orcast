# ORCAST Source Datasheets Lite

## OrcaHello / Orcasound Acoustic Detections

- Role: primary temporal spike train for kernel estimation.
- Collection: acoustic detector candidates from hydrophone stations.
- Current limitation: detections are unreviewed candidates; Level 0 detector ROC/d-prime characterization is planned.
- Use: temporal fitting and gate evidence with caveats.
- Do not use as: confirmed animal-presence labels without review.

## NOAA CO-OPS Water Level And Currents

- Role: tidal/current covariates for tide-phase estimation.
- Collection: NOAA current/water-level records and predictions.
- Current limitation: records must overlap the acoustic detection window; otherwise tide is excluded from the joint fit.
- Use: fit `k_tide` only when overlap and phase coverage are adequate.

## OBIS And iNaturalist Visual Sightings

- Role: visual evidence, validation/context, and future spatial/social layers.
- Collection: public biodiversity/sighting records.
- Current limitation: presence-only and effort-biased; source URLs exist when adapters provide them.
- Use: evidence overlay and validation, not the primary temporal kernel estimator.

## Community Reports

- Role: citizen-science sightings submitted through ORCAST.
- Collection: moderated shore/kayak reports.
- Current limitation: human effort and observer bias; approved reports receive low reliability weight.
- Use: social layer, corroboration, and future spatial/effort modeling.
- Governance: moderation now stamps reviewer metadata on approval/rejection.

## Bathymetry / Coastal Geography

- Role: static local spatial feature source.
- Collection: local `data/geo` assets.
- Current limitation: static feature read, not a streaming source.
- Use: future spatial habitat term `s_space`.

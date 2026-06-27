# W-STORY, locked demo script (B-side capturable beats)

Wave: DEMO / W-STORY. Status: locked 2026-06-27 (America/New_York).
Scope: the capturable B-side beats. A-side beats and needs-build beats are tracked in
`wave_shape.yml` and wait on their surfaces.

This is the contract W-CAPTURE and W-VOICE must not violate. Beat order is fixed. Each beat
has one line of narration and a fixed shot list. On-screen honesty captions are mandatory
and stay visible for the full beat. Every data-source claim in this script is grounded in
the inventory in the "Data lineage" section below; do not narrate a source or a feature that
is not in that table.

## Capture parameters (apply to every beat)

- Viewport 1280x900, Playwright `chromium-desktop`, `DEMO_RECORD=1` (`web/playwright.config.ts`).
- Base URL from `PW_BASE_URL`, default `https://orcast-h0.vercel.app`. Operator confirms the
  target before W-CAPTURE.
- Each silent webm must be at least as long as its narration line so the voice is not cut.
- The honesty caption is rendered as an overlay during assembly (W-ASSEMBLE), text taken
  verbatim from the Caption field below.

## What the demo is arguing

Encounter forecasting starts from one fact: a confirmed sighting is a coordinate and a
timestamp. Once the system has that anchor, every environmental factor it collects can be
sampled at that point and time and encoded as a feature, and the planner assembles those
features into an encounter probability surface. The demo shows where the sightings come
from, where the grounding data comes from, which factors are encoded as features today, and
the honest model state (effective confidence 0%, only the diel and lunar kernels fitted).

## Data lineage and the forecasting feature pipeline

This is the reference the data beat narrates from. Status is honest: "fitted" means the
covariate is in the current committed kernel fit; "available" means the source is wired and
the feature is computable but it is not in the fit yet; "validation only" means held out of
the fit by design.

### Where sightings come from (the anchor: latitude, longitude, timestamp)

| Source | Backend path | Live / cached | Role |
|--------|--------------|---------------|------|
| OBIS (live, with local seed fallback) | `src/aws_backend/sources/obis.py`, `local_obis.py` | live (`ORCAST_ENABLE_LIVE_OBIS`), seed fallback | verified occurrence backbone |
| iNaturalist | `src/aws_backend/sources/inaturalist.py` | live (`ORCAST_ENABLE_LIVE_INATURALIST`) | community visual observations |
| OrcaHello acoustic detections | `src/aws_backend/sources/orcahello.py` | live (`ORCAST_ENABLE_ORCAHELLO`) | acoustic candidate at a hydrophone position, not whale GPS |
| Community submissions | `src/aws_backend/sources/community.py` | internal store, moderator approved | citizen sightings after review |

All normalize to `NormalizedSighting` with `latitude`, `longitude`, `timestamp`
(`src/aws_backend/models.py`). "Confirmed" is not a single flag: it means
`cross_validation.status` of `verified` or `likely` (`/api/verified-sightings`), and
community rows must be moderator `approved` before ingest.

### What can be encoded as features at that coordinate and time

| Feature / covariate | Source path | Live / cached | In current fit? |
|---------------------|-------------|---------------|-----------------|
| diel (solar time of day) | `src/aws_backend/covariates.py` | computed | fitted |
| lunar phase | `src/aws_backend/covariates.py` | computed | fitted |
| tide / currents | `src/aws_backend/sources/noaa.py` (NOAA CO-OPS) | live to S3 | available, not fitted (phase coverage below threshold) |
| season (day of year) | `modeling/design.py` | computed | available, not fitted (extrapolated) |
| effort / station uptime | `src/aws_backend/sources/orcasound.py` | cached catalog | used as the exposure offset |
| depth / bathymetry | `src/aws_backend/sources/bathymetry.py`, `data/geo/san_juan_bathymetry.json` | static asset | available (provenance only), not fitted |
| shore distance | `src/aws_backend/sources/shoreline.py`, `spatial_enrichment.py` | live / derived | available, not fitted |
| salmon prey index | `src/aws_backend/sources/salmon.py` | climatology fallback | available, not fitted |
| NDBC met and ocean (wind, waves, water temp) | `src/aws_backend/sources/ndbc.py` | live | QC only, not fitted |
| AIS vessel traffic | `src/aws_backend/sources/ais.py` | live | effort proxy, not fitted |
| OBIS / iNaturalist occurrences | `obis.py`, `inaturalist.py` | live | held out for validation only |

Honest model state: the committed fit is a negative binomial GLM with two-harmonic Fourier
kernels, and only diel and lunar are fitted today. Effective confidence is 0% because the
held-out cross-validation skill is negative and time-rescaling fails. The pipeline that turns
a confirmed sighting plus these features into a probability surface is real; the trained
forecasting skill is not earned yet, and the demo shows that with the gate caveat on screen.

## Beat order (locked)

1. B1 ask the console
2. B-DATA data sources and the feature pipeline
3. B2 provenance drilldown
4. B3 hydrophone acoustic

---

## B1, ask the console

- Route: `/` (root console, `AdaptiveExplore`).
- Narration (one line): "A researcher asks the console which gates block promotion, and the
  orchestrator resolves an agent, plans the panels, dispatches a skill, and narrates the answer."
- Caption (on-screen, full beat): "Live orchestrator trace. Every step is schema-versioned
  and grounded."
- Shot list:
  1. Open `/`. Wait for the scene (`[data-demo="explore-scene"]`) and the console sidebar
     (`[data-demo="explore-console"]`) to be visible.
  2. Select the starter chip "Which gates block promotion right now?" so the textarea fills.
  3. Click "Send turn" (`[data-demo="explore-send"]`). The button reads "Orchestrating..."
     while busy.
  4. Wait for the active surface (`[data-demo="active-surface"]`). Hold on the orchestrator
     badge ("Orchestrator . {agent} . schema {version}").
  5. Hold on the trace (`[data-demo="orchestrator-trace"]`): the steps read Resolve managed
     agent, Plan ui_intent, Dispatch skill, Narrate reply.
  6. Pause on the Orchestrator reply in the replies card so the narration lands.
- Honesty note: the trace shows the real skill ids and statuses returned by the plan. Do not
  stage or hard-code steps.

## B-DATA, data sources and the feature pipeline

- Route: `/` then the realtime events overlay, then a provenance pin. Uses
  `GET /api/realtime/events` (each event carries a `source`) and `GET /api/provenance`.
- Narration (one line): "A confirmed sighting is just a coordinate and a timestamp, drawn from
  OBIS, iNaturalist, acoustic detections, and reviewed community reports, and that anchor lets
  the system encode tide, depth, diel, lunar, and prey as features for the forecast."
- Caption (on-screen, full beat): "Sources: OBIS, iNaturalist, OrcaHello, community. Fitted
  features today: diel and lunar only."
- Shot list:
  1. Open `/`. Wait for the scene and let the realtime events render on the map so points
     from more than one source are visible.
  2. Hold on the multi-source points (OBIS, iNaturalist, OrcaHello, community). Narration
     names the sighting sources from the Data lineage table.
  3. Open a provenance pin (click the scene or use `/?lat=48.5465&lng=-123.03&provenance=1`).
     Hold on the kernel contributions so the covariate-as-feature idea is visible.
  4. Narration names the feature sources from the Data lineage table and states that only
     diel and lunar are fitted today, the rest are wired but not yet in the fit.
- Honesty note: name only sources in the Data lineage table. Acoustic detections are at a
  hydrophone position, not a whale track. Do not imply tide, depth, season, or salmon are in
  the fitted model; they are available, not fitted.

## B2, provenance drilldown

- Route: `/?lat=48.5465&lng=-123.03&provenance=1`.
- Narration (one line): "Opening the provenance for a hot cell shows the detections and kernel
  contributions behind the value, with the effective confidence held at zero percent."
- Caption (on-screen, full beat): "Effective confidence 0%. Forecast gates not yet passed."
- Shot list:
  1. Open the provenance deep link. Wait for "Why is this cell hot?" and for
     "Tracing provenance..." to clear.
  2. Hold on the modeled intensity line ("Modeled intensity:") and the kernel contribution
     list (the fitted diel and lunar kernels).
  3. Hold on the effective confidence figure with the gate caveat visible. The value must read
     its true 0% effective confidence, never a promoted or inflated number.
- Honesty note: the live map path is a hotspot heuristic, not the validated kernel model. The
  narration says "effective confidence" and never claims a validated forecast.

## B3, hydrophone acoustic

- Route: `/` (root console). The hydrophone panel slots in by ui_intent after a hydrophone
  intent.
- Narration (one line): "Selecting a hydrophone slots in its recent acoustic signal panel from
  the live relay, an acoustic context layer, not a whale position."
- Caption (on-screen, full beat): "Acoustic moderator context. Hydrophone location, not whale
  GPS. Live spectrogram requires the ONC token."
- Shot list:
  1. Open `/`. Wait for the scene to load.
  2. Trigger a hydrophone intent (click a hydrophone beacon in the scene, or send a hydrophone
     prompt) so `onIntent` fires with a hydrophone panel.
  3. Wait for the hydrophone panel (`[data-panel="hydrophone_signal"]`, title "Hydrophone
     signal"). Hold on the station name and the spectrogram image when present.
  4. If the backend has no `ONC_API_TOKEN`, the panel shows station metadata and the message
     that a live spectrogram needs the token. Capture that honest degrade state as-is.
- Honesty note: OrcaHello and ONC tags are acoustic moderator labels at a fixed hydrophone
  position, distinct from biologging DTAG data and not a whale track.

---

## Captions index (verbatim, for W-ASSEMBLE overlays)

- B1: "Live orchestrator trace. Every step is schema-versioned and grounded."
- B-DATA: "Sources: OBIS, iNaturalist, OrcaHello, community. Fitted features today: diel and lunar only."
- B2: "Effective confidence 0%. Forecast gates not yet passed."
- B3: "Acoustic moderator context. Hydrophone location, not whale GPS. Live spectrogram requires the ONC token."

## Dependency on the candidate set

B-DATA is strongest when the map shows a dense, multi-source set of confirmed sightings near
the in-region hydrophones. That candidate set is prepared by the CAND waveset
(`.cca/catalogue/O0/20260627_forecast-candidates/`). B-DATA can be captured today with
whatever the live feeds return; it is sharper once CAND lands the prioritized 40.

## Exit bar (W-STORY)

Locked when beat order, the shot lists, the narration lines, the captions above, and the Data
lineage tables are fixed. MET on 2026-06-27.

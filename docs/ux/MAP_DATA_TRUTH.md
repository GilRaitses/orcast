# Map data truth

Rules that keep the map honest: orcas only on water, the pilot area only, feeds only where they are, and no pod identity we do not have. Design intent for a later build; cites the code that would change.

Related: [USER_JOURNEYS.md](USER_JOURNEYS.md), [DYNAMIC_MAP_UX.md](DYNAMIC_MAP_UX.md).

## Evidence (why this exists)

- Seed sightings sit on shore/land. Lime Kiln Point in [`verified-sightings.json`](../../archive/public-templates-backup-20250720/api/verified-sightings.json) is `48.5158, -123.1526`, essentially on San Juan Island's west shore. Hotspot centers come from clustering in [`scoring.py`](../../src/aws_backend/scoring.py) and can land on terrain.
- Feeds scatter far outside the San Juans. In [`orcasound_hydrophones_for_orcast.json`](../../src/integrations/orcasound_hydrophones_for_orcast.json), MaST Center is `47.349, -122.325` (Tacoma); Port Townsend and Bush Point are in Puget Sound, not the archipelago.
- Pod identity is invented. The data carries `pod_size` only; backend `inferPod` in [`backend.service.ts`](../../orcast-angular/src/app/services/backend.service.ts) defaults to J-Pod, yet the UI shows Resident J/K/L / Transient / Offshore filters in [`historical-sightings.component.ts`](../../orcast-angular/src/app/components/historical-sightings/historical-sightings.component.ts).

## 1. Region bounding box

Archipelago bound used to frame and filter every layer:

- lat 48.40 to 48.70
- lng -123.25 to -122.75

(Approximate San Juan / Orcas / Lopez / Shaw envelope; refine against a coastline reference during build.) Any point outside the bound is excluded from map layers. The map `fitBounds` to this on load.

## 2. In-water validation and snap

Goal: no orca marker on land; no hotspot centroid on terrain.

- **Approach (chosen):** point-in-polygon test against a static water/land mask for the archipelago (a small GeoJSON of San Juan land polygons shipped with the app). A point in water passes; a point on land is snapped to the nearest water cell, or flagged and withheld if no nearby water.
- **Hotspot centers:** after clustering, clamp the centroid to water using the same mask before display.
- **Where it runs:** frontend filter/snap now (fast to ship, no backend deploy); promote into the backend pipeline later (in `scoring.py` and the sighting normalizers) so the API itself is clean.
- **Alternatives considered:** Google Elevation API (elevation <= 0 as water) is unreliable near shore and adds quota cost; a simple bbox alone does not stop on-land points. The static polygon mask is the pragmatic pilot choice.
- **Contribute pin:** when a user drops a pin, snap to nearest water so user submissions are clean at the source.

## 3. Feed region filter

- Show only hydrophone/camera feeds whose coordinates fall inside the bounding box.
- Out-of-region feeds (MaST Center, Port Townsend, Bush Point, Point Robinson, etc.) are hidden from the San Juan map. They may be listed elsewhere as "other Salish Sea stations" but never plotted on the archipelago framing.
- The in-region subset (e.g. North San Juan Channel, Orcasound Lab, Andrews Bay) is what powers the feeds layer and the sighting-to-feed connectors.

## 4. Pod identity honesty

The data does not support pod identity, so the UI must stop claiming it.

- **Remove** the Pod Types filter group (Resident J/K/L, Transient, Offshore) from `/historical`.
- **Remove or replace** the "Top pod" statistic. Replace with top location or top behavior, which the data supports.
- **Show** "pod size N" (from `pod_size`) instead of a pod name.
- **Backend:** `inferPod` should stop defaulting to J-Pod; expose ecotype/pod only when a source actually provides it, otherwise omit. Frontend should not synthesize pod identity from coordinates or counts.
- **Behavior** stays — it is present in the data (`behavior_primary`).

## 5. Sighting-to-feed linkage

- For each in-water sighting, compute the nearest in-region feed by great-circle distance.
- On selection, draw a connector line sighting to feed and show the feed name + last-detection age.
- This is presentational context ("you could listen here"), not a claim that the feed detected that sighting.

## Net effect on each layer

| Layer | Rule applied |
|-------|--------------|
| heatmap | bounded to archipelago; water-masked cells only |
| sightings | bbox filter + water snap; behavior color; no pod identity |
| feeds | in-region subset only |
| connectors | nearest in-region feed per in-water sighting |
| hotspots | centroid clamped to water; bbox filter |
| contribute pin | snap to nearest water on drop |

## Honesty checklist (build acceptance)

- No sighting or hotspot marker renders on land.
- No feed renders outside the bounding box.
- No pod identity (J/K/L, Transient, Offshore) appears anywhere in the UI.
- "Pod size N" and behavior are the only group descriptors shown.
- Sparse data is labeled, not disguised.

# STX-R1 extent and catalog (findings)

Lane STX (station-tileset-extent, OPTIONAL). Wave STX-R, member R1. Read-only.
Reports to the STX sub-orchestrator, which reports to O0.
repo_state_verified_against: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
Method: read the served-tileset contract, the scene constant, the substrate
sidecar, the station catalog, and the raw Orcasound feed. No code edited.

## 1. The current rendered extent (one number, three places agree)

The homepage twin renders exactly one geographic footprint, and three artifacts
state it identically.

| Artifact | Source | Bounds |
|---|---|---|
| Tileset footprint | `infra/3dtwin/host/WIRING-host.md`, `full.bounds.json` | lat 48.40..48.70, lng -123.25..-122.75 |
| Scene constant `TILESET_BOUNDS` | `web/app/components/scene/SalishScene.tsx:156` | lat 48.40..48.70, lng -123.25..-122.75 |
| Substrate depth field bounds | `infra/3dtwin/science/sample_san_juan_bathymetry_cudem.json` | lat 48.40..48.70, lng -123.25..-122.75 |

This is `SAN_JUAN_BOUNDS`. In metres it is about 33.3 km north-south
(0.30 deg lat) by about 36.8 km east-west (0.50 deg lng), about 1,225 km2. The
substrate field is the SAME CUDEM `wash_bellingham` source as the render tiles
(the sidecar states "one geometry, no second pipeline"), so the extent is a
single fact shared by the rendered terrain, the depth field the rig and pick use,
and the projection frame `projectToScene` keys off.

## 2. The STATION_CATALOG and its bounds

`web/lib/scene/hydrophone/catalog.ts` carries exactly three real Orcasound nodes,
each with `withinTilesetExtent: true`, transcribed verbatim from
`src/integrations/orcasound_hydrophones_for_orcast.json`.

| id | name | lat | lng | inside extent |
|---|---|---|---|---|
| `rpi_orcasound_lab` | Orcasound Lab | 48.5583362 | -123.1735774 | yes |
| `rpi_north_sjc` | North San Juan Channel | 48.591294 | -123.058779 | yes |
| `rpi_andrews_bay` | Andrews Bay | 48.5500299 | -123.1666492 | yes |

The catalog header states the reason the list is three and not more. The backend
`GET /api/live-hydrophones` maps the full Orcasound feed through the adapter and
filters to `SAN_JUAN_BOUNDS`, so exactly three nodes survive. The catalog is the
in-extent set, by construction. `SalishScene.tsx:1877` re-applies the same bounds
filter to the beacons (`inBoundsNodes`), so a node outside the extent never gets
a beacon even if the live API returned it.

## 3. Which real nodes fall OUTSIDE the extent

The raw Orcasound feed `orcasound_hydrophones_for_orcast.json` lists nine nodes.
Six are south of the San Juan core and are dropped by the bounds filter. The two
the STX charter names are real and have verified catalog positions.

| id | name | lat | lng | why it is outside `SAN_JUAN_BOUNDS` |
|---|---|---|---|---|
| `rpi_port_townsend` | Port Townsend | 48.135743 | -122.760614 | lat 0.264 deg below the 48.40 floor (lng is inside) |
| `rpi_bush_point` | Bush Point | 48.0336664 | -122.6040035 | lat 0.366 deg below the floor AND lng 0.146 deg east of the -122.75 edge |
| `rpi_mast_center` | MaST Center | 47.34922 | -122.32512 | far south Puget Sound, well outside |
| `rpi_point_robinson` | Point Robinson | 47.388383 | -122.37267 | far south Puget Sound |
| `rpi_sunset_bay` | Beach Camp at Sunset Bay | 47.864973 | -122.333936 | central Puget Sound |
| `das_possession_bar` | DAS - Possession Bar | 47.88472 | -122.47023 | central Puget Sound (DAS experiment) |

The STX charter scope is Port Townsend and Bush Point. The other four are far
south, in Bigg's-dominated central and south Puget Sound, and are not credible
candidates for this twin even with a wider extent. So the real "nodes the user
cannot reach today but plausibly could" set is exactly two, both in Admiralty
Inlet, both about 45 to 55 km south-east of the San Juan core.

## 4. Honesty position (catalog can back both nodes)

Both Port Townsend and Bush Point carry real positions, slugs, names, and
live-listen links in the raw feed, so the honesty lock ("no station shown without
a real catalog position") is satisfiable for them. The constraint is NOT a
missing catalog entry. The constraint is that a station can only be placed where
the twin has terrain and a substrate sample to seat it on. `stationSeabedPose`
(`placement.ts`) projects with `projectToScene(lat, lng, TILESET_BOUNDS, ...)`
and reads depth from the substrate field, and the beacon raycast `surfaceYAt`
intersects the loaded tile geometry. Outside the baked footprint there is no
tile surface to raycast and no substrate sample, so a node placed there would
fall back to a flat modeled depth and a `Y = 0` beacon floating on the water
plane, not seated on real seabed.

## 5. Cross-reference: PT/BP are a known, gated region-expansion

`port_townsend` and `bush_point` already appear in the DCLDE / OrcaHello modeling
work as a deliberate, operator-gated modeling-region expansion, not a free add.
`.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB1_port_townsend_bush_point.md`
measured 25 net-new region presence-days from the two nodes, with the
decision-critical caveat that 0 of them are summer, and recommends a two-box
region gate (`ADMIRALTY_INLET_BOUNDS = lat 48.00..48.20, lng -122.85..-122.55`)
that keeps `SAN_JUAN_BOUNDS` untouched. That region gate (operator decision D1)
is NOT approved, and the PT/BP acoustic ingest is NOT run. So the served data
backing for the two nodes is, today, the station metadata only.

## 6. R1 conclusions for the decision

- The rendered extent is one shared fact across tileset, substrate, and the scene
  projection frame, all `48.40..48.70 / -123.25..-122.75`.
- The catalog is three nodes precisely because the backend filters to that
  extent. The set is correct, not a bug.
- Exactly two real, charter-named nodes fall outside, both in Admiralty Inlet,
  both about 45 to 55 km south-east of the core: Port Townsend
  (`48.135743, -122.760614`, fails latitude only) and Bush Point
  (`48.0336664, -122.6040035`, fails latitude and longitude).
- Showing them honestly needs real terrain and a substrate sample under each, so
  a widen is a tileset re-bake AND a substrate re-bake, not a catalog edit (see
  R2 and R3).
- The two nodes are already treated elsewhere as a gated region-expansion whose
  served data is not yet ingested, which lowers the marginal value of rendering
  them now (see R4).

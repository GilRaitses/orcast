# orcast UI copy guide

Plain language for user-facing strings. Read before editing Angular templates or field-campaign scripts.

Brand spelling: **orcast** (lowercase) in all user-facing copy.

## Canonical project description (locked, short)

Use for event submissions, landing tagline, booth cards, index title, and any surface that needs one or two sentences.

> orcast is a pilot study on forecast durability for orca sighting probabilities on the San Juan islands (San Juan, Orcas, Lopez, and Shaw). It supports maps and planning tools by integrating sighting catalogs, hydrophone and crowd sound tags.

## Medium description (~500 characters)

Use for event forms with a paragraph field, partner page executive summary, README intro.

> orcast is a pilot study on forecast durability for orca sighting probabilities on the San Juan islands (San Juan, Orcas, Lopez, and Shaw). Backend decision infrastructure integrates sighting catalogs (OBIS, iNaturalist, OrcaHello), NOAA tides and conditions, Orcasound hydrophone stations, and crowd sound tags. Maps and planning tools sit on top for people watching from the shore or going out kayaking. Forecasting runs in the backend; the app is the field and social layer. Not for commercial whale-watching boats.

## Long description (~750 characters)

Use for grant summaries, architecture one-pagers, technical event submissions.

> orcast is a pilot study on forecast durability for orca sighting probabilities on the San Juan islands (San Juan, Orcas, Lopez, and Shaw). Decision infrastructure ingests and cross-validates sighting catalogs, hydrophone station metadata, NOAA environmental conditions, OrcaHello acoustic reports, optional iNaturalist observer records, and crowd tags on hydrophone audio. ML ops produce probability surfaces for the archipelago. A community layer on top supports shared shore and kayak sightings, citizen science tagging, maps, and optional trip planning. External open sighting log platforms connect in rather than merge. Built for personal observation on San Juan, Orcas, Lopez, and Shaw. Not for commercial whale-watching fleets.

## Banned words (user-facing)

Do not use unless quoting an API field (e.g. `model_version`):

`fusion`, `transparent`, `honest scope`, `API Truth`, `research prototype`, `multi-agent platform`, `deterministic fusion`, `physics-informed`, `PINN`, `ML predictions` (as a product name)

## Rules

1. Say what the page does first.
2. No fake accuracy, precision, recall, or latency numbers.
3. Controls must change the API request or remove them.
4. One short disclaimer for demo pages; do not repeat "not live / not ML" in every heading.
5. No dev setup text on production pages (no `contactFormUrl`, env vars, internal doc paths).
6. No negation-led marketing ("rather than," "instead of" as the main pitch).

## Approved phrases

| Surface | Copy |
|---------|------|
| Site title | orcast · San Juan islands pilot |
| Landing tagline | (use canonical short description) |
| Reports CTA | Try probability report |
| Score grid title | Probability map |
| Score grid lead | Map of sighting probability for a region you choose. Same scoring as the report page. |
| Recent sightings | Sightings from our database on a map |
| Demo badge (live) | Live API |
| Demo badge (historical) | Historical data |
| Demo badge (scripted) | Demo only |
| Demo disclaimer | The chat-style map demos are scripted. The report page and CSV export call the live API on AWS. |
| Partners lead | (use medium description) |
| Ethics note | For people watching from the shore or going out kayaking. Not for commercial whale-watching boats. |

### Phase 5 field tools

| Surface | Copy |
|---------|------|
| Trip planner title | Plan a trip |
| Trip planner lead | Pick an island and see where orcas have been showing up. Based on recent sightings, same scoring as the report page. |
| Shore form title | Add a sighting |
| Shore form moderation note | Community sightings are reviewed before they appear on the map. We also keep a copy on this device. |
| Shore form success | Submitted for review |
| Shore form offline fallback | Saved on this device — we'll sync it when you're back online. |
| Crowd-tag placeholder | Tag this clip (coming August) |

Community submissions go to a review queue and are moderated before they appear on the map. The shore form posts to the community endpoint and falls back to on-device storage when offline.

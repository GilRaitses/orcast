# WILDLIFE dispatch prompts (self-contained subagent prompts)

Each prompt is self-contained per the wave methodology. The orchestrator owns synthesis and
verification. Subagents research (web + repo) and write only their one named report file in
`.cca/catalogue/O0/20260627_wildlife-sources/`. No ingest, no store writes, no commits.

Common requirements for every lane:
- Use the Agent Output Template in `docs/data-procurement/PROCUREMENT_CHARTER.md` (the YAML
  block) for each source, and add a `literature_grounding` block per source: a named citation
  (author, year, venue) and the one-line ecological mechanism it supports. Verify each citation
  before quoting it; if you cannot verify, mark it `unverified` and say so. Do not invent refs.
- Mark sources already wired in the repo (grep `src/aws_backend/sources/`) as `already_wired: true`.
- Label each source by its model role and never mix an effort covariate with an ecological one.
- Read `WILDLIFE_SOURCES_CHARTER.md` and `docs/methodology/FORECAST_KERNELS.md` section 6 first.

## WL-PREY (Chinook and salmonid prey -> k_salmon)

> Research, do not ingest. Write only `.cca/catalogue/O0/20260627_wildlife-sources/WL-PREY.md`.
> Survey the data sources for a real Chinook (and where relevant other salmonid) prey index for
> the SRKW forecast `k_salmon` term: run-timing and abundance, ideally stock-specific (Fraser,
> Columbia, Puget Sound). Cover at least: DFO Albion Chinook test fishery, Pacific Salmon
> Commission, Fraser River panel, Columbia Basin Research DART (Bonneville), WDFW escapement,
> PFMC Chinook abundance indices, Fish Passage Center, and the genetic-stock-ID diet work
> (Hanson et al.) that tells you WHICH stocks matter. For each source use the procurement
> template + literature_grounding (e.g. Ford et al. 2010 survival-vs-Chinook; Hanson et al. diet).
> Note the lag-structure question (prey timing to local presence). Exit: >=6 sources, each with
> availability, access path, license, fields, time/space coverage, k_salmon relevance, and a
> verified citation. Flag which directly replace the current climatology placeholder in
> `src/aws_backend/sources/salmon.py`.

## WL-SRKW (occurrence, photo-ID, census, demographics -> validation + s_space)

> Research, do not ingest. Write only `.cca/catalogue/O0/20260627_wildlife-sources/WL-SRKW.md`.
> Survey SRKW occurrence and individual/demographic data sources usable as held-out validation
> and for `s_space`, NOT for temporal-kernel estimation (they are effort-confounded). Cover at
> least: Center for Whale Research annual census, Orca Network sightings, The Whale Museum,
> Happywhale, Acartia/Salish Sea community feeds, OBIS-SEAMAP, GBIF, BC Cetacean Sightings
> Network, and DFO/NOAA line-transect or survey datasets. For each use the procurement template +
> literature_grounding (Olson et al. 2018 for the effort-bias rationale; Thornton et al. 2022 for
> distribution/habitat). State the effort-bias caveat per source and the confirmed-sighting
> definition (cross_validation verified/likely). Exit: >=6 sources with availability, access,
> license, coverage, role = validation/s_space only, and verified citations.

## WL-ACOUSTIC (passive acoustic networks -> presence spike train + log E)

> Research, do not ingest. Write only `.cca/catalogue/O0/20260627_wildlife-sources/WL-ACOUSTIC.md`.
> Survey passive acoustic monitoring networks beyond OrcaHello that could add effort-stable
> detection spike trains and, critically, MULTI-STATION coverage (the current fit is single
> station, which is the binding constraint). Cover at least: Orcasound, Ocean Networks Canada
> (ONC) hydrophones, NOAA SanctSound, JASCO, SMRU Consulting, Beam Reach / Lime Kiln, and DFO
> passive acoustic programs. For each, capture station coordinates, detection/label availability,
> per-station effort/uptime availability (needed for `log E`), and the confidence-score field
> availability (needed for detector ROC like M-L0). Ground in the acoustic-as-effort-stable
> rationale (`docs/methodology/CALIBRATION_STUDIES.md`). Exit: >=6 sources/networks with
> station/effort/label availability and verified citations; emphasize what unlocks multi-station
> Level 2.

## WL-PREYBASE (forage fish, pinnipeds, seabirds, productivity -> labeled prey-base covariate)

> Research, do not ingest. Write only `.cca/catalogue/O0/20260627_wildlife-sources/WL-PREYBASE.md`.
> Survey ecosystem and prey-base wildlife sources that contextualize Chinook availability or act
> as competitor/indicator terms: Pacific herring spawn surveys (WDFW, DFO), eulachon, Pacific
> sand lance, harbor seal and Steller/California sea lion abundance (Chinook competitors/
> predators), seabird colony and at-sea surveys, and ocean productivity (Chl-a, upwelling).
> For each use the procurement template + literature_grounding (e.g. Chasco et al. 2017 on
> pinniped predation reducing Chinook available to SRKW; forage-fish to Chinook trophic links).
> Label each source's role honestly: prey-base covariate, competitor, or indicator, never the
> temporal-kernel heat. Exit: >=6 sources with availability, access, coverage, trophic mechanism,
> and verified citations.

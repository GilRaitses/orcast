# STEP_LOG, WILDLIFE wildlife-source research waveset

All times America/New_York.

## 2026-06-27

- Chartered the WILDLIFE waveset (`WILDLIFE_SOURCES_CHARTER.md`, `wave_shape.yml`,
  `DISPATCH_PROMPTS.md`) to research the wildlife data sources worth aggregating for the SRKW
  forecast, grounded in the ecology literature. Discovery only; reuses the procurement output
  template in `docs/data-procurement/PROCUREMENT_CHARTER.md`.
- Dispatched four parallel read-only research subagents, each writing only its lane report:
  - WL-PREY (`WL-PREY.md`): 8 Chinook/salmonid prey-index sources for `k_salmon`. Albion (Fraser),
    PSC Fraser Panel, and DART (Columbia) are the daily run-timing feeds that replace the
    `salmon.py` climatology placeholder; Albion and DART are wired but on unvalidated parsers.
  - WL-SRKW (`WL-SRKW.md`): 10 SRKW occurrence/photo-ID/census sources, validation + `s_space`
    only (effort-confounded, Olson 2018). CWR census, The Whale Museum Orca Master, Happywhale,
    OBIS-SEAMAP/GBIF, DFO/NOAA line-transect (effort-known).
  - WL-ACOUSTIC (`WL-ACOUSTIC.md`): 8 PAM networks. Highest-value unlock: multi-station coverage.
    DFO OPP-MEQ moorings (~11 stations, new), OrcaHello across all Orcasound nodes (cheapest,
    already wired), ONC (provisioned), JASCO ULS effort anchor.
  - WL-PREYBASE (`WL-PREYBASE.md`): 8 prey-base/competitor/indicator sources. Ocean productivity
    (chl-a/upwelling), pinniped competitors (NOAA SARs, Chasco 2017), herring (DFO/WDFW), all
    labeled slow covariates with multi-year lags, never the temporal-kernel heat.
- Synthesized `WILDLIFE_SOURCES_REGISTER.md`: ranked by gate impact (multi-station acoustic >
  real Chinook index > held-out visual validation) with a P0/P1/P2 acquisition order. Subagents
  verified citations before quoting and flagged the few they could not (Hatch 2024, approximate
  Orcasound coords).

## Open / next

- The register feeds follow-on procurement/ingest waves (not chartered here): fit OrcaHello on all
  in-region nodes; validate the Albion/DART parsers; request DFO OPP-MEQ + ONC + CWR + Whale Museum.
- Nothing ingested or promoted; this waveset is documentation only.

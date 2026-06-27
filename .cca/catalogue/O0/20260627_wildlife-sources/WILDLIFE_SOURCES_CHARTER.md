# WILDLIFE, wildlife-source research waveset charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orcast-lane orchestrator
Home: `.cca/catalogue/O0/20260627_wildlife-sources/`
Family id: WILDLIFE

Charters a wave of parallel read-only research subagents to survey the wildlife data
sources worth aggregating for the SRKW encounter forecast, each grounded in the ecology
literature. This is a discovery waveset: it produces a literature-grounded source register,
not new ingest. It extends, and does not duplicate, the existing integrity-grade procurement
work in `docs/data-procurement/` (PROCUREMENT_CHARTER.md, SOURCE_DECISIONS.md), going deep on
the biological layers specifically.

## Why now

The L2 follow-up showed the binding constraint is the single-station, sparse-count regime, not
the covariate list: bringing `k_tide` into the joint fit via the harmonic model lifted phase
coverage 0.42 to 1.00 but held-out skill stayed negative (`docs/methodology/CALIBRATION_STUDIES.md`,
`modeling/studies/reports/level2_joint_temporal.json`). The M-L3 salmon lag scan is stuck on a
climatology placeholder. The model needs real wildlife covariates and validation, especially a
real Chinook prey index and multi-station presence, before any kernel can earn confidence. This
waveset maps which wildlife sources to aggregate and why, so the next ingest waves are targeted.

## Model context (what the sources feed)

`log lambda(x,t) = b0 + s_space(x) + k_tide + k_diel + k_lunar + k_season + k_salmon + log E(x,t)`

Wildlife sources map to specific terms and roles, never mixed:

- `k_salmon` (prey covariate): Chinook run-timing and abundance. The strongest non-tidal driver
  in the literature.
- presence spike train and `log E`: acoustic detection networks at fixed hydrophones (effort
  stable), the estimation substrate for the temporal kernels.
- external validation and `s_space`: SRKW visual occurrence, photo-ID, and demographic records
  (effort-confounded, so validation and habitat only, never the temporal-kernel heat).
- prey-base and ecosystem context: forage fish, pinnipeds, seabirds, productivity, as covariates
  on the Chinook prey base or as labeled competitor/indicator terms.

## Locked honesty constraints

- Effort-bias design holds: acoustic-first temporal estimation; visual sightings are validation
  and `s_space` only. Label every source by its model role; do not mix an effort covariate with an
  ecological covariate.
- Acoustic presence is not visual encounter; keep the layers distinct.
- A climatology fallback is not a validated ecological covariate (this is why M-L3 stays withheld).
- Literature grounding is required and must be honest: every source justification cites a named
  study with author, year, and venue, and the mechanism it supports. Verify citations before
  quoting; do not invent references (the project honesty constraint applies to references too).
- Research only. No ingest, no writes into any sighting or timeseries store, no commits by
  subagents. Each subagent writes only its one named report file in this home.

## Literature anchors (of record and to verify)

In `references.bib` already: Olson et al. 2018 (Salish Sea SRKW sightings, effort bias);
Thornton et al. 2022 CSAS (SRKW summer distribution and habitat use). Recommended and to verify
before quoting (`ORCHESTRATOR_NOTES.md` section 5): Ford et al. 2010 (killer whale survival vs
Chinook abundance); Hanson et al. 2010 and later (SRKW diet, genetic stock ID of prey); Chasco
et al. 2017 (pinniped predation on Chinook); Hilborn et al. and PFMC Chinook abundance work.
Each subagent verifies the citations it uses.

## Lanes (parallel read-only research subagents)

Each lane returns sources in the existing procurement output template
(`docs/data-procurement/PROCUREMENT_CHARTER.md`, the Agent Output Template YAML), plus a
`literature_grounding` block per source (citations + mechanism). See `wave_shape.yml` and
`DISPATCH_PROMPTS.md`.

| Lane | Scope | Model role | Output file |
|------|-------|------------|-------------|
| WL-PREY | Chinook and salmonid prey: run-timing, abundance, stock-specific indices | `k_salmon` | `WL-PREY.md` |
| WL-SRKW | SRKW occurrence, photo-ID, census, demographic records | validation + `s_space` | `WL-SRKW.md` |
| WL-ACOUSTIC | Passive acoustic detection networks beyond OrcaHello | presence spike train + `log E` | `WL-ACOUSTIC.md` |
| WL-PREYBASE | Forage fish, pinnipeds, seabirds, productivity (prey base, competitors, indicators) | prey-base covariate, labeled | `WL-PREYBASE.md` |

## Synthesis (orchestrator owns)

After the lanes return, the orchestrator merges the four reports into
`WILDLIFE_SOURCES_REGISTER.md`: a single ranked register keyed to the model term and integrity
condition, with availability, license, access path, the literature grounding, and a recommended
acquisition order (P0/P1/P2) that targets the actual gate blockers (real Chinook index;
multi-station acoustic coverage; held-out visual validation).

## Exit bars

- Each lane: at least 6 distinct sources in the template, each with availability, access path,
  model role, and a verified literature citation with mechanism; already-wired sources noted as
  such (grep `src/aws_backend/sources/`).
- Synthesis: a register that ranks sources by gate impact and names the next ingest targets,
  cross-linked to `docs/data-procurement/` and the MLM frontier (M-L0/M-L2/M-L3).

## Out of scope

- Ingest, adapters, account creation, scraping. Those are follow-on procurement/ingest waves.
- Environmental-only sources already covered in `docs/data-procurement/` (NOAA tides/currents,
  NDBC, bathymetry, shoreline) except where a wildlife source depends on them.
- Any confidence promotion.

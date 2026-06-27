# WILDLIFE sources register (synthesis)

Date: 2026-06-27 (America/New_York). Lane: O0. Synthesis of the four research lanes
(`WL-PREY.md`, `WL-SRKW.md`, `WL-ACOUSTIC.md`, `WL-PREYBASE.md`) into one ranked register keyed
to the model term and integrity condition, with a recommended acquisition order that targets the
actual gate blockers. Research only: nothing here is ingested or promoted.

Model: `log lambda(x,t) = b0 + s_space(x) + k_tide + k_diel + k_lunar + k_season + k_salmon + log E(x,t)`.

## What the gate state says we need

From the L2 follow-up (`modeling/studies/reports/level2_joint_temporal.json`): the harmonic
`k_tide` now enters the joint fit (phase coverage 0.42 to 1.00) but held-out skill is still
negative (mean deviance skill -0.047) and time-rescaling fails, so confidence stays 0%. The
binding constraint is the single-station, sparse-count regime, not the covariate list (see
`ORCHESTRATOR_NOTES.md` section 4). M-L3 stays withheld because `k_salmon` runs on a climatology
placeholder. So the three highest-impact aggregation targets, in order, are:

1. Multi-station acoustic coverage (the L2 substrate the fit is starving for).
2. A real Chinook prey index (replaces the climatology placeholder, unblocks M-L3).
3. Held-out visual validation and an effort-corrected `s_space` (lets Level 3/4 be scored).

## Tier 0: unblock the current gates (P0)

| Source | Lane | Model role | Why it moves a gate | Availability | Already wired |
|--------|------|-----------|---------------------|--------------|---------------|
| OrcaHello across all Orcasound nodes | WL-ACOUSTIC | spike train + log E | Cheapest multi-station unlock: the feed already serves several in-region nodes; the fit uses only `haro_strait`. Fitting all nodes is the fastest path to the Level 1 cross-station and Level 2 multi-station requirement. | public_api | yes (feed), no (multi-node fit) |
| DFO Ocean Protection Plan / MEQ moorings | WL-ACOUSTIC | spike train + log E | ~11 continuous SRKW-sited moorings in critical habitat since 2018 with validated killer-whale detections: the single biggest new array. | research_request | no |
| Ocean Networks Canada (ONC) hydrophones | WL-ACOUSTIC | spike train + log E | BC nodes add fixed stations north of the current fit via Oceans 3.0 / ERDDAP; token already provisioned. | account/api (provisioned) | partial |
| DFO Albion Chinook test fishery (Fraser, via PSC) | WL-PREY | k_salmon | Daily Fraser run-timing CPUE, the most diet-relevant within-season prey signal (SRKW summer Chinook ~80 to 90% Fraser-origin). Directly replaces the Fraser leg of the `salmon.py` placeholder. | public_download | wired but unvalidated parser |
| Columbia Basin Research DART (Bonneville) | WL-PREY | k_salmon | Daily Columbia Chinook passage via a scriptable query; most relevant to outer-coast/winter SRKW occurrence. Replaces the Columbia leg of the placeholder. | public_download | wired but broken parser |
| Center for Whale Research Orca Survey + census | WL-SRKW | validation + demographic | Strongest structured held-out validation: dated, pod/ecotype-labelled encounters since 1976 plus the authoritative census. | research_request | no |
| The Whale Museum Orca Master | WL-SRKW | validation + s_space | The Olson et al. 2018 dataset itself, the canonical effort-corrected `s_space` reference. | research_request | no |

## Tier 1: strengthen estimation and validation (P1)

| Source | Lane | Model role | Note |
|--------|------|-----------|------|
| PSC Fraser River Panel test fishing (Qualark/Mission/marine approaches) | WL-PREY | k_salmon | Corroborates/extends Albion; marine-approach sites are timed closer to SRKW interception (helps the lag question). |
| PSC CTC + PFMC SRKW Workgroup Chinook abundance indices | WL-PREY | k_salmon (level) | The annual/seasonal age-3+ abundance index the SRKW literature uses (Ford et al. 2010; Ward et al. 2009). Between-year level, not daily timing. |
| Happywhale photo-ID encounters | WL-SRKW | validation | Best individual-resolved cross-check; already exportable as a CC-BY-NC OBIS-SEAMAP DOI dataset. |
| OBIS-SEAMAP + GBIF Orcinus orca | WL-SRKW | validation + s_space | License-clear, DOI-citable occurrence backbones; partly overlap the wired OBIS source, so dedupe. |
| JASCO Boundary Pass ULS | WL-ACOUSTIC | log E anchor | Two cabled frames at >99% uptime: a near-flat effort anchor. Access-gated. |
| NOAA satellite chl-a (CoastWatch/ERDDAP) + CUTI/BEUTI upwelling | WL-PREYBASE | indicator (productivity) | Bottom-up driver of Chinook growth/survival; multi-year lag to adult Chinook. |
| NOAA Marine Mammal Stock Assessment Reports (harbor seal, sea lions) | WL-PREYBASE | competitor/predator | Pinniped predation reduces Chinook available to SRKW (Chasco et al. 2017). Annual, negative covariate on the prey base. |
| DFO Strait of Georgia + WDFW Puget Sound herring spawn | WL-PREYBASE | prey-base covariate | Forage base for juvenile Chinook (Duffy et al. 2010); lagged bottom-up term, not a within-season SRKW driver. |

## Tier 2: context, QA, indicators (P2)

WDFW SCoRE/SaSI escapement and Fish Passage Center (WL-PREY: Puget stock context + DART QA);
Acartia, BCCSN/WhaleReport, Orca Network, salishsea.io DwC archive, DFO/NOAA line-transect
surveys (WL-SRKW: more validation, line-transect is the one effort-known visual source);
NOAA SanctSound, OOI, Lime Kiln/LKWA, SMRU (WL-ACOUSTIC: outer-range and cross-check stations);
DFO/Olesiuk pinnipeds, rhinoceros auklet diet, eulachon, sand lance (WL-PREYBASE: indicators,
sand lance has no directed survey and is `not_found`).

## Literature grounding (anchors used across lanes; verify before quoting in any artifact)

- Olson et al. 2018, Endangered Species Research 37:105-118 (verified): Salish Sea SRKW sightings
  are opportunistic, effort-confounded; justifies the validation/`s_space`-only role for visual data.
- Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037 (verified): effort-corrected SRKW occurrence
  surface; the `s_space` reference.
- Ford et al. 2010 (Biology Letters) and Ward et al. 2009: SRKW survival/fecundity tracks Chinook
  abundance; justifies `k_salmon` as the strongest non-tidal driver.
- Hanson et al. 2010/2021 (genetic stock ID of SRKW diet): Fraser-heavy in summer, Columbia-heavy
  in winter; sets the stock weighting for the `k_salmon` index.
- Chasco et al. 2017: pinniped predation removes Chinook before SRKW; justifies the competitor term.
- Duffy et al. 2010: herring/forage fish feed juvenile Chinook; justifies the lagged prey-base term.
- Mellinger et al. 2007; Barlow & Taylor 2005 (verified in WL-ACOUSTIC): continuous PAM is
  effort-stable relative to visual survey; justifies the acoustic-first estimation.

Unverified flags carried from the lanes (do not quote until checked): Hatch 2024 and approximate
Orcasound node coordinates (WL-ACOUSTIC). Each lane file marks its own unverified items.

## Recommended acquisition order (targets the gate blockers, not source count)

1. Fit OrcaHello on all in-region Orcasound nodes (no new procurement; unblocks the Level 1
   cross-station and Level 2 multi-station requirement directly). Pair with the M-L0 confidence
   cache already built.
2. Validate the Albion and DART parsers in `src/aws_backend/sources/salmon.py` (both wired, both
   currently fall through to climatology). A real daily Chinook index is what M-L3 needs.
3. Request DFO OPP-MEQ mooring detections and ONC node access for genuinely new fixed stations.
4. Request CWR and The Whale Museum exports for held-out visual validation and `s_space`.
5. Add the prey-base covariates (productivity, pinniped competitor, herring) as labeled slow
   regressors once the prey index and multi-station presence are in.

## Cross-links

Procurement charter and decisions: `docs/data-procurement/PROCUREMENT_CHARTER.md`,
`docs/data-procurement/SOURCE_DECISIONS.md`. MLM frontier: `.cca/catalogue/O0/20260627_mlops/`.
Methodology: `docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/CALIBRATION_STUDIES.md`.
Lane detail: `WL-PREY.md`, `WL-SRKW.md`, `WL-ACOUSTIC.md`, `WL-PREYBASE.md` in this home.

# OS2 findings: open-archive net-new summer (JJA) SRKW presence-day screen

Agent: OS2 background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc is the ONLY
file written (plus one STEP_LOG line). READ-ONLY research plus reads of web, repo, and `/tmp` scratch;
no repo-store write, no convergence-file edit (`modeling/**`, `src/aws_backend/**`), no served/S3 write,
no fetch-that-writes-to-store, no ingest, no deploy, no promotion, no commit, no `git add`. Effective
confidence stays 0.0; this RECOMMENDS and SPECs only. It EXTENDS `research/signal_modeling/S1_node_sources.md`.

Hydration read in full first: `WAVESET_CHARTER.md` (section 2 OS2 row), `OS_DISPATCH.md` (OS2 source
pointers + rails), `research/signal_modeling/S1_node_sources.md` (the served universe + the W6
"0 net-new" lesson), `graduation/TB1_port_townsend_bush_point.md` (Admiralty Inlet: 0 JJA), and
`integrate-promote-launch-handoff/TB4_PRESENCE_DAY_COUNT.md` (Boundary Pass / Strait of Georgia already
screened: 6 JJA-2016 days, 0 from AMAR Boundary Pass).

## 0. The lever, the net-new test, and the honest bound on every count

The binding L3 lever (DE3 / TB1 drift-guard) is net-new SUMMER (JJA) SRKW PRESENCE-DAYS beyond the four
served nodes, judged against the summer-conditioned served gate toward +0.144. The decisive test, from
the W6 lesson (`S1` section 0.1): a source adds value only if it is ABSENT from the served universe and
the already-screened sets, not a re-shelving of cache rows the model already has. Two standing rails
bound every count here:

1. Effort is NOT-MEASURED for any new node (the OS1 denominator gap). Presence-days are MEASURED, but
   without a per-(station, day) `log E` (uptime/duty plus the OS1 detection-range term), the rate is
   biased (B.2), so NO CV-skill credit is claimed in this lane. The presence-day count is the deliverable;
   the skill is gated on the effort frame.
2. These are encounter-selected annotation corpora, so a presence-day is a true positive but the
   non-presence days are not verified absence; the absence/effort side needs the duty cycle (same caveat
   TB4 carried).

## 1. The served universe and the already-screened baseline (what "net-new" is judged against)

- Served four nodes (San Juan core, OrcaHello classifier): `haro_strait` (48.516, -123.152, co-located
  with Lime Kiln), `orcasound_lab` (48.558, -123.174), `andrews_bay` (48.550, -123.167),
  `north_san_juan_channel` (48.591, -123.059). All inside `SAN_JUAN_BOUNDS` (lat 48.40-48.70,
  lng -123.25 to -122.75).
- Already screened by prior lanes (do not recount): TB4 measured Strait of Georgia ULS = 6 JJA-2016
  SRKW-certain days and AMAR Boundary Pass = 0 JJA; TB1 measured Port Townsend + Bush Point (Admiralty
  Inlet) = 0 JJA (all their net-new days are Oct-Mar).

So OS2 screens the OPEN archives for JJA SRKW presence-days at locations and detectors NOT in that set.

## 2. NCEI / DCLDE-2027 killer-whale corpus (MEASURED screen, the master open source)

Source: the published collated ECHO/DCLDE killer-whale annotation corpus (Hildebrand et al. 2025,
*Sci Data* 12:1137; DOI artifact `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/Annotations.csv`,
207,574 rows, CC-BY-4.0). Reachability/provenance: this is the SAME artifact TB4 downloaded once to
`/tmp/orcast_tb4/Annotations.csv` (50.5 MB, outside the repo store); it is still present and was re-used
read-only here (no re-fetch, no store write). Schema per TB4:
`Soundfile, Dataset, ..., UTC, ..., KW, KW_certain, Ecotype, Provider, ...`; SRKW flag `Ecotype=="SRKW"`,
site key `Dataset`, presence-day = distinct `UTC` calendar date.

Screen method (MEASURED): per `Dataset`, count SRKW rows, distinct SRKW presence-days, and the JJA
(Jun/Jul/Aug) subset, both all and `KW_certain==1`. Cross-check against TB4: the screen reproduces
StraitofGeorgia = 6 JJA-2016 days (exact same dates) and BoundaryPass = 0, confirming the parse.

Per-`Dataset` JJA SRKW presence-days (MEASURED; 32 Dataset keys, about 23 named locations; only the
datasets with any JJA SRKW day shown; "cert" = `KW_certain==1`):

| Dataset | provider | JJA SRKW days | cert | years | span | net-new class |
|---|---|---:|---:|---|---|---|
| **Tekteksen** | SIMRES | **11** | 11 | 2022 | 2022-06-24 .. 2022-10-03 | NEW location (BC, Boundary Pass/Saturna), indep operator+detector |
| StraitofGeorgia | JASCO/ONC | 6 | 6 | 2016 | 2015-09 .. 2018-03 | already screened (TB4) |
| CarmanahPt | DFO_WDLP | 4 | 4 | 2022 | 2022-03 .. 2022-06 | NEW location (W Juan de Fuca entrance) |
| HaroStraitSouth | JASCO_VFPA | 4 | 4 | 2017 | 2017-07 .. 2017-10 | Haro Strait corridor, indep detector+epoch |
| LimeKiln | SMRUConsulting | 4 | 4 | 2019 | 2016-11 .. 2020-09 | co-located with `haro_strait`, indep detector+epoch |
| HaroStraitNorth | JASCO_VFPA | 3 | 3 | 2017 | 2017-07 .. 2017-10 | subset of HaroStraitSouth days (same deployment) |
| Cpe_Elz | SIO | 2 | 2 | 2011 | 2011-05 .. 2012-01 | NEW location (Cape Elizabeth, WA outer coast) |
| WVanIsl | DFO_CRP | 1 | 1 | 2011 | 2011-05 .. 2012-05 | NEW location (W Vancouver Island) |
| orcasound_lab | OrcaSound | 1 | 1 | 2019 | 2017-09 .. 2020-09 | SERVED node (duplicate location+operator) |
| BarkleyCanyon | ONC | 1 | 0 | 2013 | 2013-05 .. 2014-12 | NEW location (offshore WVI), UNCERTAIN day |

Net-new JJA SRKW presence-day tally (MEASURED), excluding the served `orcasound_lab` duplicate and the
TB4-screened StraitofGeorgia/BoundaryPass, and de-duplicating HaroStraitNorth into HaroStraitSouth (same
JASCO deployment, its 3 days are a subset of South's 4):

- New location, SRKW-certain, fully independent (operator + detector + location): Tekteksen 11 +
  CarmanahPt 4 + Cpe_Elz 2 + WVanIsl 1 = **18** certain net-new JJA days (+ BarkleyCanyon 1 uncertain).
- Haro Strait corridor, independent detector + independent epoch (location overlaps the served
  `haro_strait`/Lime Kiln position): JASCO_VFPA 2017 = 4 + SMRU LimeKiln 2019 = 4 = **8** more.
- Open-corpus net-new JJA SRKW presence-days total: about **26** (18 new-location-certain + 8
  corridor-detector-independent), or 27 counting the single uncertain Barkley day. This is roughly 4x
  TB4's 6, and the bulk is one site.

Headline (MEASURED): **Tekteksen (SIMRES, Boundary Pass off Saturna Island, 11 JJA-2022 SRKW-certain
presence-days) is the single best net-new summer source in the open corpus**, alone larger than the
entire TB4 Strait-of-Georgia summer payload (6 days), and the most recent epoch (2022). Independence is
high: SIMRES operator (not Orcasound), expert/JASCO-recognizer annotation (not OrcaHello), a new BC
location in the Boundary Pass shipping corridor, 2022 epoch (disjoint from the 2020+ served cache).
SIMRES context (MEASURED from a Transport Canada/JASCO 2020 report): killer-whale vocalizations were
validated on 36 days at Monarch Head and 42 days at East Point over Feb-Dec 2020, so the SIMRES archive
holds substantially more presence than the 2022 DCLDE subset, across multiple years since 2014/2017.

License/provenance: corpus CC-BY-4.0 (clean reuse). Per-Dataset provider is recorded in the corpus, so
sub-source attribution (SIMRES, DFO_WDLP, JASCO_VFPA, SMRU, SIO, ONC, OrcaSound) is preserved.

## 3. DORI-ONC (Hugging Face `DORI-SRKW/DORI-ONC`) (characterized; net-new JJA NOT-MEASURED)

Reachability: the HF dataset page is reachable (HTTP 200, fetched read-only). License: curated species
LABELS are CC-BY (the paper states CC-BY-4.0); the audio is under the original owners' licenses (ONC).
Size: about 1.03 TB; about 955 downloads last month; flagged "pre-release, labels subject to change".

Coverage and overlap (the decisive point for net-new): DORI-ONC is the Ocean Networks Canada subset of
the DORI curation. Its labels are produced by an amateur labeller with a Jaccard score of about 0.7
versus an expert bioacoustician, and (the page states) species and ecotype-level labels are NOT compared,
so the SRKW-ecotype reliability is weaker than the DCLDE expert annotations. ONC deployments already
appear in the DCLDE corpus (BarkleyCanyon, the ONC-served Strait of Georgia / Boundary Pass raw), so
DORI-ONC is largely a higher-volume, weaker-label re-derivation over data the section-2 corpus already
covers with expert labels. It is a roughly 1 TB audio retrieval keyed by `DORI.csv`, not a turnkey
per-day SRKW presence table.

Net-new JJA SRKW presence-days: NOT-MEASURED. Extracting them would require pulling `DORI.csv`, filtering
to ONC summer SRKW labels, and de-overlapping against the DCLDE expert annotations, against weak
(Jaccard 0.7, uncompared-ecotype) labels. Per B.3 (withhold over fake) this lane does not estimate a
number it cannot defend. GATE: an operator decision to invest in parsing `DORI.csv` plus the ONC token
for the audio, weighed against the fact that the expert-labelled DCLDE corpus already covers ONC.

## 4. The 30-year SRKW curation literature map, arXiv `2602.09295` (ESTIMATED)

Reachability: arXiv abstract + ar5iv full text reachable (fetched read-only). This is the DORI paper
(Nestor et al. 2026): from about 260,000 hours of 30-year archival data it curates 919 hours of SRKW
audio, stated to be "larger than DCLDE-2026, Ocean Networks Canada, and OrcaSound combined." It reports
HOURS, not presence-days, and labels are CC-BY-4.0. Its value for OS2 is a literature map for ESTIMATING
net-new JJA days at deployments whose raw annotations are not otherwise public.

The four per-deployment day-counts from the OS2 dispatch's literature map, and the honest JJA reading of
each (ESTIMATED; not independently re-counted here):

| deployment (literature) | reported days | epoch | net-new JJA reading (ESTIMATED) |
|---|---|---|---|
| Swiftsure Bank | 605 days | 2018-2020 | DFO site (also a PLOS/OS1 detection-range site); not in the served set; a real summer SRKW area at the JdF entrance. Genuinely net-new IF a JJA subset and effort are extractable; likely the largest single ESTIMATED summer reservoir, but day-count is all-season, JJA fraction unknown. |
| Lime Kiln | 46 days (2018) | 2018 | co-located with served `haro_strait`; detector/epoch-independent gap-fill only (matches the section-2 LimeKiln 2019 finding). Small net-new-LOCATION value. |
| northern Salish Sea | 96 winter days | 2015-2017 | WINTER (off-season). Net-new JJA approximately 0 (wrong season for the summer lever, like TB1). |
| OrcaSound public | 122 whale-days | 2018-2022 | same nodes/operator as the served OrcaHello universe; re-shelving risk (W6); net-new JJA approximately 0 beyond what is served. |

ESTIMATED conclusion: the only literature deployment that plausibly adds a material net-new SUMMER
reservoir beyond section 2 is Swiftsure Bank (DFO, JdF entrance), and even there the JJA subset and the
effort frame are NOT-MEASURED. The other three are off-season, co-located, or already served.

## 5. OrcaSound public archive (re-shelving risk; restrictive label license)

The served four nodes ARE OrcaSound nodes detected by OrcaHello; the DCLDE corpus already carries an
`orcasound_lab` Dataset (1 JJA-2019 day, section 2) and `port_townsend`/`bush_point` (TB1, 0 JJA).
Reachability: OrcaSound audio is open on the AWS Registry of Open Data (`registry.opendata.aws/orcasound/`).
License: audio open; the curated whale-day labels are CC-BY-NC-SA per the dispatch (noncommercial +
share-alike, more restrictive than CC-BY, a reuse constraint to flag). Net-new JJA SRKW presence-days
beyond the served universe: approximately 0 (same locations + same operator + same detector family); this
is the W6 re-shelving case. NO-GO as a net-new source.

## 6. Ranked GO / NO-GO (net-new JJA presence-days x independence x license-clarity)

1. **GO (conditional, region-expansion + effort gated) - Tekteksen / SIMRES Boundary Pass (Saturna).**
   MEASURED 11 JJA-2022 SRKW-certain days, the largest net-new summer payload found; highest independence
   (new BC location, SIMRES operator, expert/JASCO-recognizer detector, 2022 epoch disjoint from the
   served cache); CC-BY-4.0 via the DCLDE corpus. Out-of-box (Boundary Pass, BC), so it carries the same
   region-expansion decision as TB1/TB4, and its effort (SIMRES/JASCO duty cycle) is NOT-MEASURED. The
   broader SIMRES archive (multi-year, multi-station Monarch Head + East Point since 2014/2017) is the
   single highest-value follow-on reservoir.
2. **GO (conditional) - CarmanahPt (DFO_WDLP, W Juan de Fuca entrance).** MEASURED 4 JJA-2022
   SRKW-certain days, new location, independent operator/detector, CC-BY-4.0, recent epoch. Out-of-box;
   effort NOT-MEASURED.
3. **CONDITIONAL - Haro Strait JASCO_VFPA 2017 + Lime Kiln SMRU 2019 (corridor detector-fusion).**
   MEASURED 4 + 4 JJA days, at/near the served `haro_strait` position but via independent detectors
   (JASCO ECHO, SMRU PAMGuard) and independent epochs (2017, 2019, predating the served 2020+ OrcaHello).
   Value is detector + epoch corroboration / gap-fill at an existing location, NOT a new location (S1
   Group B classing). Lime Kiln access historically needs an SMRU/VFPA agreement; the DCLDE corpus
   already contains these annotations under CC-BY-4.0, which removes that gate for the historical subset.
4. **CONDITIONAL (ESTIMATED) - Swiftsure Bank (DFO, literature / OS1 detection-range site).** Potentially
   the largest summer reservoir (605 all-season days 2018-2020) but JJA subset and effort NOT-MEASURED;
   needs the DFO/OSF-linked annotations plus a duty cycle. Screen the JJA subset before committing.
5. **NO-GO (now) - Cpe_Elz (2 JJA-2011), WVanIsl (1 JJA-2011), BarkleyCanyon (1 uncertain JJA-2013).**
   New locations but tiny counts, old epochs, and (Barkley) uncertain ecotype; high heterogeneity for
   negligible summer payload.
6. **NO-GO (now) - DORI-ONC.** Net-new JJA NOT-MEASURED; about 1 TB; amateur labels (Jaccard 0.7,
   uncompared ecotype) over ONC data the expert DCLDE corpus already covers. Revisit only if the operator
   wants the full ONC audio and accepts the parse cost.
7. **NO-GO - OrcaSound public archive.** Same nodes/operator/detector as served (re-shelving, W6);
   net-new JJA approximately 0; label license CC-BY-NC-SA (noncommercial/share-alike).
8. **NO-GO - northern Salish Sea winter deployments.** Off-season (winter), net-new JJA approximately 0.

## 7. Region-expansion implication (operator scope decision, like TB1)

Every strong net-new summer source (Tekteksen/SIMRES, CarmanahPt, Swiftsure Bank, Cpe_Elz, WVanIsl,
BarkleyCanyon) sits OUTSIDE `SAN_JUAN_BOUNDS` (BC Gulf Islands / Boundary Pass, west Juan de Fuca, WA
outer coast, offshore Vancouver Island). Grounding any of them is not just an ingest; it is a deliberate
modeling-region expansion, the same operator decision TB1 framed for Admiralty Inlet and TB4 for Boundary
Pass. Tekteksen and CarmanahPt are in/adjacent to the SRKW summer foraging corridor (Boundary Pass and
the Juan de Fuca entrance), so they are more seasonally aligned with the summer gate than TB1's
fall-dominated Admiralty nodes. The two-box gate pattern from TB1 (keep `SAN_JUAN_BOUNDS` unchanged; add
disjoint region boxes) is the recommended blast-radius control; this is operator-gated and not applied
here.

## 8. Extends-S1 integrate note (no code edited here)

This lane extends `S1_node_sources.md` with a MEASURED open-archive screen; it adds no convergence-file
edit. When an operator chooses to ground a source, the integrate path is the established one S1/TB1
specify: extend `EXTRA_NODES` / `STATION_COORDS` (`modeling/studies/common.py`,
`src/aws_backend/ingest_multistation.py`), add the region box (`src/aws_backend/geo_region.py`,
two-box), build the per-source presence-day records keyed by station from the CC-BY DCLDE annotations
(provenance `source: "dclde_2027_killer_whales"` plus the per-Dataset provider), and, critically, attach
the per-deployment duty cycle as the `log E` effort offset (the OS1 detection-range term plus the ONC /
SIMRES uptime), without which no rate or skill is honest. The fetch + ingest + refit are separate
operator-gated steps. Promotion remains a separate B.1 supervisor decision on served data; nothing here
promotes.

## 9. DE drift note

This doc frames the deliverable strictly as net-new SUMMER SRKW PRESENCE-DAYS (per DE3 / the TB1
drift-guard: presence-days are the binding L3 lever, not a prey or noise feed), and records that the
strong sources are out-of-box and effort-NOT-MEASURED so no skill is credited. It touches no DE-flagged
prose doc (`M2_nonlinear_physics.md`, `wave_shape.yml` objectives, `ORCHESTRATOR_NOTES.md`, the wildlife
register); it extends S1, which already classes acoustic nodes as effort-stable presence drivers with
`log E`. No stale GO is superseded. If a later integrate touches a DE1/DE3-flagged register that still
reads "more nodes -> summer skill", attach the same caveat (presence-days measured; skill gated on the
effort frame).

## 10. Return summary

- Doc path: `.cca/catalogue/O0/20260627_open-science-integration/OS2_open_node_screen.md`.
- Top-ranked net-new JJA source (MEASURED): **Tekteksen (SIMRES, Boundary Pass off Saturna Island, BC) =
  11 JJA-2022 SRKW-certain presence-days**, the largest single net-new summer payload in the open corpus
  (alone bigger than TB4's 6), highest independence (new BC location, SIMRES operator, expert detector,
  2022 epoch), CC-BY-4.0.
- Open-corpus net-new JJA SRKW presence-days total (MEASURED, excluding served-duplicate and TB4-screened
  sites): about 26 (18 new-location-certain: Tekteksen 11, CarmanahPt 4, Cpe_Elz 2, WVanIsl 1; plus 8
  Haro Strait corridor detector/epoch-independent: JASCO 2017 = 4, Lime Kiln 2019 = 4). DORI-ONC net-new
  JJA NOT-MEASURED (1 TB, weak labels, overlaps DCLDE); Swiftsure Bank ESTIMATED as the largest untapped
  reservoir but JJA-NOT-MEASURED; OrcaSound and northern-Salish-Sea-winter approximately 0 net-new JJA.
- OS2 GO/NO-GO: **GO (conditional, region-expansion + effort gated) on the DCLDE-2027 open corpus as the
  net-new summer presence-day source, led by Tekteksen/SIMRES and CarmanahPt; NO-GO on any skill credit
  until the per-deployment effort/`log E` (OS1 term + ONC/SIMRES duty cycle) is measured; NO-GO on
  OrcaSound (re-shelving) and on DORI-ONC for now (NOT-MEASURED, weak labels).**
- Single highest-value next action: screen the broader SIMRES Boundary Pass archive (Monarch Head + East
  Point, multi-year since 2014/2017) for its full JJA SRKW presence-day count and duty cycle, since the
  MEASURED 2022 DCLDE subset (11 days) is the strongest open net-new summer signal and the SIMRES archive
  is far larger.
- Operator gates hit: (1) region expansion (all strong sources out of `SAN_JUAN_BOUNDS`, two-box gate
  decision per TB1); (2) effort/`log E` NOT-MEASURED per deployment (the OS1 denominator gate, plus ONC
  token / SIMRES duty cycle); (3) license nuance (DCLDE CC-BY-4.0 clean; DORI-ONC labels CC-BY but audio
  under owners; OrcaSound labels CC-BY-NC-SA noncommercial/share-alike).
- Confirmation: nothing edited in `modeling/**` or `src/aws_backend/**`, nothing fetched-to-store,
  ingested, deployed, promoted, or committed; the DCLDE corpus was re-used read-only from existing `/tmp`
  scratch (no re-fetch, no store write); web sources accessed read-only; only this one findings doc plus
  a STEP_LOG line written; effective confidence 0.0.

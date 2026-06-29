# OS2 build charter, net-new summer presence-days (LAUNCH-HELD)

Lane O0, Open-Science Integration. Date: 2026-06-27. Status: **CHARTERED, LAUNCH-HELD** pending operator
confirmation of the two gates in section 3. This charters the build that turns the MEASURED OS2 research
screen (`OS2_open_node_screen.md`) into served summer skill. It launches nothing until the operator
confirms the region-expansion and effort gates. Effective confidence 0.0; nothing here promotes.

## 1. Hypothesis

The served forecast is weakest in summer (JJA). The open DCLDE-2027 corpus (CC-BY-4.0) holds ~26 net-new
JJA SRKW-certain presence-days beyond the four served nodes and the TB1/TB4 screens, led by **Tekteksen /
SIMRES Boundary Pass (Saturna Island, BC) = 11 JJA-2022 days** (the largest single net-new summer payload
found, alone bigger than TB4's 6) and **CarmanahPt (DFO, W Juan de Fuca) = 4**. Adding these as honest
presence-days with a measured effort frame should lift the summer-conditioned held-out CV deviance-skill
toward the +0.144 promotion bar. This is the top-ranked open lever after OS1 closed.

## 2. Why OS1's NO-GO does NOT pre-empt OS2 (the banked physics earns its keep here)

OS1 failed on the SERVED cluster because those nodes are co-located and the OrcaHello detections sit well
above ambient, so per-day detectability barely moves the count and a noisy offset only added variance.
OS2's nodes are the opposite case: spatially separated, different operators/detectors, different basins,
each with its OWN ambient and propagation regime, so per-deployment detectability genuinely varies and is
required just to put a new node's counts on the same `log E` footing as the served stations. The OS1
deliverables banked at close — the VALIDATED detection-range calculator
(`data/external/osf_6ctjq/validate_detection_range.py`) and the PROVEN OrcaSound/Welch DSP pipeline — are
exactly the tools OS2's effort frame needs. OS1 was the wrong venue for the physics; OS2 is the right one.

## 3. The two LAUNCH-BLOCKING gates (operator must confirm before W1)

Both are held deliberately by prior lanes; neither is auto-startable.

1. **Region expansion outside `SAN_JUAN_BOUNDS`.** Every strong net-new source sits outside the served
   box (Boundary Pass/Gulf Islands, W Juan de Fuca). Grounding them is a deliberate modeling-region
   expansion, the same operator decision TB1 framed for Admiralty Inlet and TB4 for Boundary Pass.
   Recommended blast-radius control: the **two-box pattern** — keep `SAN_JUAN_BOUNDS` unchanged and add a
   disjoint Boundary Pass region box (`src/aws_backend/geo_region.py`). CONFIRM = operator approves adding
   the disjoint region box(es) and the specific nodes (Tekteksen first; CarmanahPt optional).
2. **Per-deployment effort / `log E` is NOT-MEASURED.** Presence-days are MEASURED; the rate is not honest
   without each new node's effort. CONFIRM = operator agrees effort is measured FIRST (W1) — SIMRES/JASCO
   duty cycle for uptime, and the banked OS1 detection-range calculator for per-node detectability — and
   that NO CV-skill credit is claimed until it lands. (The encounter-selected corpora also mean
   non-presence days are not verified absence; the effort/absence side carries the same TB4 caveat.)

License is already clean (DCLDE corpus CC-BY-4.0, per-`Dataset` provider attribution preserved), so it is
not a launch gate — only a provenance-tagging requirement.

## 4. Scope

In: (W1) measure the per-deployment effort frame for the chosen new nodes; (W2) ingest the net-new
presence-day records from the CC-BY DCLDE annotations keyed by station + provider, behind a two-box region
expansion; (W3) measure the summer-conditioned CV deviance-skill on the expanded design and return a
GO/NO-GO vs +0.144; (SYN) synthesize + recommend.

Out: served-region promotion (a separate B.1 supervisor decision on served data — never auto); DORI-ONC
(~1 TB, weak labels, overlaps DCLDE — NO-GO now); OrcaSound public re-shelving (W6 lesson, ~0 net-new JJA,
CC-BY-NC-SA); the small/old/uncertain sites (Cpe_Elz, WVanIsl, Barkley); Swiftsure Bank (ESTIMATED only —
screen its JJA subset before any commit).

## 5. Data sources (MEASURED in OS2 research; see `OS2_open_node_screen.md`)

| source | net-new JJA SRKW days | epoch | license | role |
|---|---:|---|---|---|
| Tekteksen / SIMRES Boundary Pass (Saturna) | 11 (certain) | 2022 | CC-BY-4.0 (DCLDE) | primary net-new node |
| CarmanahPt / DFO (W Juan de Fuca) | 4 (certain) | 2022 | CC-BY-4.0 | optional second node |
| Haro corridor (JASCO_VFPA 2017 + SMRU LimeKiln 2019) | 4+4 | 2017/2019 | CC-BY-4.0 | detector/epoch corroboration at served position |
| SIMRES broader archive (Monarch Head + East Point, multi-year since 2014/2017) | larger, NOT-MEASURED | 2014- | (SIMRES) | highest-value follow-on reservoir |

DCLDE artifact: `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/Annotations.csv`
(207,574 rows; the same file TB4 cached read-only to `/tmp/orcast_tb4/Annotations.csv`). SRKW =
`Ecotype=="SRKW"`, site = `Dataset`, presence-day = distinct `UTC` date; parse cross-checks TB4 exactly.

## 6. Wave shape (launches only after section-3 gates confirmed)

- **W1 — effort/detectability frame (unblocks honesty).** For each chosen new node: derive uptime/duty
  cycle (SIMRES/JASCO deployment metadata; ONC token if an ONC node is added) and per-node detectability
  via the banked OS1 calculator with that node's geoacoustic class + ambient. Output a per-(node,day)
  `log E` offset. Gate to W2 only if effort is defensible per node.
- **W2 — ingest net-new presence-days.** Behind the two-box region expansion: extend `EXTRA_NODES` /
  `STATION_COORDS` (`modeling/studies/common.py`, `src/aws_backend/ingest_multistation.py`), add the
  region box (`src/aws_backend/geo_region.py`), build presence-day records from the CC-BY DCLDE
  annotations keyed by station with `source: "dclde_2027_killer_whales"` + per-`Dataset` provider
  provenance, and attach the W1 `log E`. Local design only; no served/S3 write.
- **W3 — measure.** Summer-conditioned `block_cv` mean-deviance-skill on the expanded design vs the served
  baseline; report fold stability and a GO/NO-GO vs +0.144. No promotion.
- **SYN — synthesize.** Ranked outcome, the SIMRES-archive follow-on recommendation, consolidated gates,
  and a single next action. Promotion remains a separate operator/supervisor decision on served data.

## 7. Honesty rails (inherited)

Presence-days are the deliverable; NO CV-skill credit until W1 effort lands. Read-only research + bounded
local reruns; no served/S3 store write, no fetch-to-store, no deploy, no fit-that-writes, no promotion, no
commit / `git add -A` without an explicit operator ask. Effective confidence stays 0.0; the +0.144 bar and
`_confidence_from_gates` are untouched. Provenance/attribution per `Dataset` provider is mandatory.

## 8. Single next action

Operator confirms the two section-3 gates (region expansion via the two-box pattern + effort-measured-
first). On confirmation, dispatch W1 as a background subagent under O0 steering; until then this charter
holds and OS2 is parked-but-ready. Machine shape: `OS2_wave_shape.yml`.

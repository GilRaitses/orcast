# TB4 summer SRKW presence-day count (step 3, read-only measurement)

Orchestrator O0 (integrate / measure-on-served / promote). Date: 2026-06-27. Repo `main` at `9a00e15`.
Read-only measurement; no store write, no ingest, no convergence edit, no commit. This MEASURES the
number TB4 (`TB4_onc_boundary_pass.md` §2/§4) left as **NOT-MEASURED / ESTIMATED plausible-positive**.
Effective confidence 0.0.

## Source (read-only fetch to scratch only)

Published collated ECHO/DCLDE annotation corpus (Hildebrand et al. 2025, *Sci Data* 12:1137):
`gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/Annotations.csv` (50.5 MB,
207,574 rows, 18 providers, CC-BY-4.0). Downloaded once to `/tmp/orcast_tb4/` (outside the repo, NOT
the store). No fetch-to-write, no ingest. This is the same DOI artifact TB4 §4 specified.

Schema (as published): `Soundfile, Dataset, LowFreqHz, HighFreqHz, FileEndSec, UTC, FileBeginSec,`
`ClassSpecies, KW, KW_certain, Ecotype, Provider, AnnotationLevel, FilePath, FileOk`. Site key is
`Dataset`; SRKW flag is `Ecotype=="SRKW"`; `UTC` is ISO. Matches TB4 §4 step-2 filter exactly.

## Filter (TB4 §4 step 2-3, as specified)

`Dataset` ∈ {`StraitofGeorgia`, `BoundaryPass`}; `Ecotype=="SRKW"`; bin `UTC` -> `date()` -> set of
SRKW-present days per sub-node; per-JJA tally. Both target sites are present
(`StraitofGeorgia`=2078 rows, `BoundaryPass`=2021 rows); SRKW ecotype present (20,908 rows total).

## Measured result

| sub-node | dataset key | annotation span (measured) | SRKW presence-days total | **JJA-2016** | **JJA-2017** |
|---|---|---|---|---|---|
| Strait of Georgia ULS | `StraitofGeorgia` | 2015-09-29 -> 2018-03-30 | 17 | **6** | **0** |
| Boundary Pass AMAR | `BoundaryPass` | 2018-09-02 -> 2019-04-02 | 7 | **0** (no summer window) | **0** (no summer window) |
| **Net-new summer total** | | | | **6** | **0** |

JJA-2016 SRKW presence-days (Strait of Georgia ULS, all `KW_certain==1`):
`2016-07-30, 2016-08-09, 2016-08-17, 2016-08-21, 2016-08-30, 2016-08-31`.

Certainty: **every** SRKW row at both sites is `KW_certain==1`, so the certain-only and
certain+uncertain variants TB4 §4 step-2 asked for are **identical**; the 6 days are all SRKW-certain.

JJA-2017 zero is a TRUE corpus result, not a parse gap: the ULS station carries **253 annotation rows
in calendar-2017** (SRKW in May and Nov) but **zero annotation rows of any class in Jun/Jul/Aug 2017**.
The encounter-selected corpus has no summer-2017 SRKW encounter at this node. AMAR's window (Sep->Apr)
confirms TB4 §2's MEASURED 0 summer days for that sub-deployment.

## Verdict vs TB4's go/no-go

- TB4 §2/§7 condition #1 (**measure the JJA SRKW count**) is now **DISCHARGED**: the count is **6
  net-new summer presence-days** (all JJA-2016, all SRKW-certain, Strait of Georgia ULS), **0 in
  JJA-2017**, **0 from AMAR**. These are disjoint-epoch (2016) days vs the ~2020+ served cache, so they
  are genuinely net-new (the TB4 §5 epoch-independence claim holds).
- This clears TB4's "**NO-GO if ~0**" trigger, but only marginally: 6 days in a single summer, none in
  the second summer the window nominally covers. It is materially better than TB1 (0 summer days) yet
  far thinner than the "two full summers of continuous coverage" framing implied a richer payload.
- TB4 §7 condition #2 (**reconstruct effort honestly**) is **STILL NOT-MEASURED**: the ULS ONC-uptime
  mask and the AMAR duty cycle require an ONC Oceans 3.0 account/token (operator gate). Per B.2,
  presence-only without an effort denominator biases the rate, so **no CV-skill credit is claimed here**;
  the §4 step-7 `block_cv` score against +0.144 remains gated on the effort frame.

**Go/No-Go (grounding TB4 as the new-observation lever):** **GO (conditional), unchanged from S1 rank
3 / TB4 §7 — now with a MEASURED summer payload of 6 disjoint-epoch presence-days instead of an
estimate.** It stays the highest-independence-quality lever in the catalog, but the operator should
weigh that the measured summer signal is small (6 days, one summer) against the cost of the ONC-token
effort frame + the region-expansion memo (Boundary Pass is outside `SAN_JUAN_BOUNDS`). Recommend: do
NOT prioritize the TB4 ingest ahead of the cheap OrcaHello adds (TB1); revisit if/when the operator
wants the BC corridor and is willing to stand up the ONC uptime query.

## Rails confirmed

Read-only. No store write, no S3 write, no ingest, no convergence-file edit, no deploy, no promotion,
no commit. Single read-only corpus fetch to `/tmp` scratch (outside repo). All counts MEASURED from the
published `UTC` column; nothing fabricated. `data/models/fit_report.json` untouched. Effective
confidence 0.0.

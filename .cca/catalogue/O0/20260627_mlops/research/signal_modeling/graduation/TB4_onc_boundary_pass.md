# TB4 -- ONC / JASCO Boundary Pass (ECHO published dataset)

Agent: graduation subagent TB4 (retry). Date: 2026-06-27 (America/New_York). Repo:
`/Users/gilraitses/orcast`. This doc only; no other file edited, no fetch-to-write, no ingest,
no convergence edit, no deploy, no promotion, no commit (B.1/B.5/B.6/B.10). Effective confidence 0.0.

Authority: `GRADUATION_DISPATCH.md` (Shared context + RECALIBRATION FROM DE [BINDING] + lane TB4);
`S1_node_sources.md` rank 3 / group C; `src/aws_backend/ingest_multistation.py` (the
`acoustic_detections` record shape). The binding L3 lever (TB1, restated in DISPATCH RECALIBRATION):
**summer (JJA) PRESENCE-DAYS**, not "more prey series." This doc is judged on whether ONC/ECHO adds
*summer presence-days* the served 4-station universe lacks.

Source confirmation (light WebSearch/WebFetch, a few calls only): Hildebrand et al., *A Public Dataset
of Annotated Orcinus orca Acoustic Signals for Detection and Ecotype Classification*, Scientific Data
12(1):1137 (2025), DOI 10.1038/s41597-025-05281-5. Deployment Table 1, annotation summary Table 2,
annotation-file descriptors Table 3, and the JASCO/VFPA + JASCO/VFPA/ONC method sections were read
from the published article text. Nothing was downloaded to the store.

---

## 1. What the published dataset actually is (decides everything below)

It is an **encounter-selected annotation corpus** for ML detector/ecotype training -- **not** a
continuous effort-uniform detection timeline.

- Processing (both relevant deployments): "Files that detected marine mammal signals were selected for
  human inspection and detailed annotation effort." Encounters were first flagged by PAMlab/PAMGuard
  custom detectors, then expert analysts annotated calls in Raven Pro v1.5 following the HALLO protocol.
- Annotation grain: per-call bounding boxes (`SoundFile`, `FileBeginSec`, `FileEndSec`, `UTC`,
  `LowFreqHz`, `HighFreqHz`, `Species/Class` ∈ {KW, HW, Abiotic, UndBio}, `KW_certain`, `Ecotype` ∈
  {SRKW, SAR, NRKW, TKW, OKW, blank}). A collated `Annotations.csv` standardizes these across all 18
  providers; per-provider raw annotations carry extra call-type detail.
- Annotation completeness: pulsed calls + whistles are **strongly** annotated (all annotated); clicks,
  abiotic, and other-biological are **weakly** annotated (some missed). So a call/whistle-based
  presence frame is clean; a click-based one is not.
- Distribution: archived by NOAA NCEI (US National Centers for Environmental Information); audio +
  annotations + metadata public. Only audio files that carry annotations are included.

Consequence for us: the corpus gives a clean **presence numerator** (days with an SRKW
call/whistle annotation), but it does **not itself carry the effort denominator** (recording-on hours
on no-detection days). The denominator must be reconstructed from the **deployment window + recording
schedule** (Section 3). This is the central effort-bias discipline (B.2) for this lane.

### 1.1 The two Boundary Pass / Strait of Georgia deployments (Group C)

From Table 1 (deployment) and Table 2 (annotation counts):

| sub-node | dataset key | lat, lon | depth | recorder | annotation span (Table 1) | recording schedule | KW ann. | SRKW ann. | Biggs ann. |
|---|---|---|---|---|---|---|---|---|---|
| **Strait of Georgia ULS** | `StraitofGeorgia` | 49.04, -123.32 | 168-170 m | GeoSpectrum M8, cabled via VENUS (ONC) | 2015-09-29 -> 2018-03-30 | **continuous** streamed-to-shore (cabled) | 1886 | **1263** | 248 |
| **Boundary Pass AMAR** | `BoundaryPass` | 48.76, -123.07 | 193 m | AMAR (autonomous, bottom-mounted) | 2018-09-02 -> 2019-04-02 | autonomous; **duty cycle NOT stated in paper** | 1966 | **988** | 47 |

Both sit on the seabed adjacent to the **northbound shipping lane in Boundary Pass** -- a true SRKW
transit/foraging corridor, ~25-35 km NE of the `haro_strait` listening position (48.516, -123.152).
The ULS deployment (2.5 yr cabled) and the AMAR deployment (7 mo autonomous) are temporally disjoint
and together span 2015-09 through 2019-04.

---

## 2. Summer (JJA) coverage -- the binding L3 verdict (READ THIS FIRST)

The binding lever is **net-new summer presence-days**. TB1 found Port Townsend + Bush Point add **0**
summer days. ONC/ECHO is materially different here, and this is its strongest argument:

- **Boundary Pass AMAR (2018-09-02 -> 2019-04-02): covers Sept->April only. ZERO JJA months.
  -> 0 summer presence-days. MEASURED from the deployment window (no extraction needed to know this).**
- **Strait of Georgia ULS (2015-09-29 -> 2018-03-30): continuous cabled recording. The window spans
  two full summers -- JJA 2016 and JJA 2017. -> the deployment DID record in summer (coverage = YES).**

So summer **coverage** = **YES**, contributed entirely by the ULS sub-node. This is the first
candidate in the graduation waveset (vs TB1's 0) whose deployment window actually contains JJA, in a
prime SRKW summer corridor (Boundary Pass, peak Fraser Chinook season).

HONEST LIMIT -- the summer presence-day COUNT is **NOT-MEASURED**: whether SRKW calls were actually
*annotated* on JJA-2016 / JJA-2017 days requires parsing the `UTC` column of `Annotations.csv`
(station `StraitofGeorgia`, KW indicator true, `Ecotype == SRKW`) and binning by date. This doc runs
no fetch-to-write, so the per-month/per-day distribution of the 1263 SRKW ULS annotations is **not
established here**. It is *plausible-positive* (SRKW heavily use Boundary Pass in summer; the station
recorded continuously through both summers), but the number must be **MEASURED, not fabricated**,
before any summer-day credit is claimed.

**Summer-coverage verdict:** coverage = YES (ULS, JJA 2016+2017 recorded continuously); net-new summer
presence-day count = **ESTIMATED plausible-positive, NOT-MEASURED** (gated on the Section 4 extraction).
AMAR contributes 0 summer days (measured). This is the honest analogue of TB1's finding: TB1's nodes
had no summer window at all; TB4's ULS node has a real summer window but an unmeasured summer-day count.

---

## 3. Effort / `log E` model (duty cycle + the corpus-bias caveat)

Acoustic detections are effort-stable temporal drivers with a `log E` offset; a bottom-mounted
hydrophone is a fixed position, not a whale fix (B.2). Two distinct effort regimes:

**ULS (`StraitofGeorgia`) -- continuous, cabled.** Streamed to shore via VENUS, so recording is
effectively continuous on up-days. Effort model: `log E = log(recording_hours_on per day)` with
`recording_hours_on ~= 24` on up-days, `0` on gap-days. Up/down day mask is **NOT in the corpus**;
recover it from **ONC Oceans 3.0** (deviceCategory `Hydrophone`, the VENUS/Barkley-Slope device,
data-availability / gap metadata) for the 2015-09 -> 2018-03 window. Until then the continuous-24h
assumption per day-in-window is a defensible **ESTIMATED** offset, refined by the ONC gap mask.

**AMAR (`BoundaryPass`) -- autonomous, duty-cycled.** Bottom-mounted autonomous AMARs are typically
duty-cycled (record N min / sleep M min), but **the Boundary Pass AMAR duty cycle is NOT stated** in
the published paper text read here -> **NOT-MEASURED**. It must come from the JASCO/ONC deployment
metadata (or the ONC Oceans 3.0 device record). Effort model:
`log E = log(duty_fraction * 24h)` per up-day, `duty_fraction` from that metadata. Because the AMAR
window has **0 summer days**, this sub-node is low-priority for the binding lever; ingest it
presence-only with a **flagged NOT-MEASURED effort**, or defer it, rather than guessing the duty cycle.

**Corpus-bias frame (applies to both).** The corpus lists only files with detections, so:
- Presence-day (numerator): a day with >=1 SRKW call/whistle annotation = SRKW-present day. Clean
  (calls/whistles are strongly annotated).
- Absence/effort frame (denominator): a day **inside the deployment window** with the station
  recording but **no SRKW annotation** = effort-on, no-SRKW-detected day. This is valid precisely
  because annotation ran over the whole continuous stream (encounters flagged across the deployment),
  so non-annotation within the window is a genuine no-detection -- modulo the click-only weak-annotation
  caveat (we use the call/whistle frame, so this is bounded). Days **outside** the deployment window
  are not absence; they are no-effort and must not enter the model.

Net: effort is **reconstructable** (deployment window x ONC uptime mask) for ULS as `log E`; for AMAR
it is **NOT-MEASURED** pending the duty cycle. No effort number is fabricated here.

---

## 4. Presence-day extraction plan (specification only -- NOT executed)

Goal: per-day SRKW-present events mapped to `acoustic_detections` with `station: "boundary_pass"`
(ULS and AMAR can share the corridor station key, or split `boundary_pass_uls` / `boundary_pass_amar`
if the operator wants per-deployment effort kept separate -- recommended, because their effort regimes
differ and their year-epochs are disjoint).

1. **Acquire (operator-gated):** download the collated `Annotations.csv` (+ per-provider JASCO/VFPA
   and JASCO/VFPA/ONC annotation files for call-type detail) from the NOAA NCEI archive for this DOI.
   Single read-only file fetch; no store write.
2. **Filter to corridor + SRKW calls:**
   - `Dataset/location` ∈ {`StraitofGeorgia`, `BoundaryPass`};
   - KW indicator true AND `Species/Class == KW`;
   - `Ecotype == "SRKW"` (drop SAR/NRKW/TKW/OKW/blank for the SRKW presence target; keep a parallel
     all-KW tally for QA);
   - prefer pulsed-call/whistle annotations (strongly annotated); exclude click-only rows from the
     presence frame.
   - Optionally require `KW_certain` true for a high-precision variant; report both certain-only and
     certain+uncertain counts (do not silently choose).
3. **Bin to presence-days:** parse `UTC` (ISO), convert to the modeling tz, `date()` -> set of
   SRKW-present days per sub-node. Record per-month and per-JJA tallies explicitly (this is the
   Section 2 NOT-MEASURED number).
4. **Build the effort frame:** deployment-window day grid x ONC Oceans 3.0 uptime mask (ULS continuous;
   AMAR duty-cycled, NOT-MEASURED). Emit effort-on/no-detection days as absence.
5. **Map to `acoustic_detections` records** mirroring `build_acoustic_records`
   (`src/aws_backend/ingest_multistation.py`): per record `t` (UTC), `station: "boundary_pass[_uls|_amar]"`,
   `latitude/longitude` (49.04,-123.32 ULS; 48.76,-123.07 AMAR), `confirmed: true` for SRKW-certain,
   `reviewed: true`, `outcome: "confirmed"`, `confidence: null` (expert annotation, no model score),
   `source: "onc_jasco_echo_2025"`, plus an `effort_hours`/`duty_fraction` field carrying the `log E`
   input. Group via `_put_grouped_by_station` (keyed by `record["station"]`), monthly `YYYY/MM.ndjson`,
   idempotency `(station, t, id)` -- same layout as the existing nodes.
6. **DRY-RUN report (no write):** per-sub-node presence-day count, JJA presence-day count, deployment
   window, effort-day count, and net-new vs the served universe. Mark every count MEASURED or
   NOT-MEASURED.

Extraction effort estimate: **LOW-MEDIUM**. Presence-day extraction from `Annotations.csv` is a single
download + a deterministic filter/group (hours, not days). The effort denominator (ONC uptime mask +
AMAR duty cycle) is the medium part and needs an ONC Oceans 3.0 account/token + a deviceCategory
`Hydrophone` data-availability query. No new detector to build (unlike the SIMRES/Raincoast streams).

---

## 5. Independence assessment (operator / detector / corridor / epoch)

| axis | ONC/ECHO Boundary Pass | served OrcaHello nodes (haro_strait + 3) | independent? |
|---|---|---|---|
| operator | JASCO + VFPA + ONC (ECHO program, VENUS) | Orcasound / AI for Orcas (OrcaHello) | **YES** -- different funder, infra, program |
| detector | PAMlab/PAMGuard encounter flag -> expert Raven Pro manual annotation (HALLO) | OrcaHello CNN binary SRKW-call classifier + crowd/expert moderation | **YES** -- different algorithm + human protocol |
| corridor | Boundary Pass NB shipping lane (48.76-49.04 N), bottom-mounted 168-193 m | San Juan core surface/shallow nodes (48.5-48.6 N) | **YES (new location)** -- but contiguous with Haro Strait |
| epoch | 2015-09 -> 2019-04 | OrcaHello cache ~2020+ | **YES (disjoint years)** -- strongest axis |

- **Strongest independence axis = temporal epoch.** The ULS/AMAR annotations (2015-2019) **predate**
  the OrcaHello cache (~2020+), so there is **zero row overlap** and **zero same-day double-count** with
  the served stations -- this is genuinely new analysis observation, unlike W6's 0-net-new re-shelving.
  Because the served model carries seasonal/diel/tide/lunar kernels (not a year term), historical JJA
  encounter onsets still feed `k_season`/`k_diel`/`k_tide`/`k_lunar` as new in-season observations.
- **Independence caveat (spatial autocorrelation).** Boundary Pass is the corridor immediately NE of
  Haro Strait; SRKW transiting Haro Strait northbound pass Boundary Pass within hours. On a same-day
  grain the *biological* presence signal is spatially autocorrelated with the San Juan core, so on
  overlapping years it would add fewer fully-independent presence-days than a distant node. The
  disjoint epoch (2015-2019 vs 2020+) **removes the same-day double-count**, which is why the epoch
  axis carries the independence claim, not the corridor axis.
- **Heterogeneity / consistency risk (per S1).** A new BC corridor node, bottom-mounted at depth, in
  an older epoch, can lift CV-skill while *worsening* cross-station kernel consistency (already failing
  0.14-0.34). Consistency is not a confidence-map input but is an L2 quality blocker; flag it on any
  graduation. Per-deployment station keys + honest `log E` mitigate but do not erase this.

**Independence verdict:** **INDEPENDENT** on operator + detector + new-location + (decisively) epoch;
the corridor is biologically autocorrelated with Haro Strait on a same-day grain, neutralized by the
disjoint year epoch. Highest *independence quality* node in S1's catalog, at higher effort -- consistent
with S1 rank 3 / "GO (conditional)".

---

## 6. Runbook (operator-gated; nothing here executes)

Preconditions: ONC Oceans 3.0 free account + API token; `.venv-modeling`; isolated scratch output dir;
fit safety env (`ORCAST_STORAGE_BACKEND=aws`, raw-payload bucket pinned, `AWS_REGION=us-west-2`,
production upload disabled via `fit_kernels._maybe_write_s3 = lambda: None` and/or `write_outputs=False`).
No `data/models/fit_report.json` or served-store write.

1. **Fetch corpus (read-only):** download `Annotations.csv` (+ JASCO/VFPA, JASCO/VFPA/ONC per-provider
   files) from NOAA NCEI for DOI 10.1038/s41597-025-05281-5 into the scratch dir. No store write.
2. **ONC uptime/duty metadata (read-only):** `onc` Python client -> discovery deviceCategory
   `Hydrophone` -> data-availability for the VENUS Strait-of-Georgia ULS (2015-09..2018-03) and the
   Boundary Pass AMAR (2018-09..2019-04); record per-day recording-on mask + AMAR duty fraction.
3. **Extract presence-days** (Section 4 steps 2-3) into a scratch parquet/ndjson; emit per-sub-node
   counts, per-JJA counts (the Section 2 NOT-MEASURED number), and certain-only vs certain+uncertain.
4. **Build effort frame** (Section 3): deployment-window grid x uptime mask; absence = effort-on,
   no-SRKW-annotation days; ULS continuous, AMAR duty-cycled (NOT-MEASURED until step 2 returns).
5. **Map -> `acoustic_detections`** records (Section 4 step 5); group via `_put_grouped_by_station`.
6. **DRY-RUN ingest probe** (mirror `ingest_multistation_acoustic(dry_run=True)`): report
   raw + post-dedupe per-station counts, presence-days, JJA-days, effort-days. **No production write.**
7. **DRY-RUN score** in scratch (`write_outputs=False`): incremental fold-stable held-out CV
   mean-deviance-skill via `crossval.py block_cv` with the new node + its `log E`, vs the +0.144 bar.
   Report per-fold + across-fold lower bound + whether summer-day additions move the skill.
8. **STOP.** Real fetch-to-write, ingest, region expansion, refit, and promotion are separate
   operator-gated steps. This lane produces the spec + this doc only.

PATCH-SPEC (for the later single-editor integrate; nothing applied here):
- `src/aws_backend/ingest_multistation.py`: add `boundary_pass_uls` (49.04,-123.32) and optionally
  `boundary_pass_amar` (48.76,-123.07) to a new `ECHO_NODES` map analogous to `EXTRA_NODES`, fed by a
  new `build_echo_records(annotations_csv, effort_mask)` that emits the Section 4 step-5 record shape
  with `source: "onc_jasco_echo_2025"` and an effort/`duty_fraction` field. Keep dry-run default.
- Region gate: Boundary Pass is **outside** `SAN_JUAN_BOUNDS` (lat>48.70, BC). Graduating it is an
  explicit **region-expansion** decision (same class as TB1's Admiralty-Inlet expansion); route it
  through the same operator region-expansion memo, do not silently widen the box.
- DE drift note: none of the docs DE flagged (`M2_nonlinear_physics.md`, `wave_shape.yml`
  objectives, `ORCHESTRATOR_NOTES.md`, wildlife register) are touched by this patch-spec.

---

## 7. Go / No-Go

**GO (conditional), after the cheap OrcaHello adds (TB1) -- consistent with S1 rank 3.**

Rationale: it is the **highest independence-quality** node available (independent operator + detector +
new BC corridor + a disjoint 2015-2019 epoch with zero overlap with the served cache) and, uniquely
among the graduation candidates, its ULS sub-deployment **recorded continuously through two summers
(JJA 2016, JJA 2017)** in a prime SRKW summer corridor -- so it is the first candidate that *can* add
net-new **summer presence-days**, the binding L3 lever that TB1's nodes could not touch (0 summer days).

Conditions (all must hold before any value is credited):
1. **Measure the summer presence-day count** from `Annotations.csv` (ULS, SRKW, JJA). It is currently
   **NOT-MEASURED / ESTIMATED plausible-positive**; no summer-day credit without the parsed number.
2. **Reconstruct effort honestly:** ULS continuous-24h x ONC uptime mask (`log E` recoverable);
   AMAR duty cycle is **NOT-MEASURED** -> ingest AMAR presence-only with flagged effort or defer it.
   AMAR adds **0** summer days regardless.
3. **Accept the spatial-autocorrelation caveat**, leaning on the disjoint epoch for independence, and
   **flag the cross-station consistency risk** on graduation.
4. **Score through `block_cv` (`write_outputs=False`)** against the +0.144 bar; do not argue from
   in-sample fit. Effective N stays the pooled ~300 encounter onsets framing.

**NO-GO** if the parsed JJA SRKW count comes back ~0 (then it degenerates to TB1's situation -- a real
window but no summer signal) or if the effort denominator cannot be reconstructed (presence-only with
unknown effort biases the rate and violates B.2).

---

## Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB4_onc_boundary_pass.md`
- **Presence-day extraction feasibility:** **FEASIBLE, LOW-MEDIUM effort.** Clean per-day SRKW presence
  numerator from the published collated `Annotations.csv` (NOAA NCEI; filter location ∈
  {StraitofGeorgia, BoundaryPass}, KW, `Ecotype==SRKW`, bin `UTC` by date). The effort denominator is
  reconstructable for the ULS (continuous, x ONC uptime mask) but the AMAR duty cycle is **NOT-MEASURED**
  (absent from the paper; needs ONC Oceans 3.0 / JASCO metadata).
- **Summer-coverage verdict:** **coverage = YES**, via the ULS sub-deployment (continuous cabled
  recording spanning JJA 2016 + JJA 2017 in the Boundary Pass corridor); the AMAR sub-deployment covers
  Sept->April only = **0 summer days (MEASURED)**. The net-new **summer presence-day COUNT is
  ESTIMATED plausible-positive but NOT-MEASURED** (requires parsing the UTC column; not fabricated).
  This is materially better than TB1 (Port Townsend + Bush Point = 0 summer days), because TB4 has a
  real summer recording window in a prime SRKW summer corridor.
- **Independence verdict:** **INDEPENDENT** -- independent operator (JASCO/VFPA/ONC vs OrcaHello),
  independent detector (PAMlab/PAMGuard + Raven Pro HALLO manual annotation vs OrcaHello CNN), new BC
  corridor location, and decisively a **disjoint 2015-2019 epoch** (zero overlap with the ~2020+ served
  cache; unlike W6's 0-net-new). Caveat: same-day spatial autocorrelation with Haro Strait, neutralized
  by the disjoint epoch; cross-station consistency risk flagged.
- **Go/No-Go:** **GO (conditional)** after the cheap OrcaHello adds (S1 rank 3), gated on measuring the
  JJA SRKW count and reconstructing effort; NO-GO if the parsed summer count is ~0 or effort is
  unrecoverable.
- **Hard rails:** no production write, no fetch-to-write, no ingest, no convergence-file edit, no
  deploy, no promotion, no commit. Light read-only WebSearch/WebFetch only (paper text). All unmeasured
  counts marked ESTIMATED/NOT-MEASURED; nothing fabricated. **Effective confidence 0.0.**

# OG-DATA — Orca vs humpback movement contrast spec

Lane: **OG-DATA**. Purpose: make the twin's orca motion **species-true** — orca, not a
humpback profile — by specifying per-species kinematic parameters the OG motion driver
can consume directly. The orca side is grounded in the **downloaded open CC-BY data**
(Tennessen et al. 2024) plus Wright et al. 2017; the humpback side is from cited DTAG
literature **and** a clearly-marked slot for the operator's own humpback whale-tagger
DTAG export.

## Honesty label
Orca motion is "**modeled, parameterized from / driven by cited open killer-whale DTAG
data**" — now grounded in the **measured** SRKW record (Tennessen et al. 2024 `oo14_264m`,
CC-BY-4.0). The humpback baseline is the **operator's own measured DTAG** (`mn09_203a`,
"lavaliers_Calf"), used as **contrast only**. The two are never merged and one species'
motion is never presented as the other. No claim is made about a named individual beyond
what a loaded file literally contains (deployments identified by code/sex/population).

---

## 1. Humpback DTAG kinematics

### 1.0 Operator humpback baseline — MEASURED (`mn09_203a`) — PRIMARY

This is the **operator's own real humpback DTAG**, computed from the per-sample H5 by
OG-PREBAKE (`dev/humpback_mn09_203a_contrast.{bin,json}`, baked from
`Visualization_Poster_Appendix/data/dive_analysis.h5`). It is the humpback contrast
column for this project. **Measured values (128 dives, 5 Hz, ~5.5 h):**

| Quantity | Operator humpback `mn09_203a` (measured) |
|---|---|
| Max depth (m) | median **20.85**, max **39.03**, min 6.81 |
| Descent rate (m/s) | median **0.47** (max 1.25) |
| Ascent rate (m/s) | median **0.45** (max 1.33) |
| Dive duration (s) | median **66.7** (max 411) |
| Bottom duration (s) | median 30.1 |
| Fluke beat (Hz) | **~0.23** (median inter-stroke 4.4 s, from Aw.3 stroke peaks) |
| Behavior mix | feeding-dominated: Exploratory dives 35%, Side rolls 22%, Noodle feeding 18%, Kick feeding 9%, Feeding loop 6% |

**This animal is a coastal feeding humpback and is markedly SHALLOWER than the generic
deep-lunge literature** (mean foraging ~98 m below): median max depth ~21 m, max ~39 m,
with slow vertical rates (~0.45–0.47 m/s) and short dives (~67 s). Its fluke beat
(~0.23 Hz) sits at the slow end and overlaps the measured orca fundamental (~0.2–0.35 Hz).
Use these operator-measured numbers as the humpback column; the literature below is
secondary context only.

### 1.1 Generic literature baseline (deep-lunge rorqual — context only)

Humpbacks are large rorquals (~12–15 m). Their signature is **deep, powerful
lunge-feeding** with a **slow, high-amplitude fluke beat** and (for krill) **little
rolling** — the opposite of orca's fast, sharp, roll-heavy maneuvering. (Context for
the deep-lunge mode; the operator's `mn09_203a` is a shallower coastal feeder — use 1.0.)

- **Dive depth.** Feeding-mode dependent. Bubble-net feeding is shallow with an
  observed **~20 m depth-interval limit** (bubble physics) [Wiley et al. 2011]. Subsurface
  lunge-feeding on fish reaches a consistent **mean foraging depth ≈ 98 ± 6 m**
  [Szabo et al. 2023, Juan de Fuca, PLOS One]. Krill/fish foraging dives commonly span
  tens to ~150 m.
- **Descent/ascent + lunge speed.** Descent **≈ 2.7 ± 0.2 m s⁻¹**; engulfment depth-rate
  **≈ 2.0 ± 0.3 m s⁻¹**; lunge approach speed **3.0–3.7 m s⁻¹**, gliding to **~1–1.5 m s⁻¹**
  after the lunge [Simon, Johnson & Madsen 2012, JEB; Szabo et al. 2023; Goldbogen et al.].
- **Descent/lunge pitch.** Steep on lunge approach: **pitch ≈ 71 ± 13°** at the lunge,
  near-horizontal at jaw opening [Szabo et al. 2023].
- **Fluke-beat rate + amplitude.** Routine/cruise **≈ 0.20–0.25 Hz**; lunge-associated
  **≈ 0.34 Hz** [Segre et al. 2021, "Scaling of oscillatory kinematics…", PMC8317509;
  Gough et al., baleen-whale swimming-performance scaling — oscillatory frequency falls
  ∝ length⁻⁰·⁵³, cruise speed ~2 m s⁻¹ roughly length-invariant]. Slow but high-amplitude
  (large flukes), powerful strokes.
- **Roll / banking.** Krill-feeding humpbacks show **consistent approaches with little
  roll excursion** (unlike blue whales' 180° roll lunges) [Cade et al. 2016, Curr. Biol.].
  Bubble-net feeding uses **turning manoeuvrability** (upward-spiral / double-loop) rather
  than inverted rolling [Wiley et al. 2011]. Fish-feeding lunges are more variable.
- **Lunge / bout structure.** **0–6 lunges per dive (mean 4 ± 1)**, inter-lunge interval
  **≈ 1.0 ± 0.6 min**, post-lunge filtration **≈ 46 s**; high feeding rates up to
  **~37 lunges h⁻¹** [Szabo et al. 2023; Simon et al. 2012].

### >>> OPERATOR HUMPBACK — PROVIDED & BAKED (`mn09_203a`) <<<
The operator's real humpback DTAG export has landed and is baked (see 1.0 above and
`infra/orca/biologging/OG-PREBAKE_NOTES.md` "Humpback contrast baseline"). Source H5:
`/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5`
(read-only, external; not copied into the repo). It validated `prebake.py` on real
per-sample animaltags data and produced the measured humpback contrast column. Its
schema matched the open orca set exactly, slotting into the same loader:

| Field | Type | Meaning | Unit |
|---|---|---|---|
| `p` | (N,1) | depth (pressure-derived) | m, +down |
| `pitch` | (N,1) | animal pitch | radians (a2pr) |
| `roll` | (N,1) | animal roll | radians |
| `head` | (N,1) | animal heading | radians (magnetic; needs declination) |
| `Aw` | (N,3) | animal-frame tri-axial accelerometer (Az = col 3 = heave) | g or m s⁻² |
| `Mw` | (N,3) | animal-frame tri-axial magnetometer | µT |
| `fs` | scalar | sample rate | Hz |
| dive/lunge table | — | lunge timestamps / dive indices (if present) | — |

Accepted containers: animaltags `.nc` (NetCDF-4/HDF5) **or** MATLAB `.mat` (as the orca
set). Once provided, replace the literature-baseline humpback rows below with the
operator-measured values and relabel provenance accordingly.

> Open fallback reference (no operator dependency): the **CC0** Dryad bubble-net humpback
> set (DOI 10.5061/dryad.m0cfxppbj) has depth + speed profiles; its license is open but its
> download is currently blocked by a bot-protection challenge (see sources catalog) — pull
> via a browser if an open humpback file is wanted before the operator export.

---

## 2. Orca (resident, fish-eating) kinematics — from the downloaded open data

Computed directly from the CC-BY Tennessen et al. 2024 `.mat` files + `foraging_data.csv`
(see `OG-DATA_orca_sources.md` for the full table), cross-checked against Wright et al. 2017.

- **Dive depth.** Mostly shallow with a deep foraging tail: per-dive **median ≈ 4 m**,
  **p90 ≈ 34 m (NRKW) / 68 m (SRKW)**, foraging dives reaching **~150–270 m**
  (measured SRKW max 155 m in one record; `foraging_data.csv` max 272 m NRKW / 198 m SRKW).
  Wright 2017: foraging dives are deeper than non-foraging and track Chinook depth.
- **Attitude.** Steep, agile: measured **\|pitch\| p95 ≈ 40–62°** (range to ±90°).
- **Roll / banking — the defining orca contrast.** **Full ±180° roll range** with very
  frequent large excursions: measured **\|roll\| p95 ≈ 133–171°**, p99 ≈ 175–178° — i.e.
  sustained near-90° and **inverted** rolls during foraging. Wright 2017 confirms orca
  "rolled their bodies to a greater extent" while foraging. The rig **must** support full
  roll, not a small-angle clamp.
- **Fluke-beat rate.** Measured dominant heave (Aw_z) fundamental **≈ 0.20–0.34 Hz** per
  record (use `dsf()` per dive for the live value; do not hard-code). Higher cadence than a
  humpback for equivalent effort given smaller body size.
- **Speed.** Cruising **≈ 2.1–2.7 m s⁻¹** [Wright et al. 2017], with faster bursts during
  prey pursuit.
- **Dive duration.** Mean **66 s (NRKW) / 98 s (SRKW)**, up to ~520 s.
- **Antarctic ecotypes (cited, depth-only, not used to drive kinematics):** Type B/C dives
  typically **7.5–50 m**, bouts to **~368 m**, max recorded **~500–767 m**, deeper by day
  [Durban & Pitman; Andrews et al. 2008] — broadens the depth envelope but has no accel.

---

## 3. Contrast headline

Orca column = **measured SRKW** (Tennessen `oo14_264m`, CC-BY-4.0); humpback column =
**operator's measured `mn09_203a`** (generic deep-lunge literature kept in parentheses
for context only).

| Axis | **Orca SRKW (measured, Tennessen oo14)** | **Operator humpback `mn09_203a` (measured)** |
|---|---|---|
| Body size | mid odontocete (~6–9 m) | large rorqual (~12–15 m) |
| Foraging depth | to **155 m** measured; shallow median, deep foraging tail | median max **20.85 m**, max **39 m** — coastal feeder (*vs ~98 m deep-lunge lit.*) |
| Descent / ascent | steep dives | **~0.47 / ~0.45 m s⁻¹** measured (*vs lit. lunge 2.0–2.7*) |
| Dive duration | longer foraging dives | median **66.7 s** measured |
| Fluke cadence | dom. **~0.2–0.35 Hz** (active dsf med ~0.18–0.27) | **~0.23 Hz** measured (*lit. 0.20 cruise / 0.34 lunge*) |
| Roll / banking | **heavy** — near-90° & inverted (\|roll\|p95 **133°**) | feeding rolls present (side-rolls 22% of time; *krill lit. = low roll*) |
| Behavior | sharp, high tortuosity in prey pursuit | feeding-dominated: exploratory dives, side rolls, noodle/kick feeding |
| Speed | cruise 2.1–2.7 m s⁻¹ [W] | (no per-sample speed; lit. cruise ~2, lunge 3.0–3.7) |

One line: **orca SRKW (measured) = deeper-reaching (to 155 m), roll-heavy (\|roll\|p95
~133°), fluke ~0.2–0.35 Hz; operator humpback `mn09_203a` (measured) = shallow coastal
feeder (median ~21 m, max ~39 m), slow fluke ~0.23 Hz, short ~67 s feeding-dominated
dives — much shallower than generic ~98 m deep-lunge literature.** Contrast only; the
orca twin is never driven by humpback motion and neither species' motion is shown as the
other.

---

## 4. Concrete parameter table for the OG motion driver

Driver-consumable defaults. Orca rows are **measured from open CC-BY data** where marked
[D] (download) or [W] Wright 2017; humpback rows are now **operator-measured** [O] from
`mn09_203a` (generic literature [L] kept only where there is no operator measurement, in
parentheses). Ranges are "typical → extreme"; the driver should prefer per-segment live
values (e.g. `dsf().fpk`, actual `p` track) over these constants and use the table only as
bounds/fallback.

| Parameter | Orca SRKW (measured) | Operator humpback `mn09_203a` (measured) | Source |
|---|---|---|---|
| `depth_typical_m` (foraging) | 5 → 60 | **7 → 21 → 39** (coastal feeder) | [D] p95 16–142 m; [O] |
| `depth_max_m` | 155 measured / 270 obs / 767 (Antarctic cited) | **39** ([L] generic deep-lunge ~98–150) | [D]; [O] |
| `depth_median_m` (max-depth) | ~4 | **~20.85** | [D]; [O] |
| `descent_rate_mps` | 1.5 → 2.5 | **~0.47** (max 1.25) ([L] lunge 2.0–2.7) | [W]; [O] |
| `ascent_rate_mps` | 1.5 → 2.5 | **~0.45** (max 1.33) | [W]; [O] |
| `fluke_hz_cruise` | ~0.2–0.35 (active dsf med ~0.18–0.27) | **~0.23** | [D] dsf Aw_z; [O] stroke peaks |
| `fluke_hz_burst` | up to ~0.4 | (~0.34 lunge, [L]) | [D] band; [L] |
| `dive_duration_s` | longer foraging dives | **median 66.7** (max 411) | [D]/[W]; [O] |
| `cruise_speed_mps` | 2.1 → 2.7 | (no per-sample speed; [L] ~2.0, lunge 3.0–3.7) | [W]; [L] |
| `roll_envelope_deg` (p95) | **133** → 180 (inc. inverted) | side-rolls present (22% of time); ([L] krill low roll) | [D] \|roll\|p95; [O] |
| `pitch_envelope_deg` (p95) | **62** → 90 | (up to 71 lunge, [L]) | [D]; [L] |
| `bout_structure` | many short dives; deeper foraging dives | feeding-dominated (exploratory dives 35%, side rolls 22%, noodle/kick feeding) | [D]/[W]; [O] |

Labels: **[O] = operator-measured `mn09_203a`** (the humpback contrast column); [D]/[W] =
measured/derived open orca; [L] = generic literature kept only as context. The operator
humpback is a **shallow coastal feeder**, not the generic ~98 m deep-lunge profile.

Driver guidance:
- **Roll is the strongest species discriminator.** Keep the orca roll envelope wide and
  active (frequent ±90°/inverted during foraging); keep the humpback roll low and use
  heading-change turning instead — otherwise the orca reads as a humpback.
- **Fluke:** orca slightly faster + lower amplitude; humpback slower + higher amplitude.
  Both bands overlap near 0.2–0.35 Hz, so amplitude/roll, not frequency alone, carry the
  species feel.
- Always prefer the **loaded stream** (depth track, Aw_z phase) to these constants; use the
  table for the labeled procedural fallback only.

---

## 5. Citations + licenses
- **Operator humpback `mn09_203a`** ("lavaliers_Calf", *Megaptera novaeangliae*) —
  operator's own **measured** DTAG; baked by OG-PREBAKE to
  `infra/orca/biologging/dev/humpback_mn09_203a_contrast.{bin,json}` (see
  `OG-PREBAKE_NOTES.md`). The humpback contrast column. Contrast only; never drives the
  orca twin.
- **Tennessen et al. 2024**, Zenodo 10.5281/zenodo.13308835 — **CC-BY-4.0** (downloaded; orca).
- **Wright et al. 2017**, Movement Ecology 5:3, 10.1186/s40462-017-0094-0 — **CC-BY-4.0** (text).
- **Simon, Johnson & Madsen 2012**, J. Exp. Biol., 10.1242/jeb.071092 — humpback lunge kinematics.
- **Segre et al. 2021**, "Scaling of oscillatory kinematics and Froude efficiency in baleen
  whales", J. Exp. Biol. (PMC8317509) — humpback fluke 0.20 cruise / 0.34 lunge Hz.
- **Gough et al.**, "Scaling of swimming performance in baleen whales", J. Exp. Biol.
  (pure.au.dk 195213336) — oscillatory-frequency vs length, cruise ~2 m s⁻¹.
- **Cade et al. 2016**, "Kinematic Diversity in Rorqual Whale Feeding Mechanisms",
  Curr. Biol. — humpback (krill) low roll vs blue-whale 180° rolls.
- **Szabo et al. 2023**, PLOS One 10.1371/journal.pone.0282651 — humpback foraging depth
  98 m, descent 2.7 m s⁻¹, lunge 3.7 m s⁻¹, pitch 71°, 0–6 lunges/dive.
- **Wiley et al. 2011**, Behaviour — humpback bubble-net (~20 m limit, manoeuvrability).
- **Bubble-net humpback**, Dryad 10.5061/dryad.m0cfxppbj — **CC0-1.0** (open; WAF-blocked here).
- **Durban & Pitman 2012**, Biol. Lett. 10.1098/rsbl.2011.0875; **Andrews et al. 2008**,
  Polar Biol. 10.1007/s00300-008-0487-z — Antarctic Type B/C dive depths (cited, depth-only).

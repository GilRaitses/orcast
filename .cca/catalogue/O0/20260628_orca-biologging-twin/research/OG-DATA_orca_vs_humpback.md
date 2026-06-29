# OG-DATA — Orca vs humpback movement contrast spec

Lane: **OG-DATA**. Purpose: make the twin's orca motion **species-true** — orca, not a
humpback profile — by specifying per-species kinematic parameters the OG motion driver
can consume directly. The orca side is grounded in the **downloaded open CC-BY data**
(Tennessen et al. 2024) plus Wright et al. 2017; the humpback side is from cited DTAG
literature **and** a clearly-marked slot for the operator's own humpback whale-tagger
DTAG export.

## Honesty label
Orca motion is "**modeled, parameterized from cited open killer-whale DTAG data**." The
humpback baseline is "**from cited humpback DTAG literature**" until the operator's export
lands, at which point it becomes "**parameterized from the operator's humpback DTAG**".
No claim is made about a named individual beyond what a loaded file literally contains.

---

## 1. Humpback DTAG kinematics (literature baseline)

Humpbacks are large rorquals (~12–15 m). Their signature is **deep, powerful
lunge-feeding** with a **slow, high-amplitude fluke beat** and (for krill) **little
rolling** — the opposite of orca's fast, sharp, roll-heavy maneuvering.

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

### >>> OPERATOR SLOT — humpback whale-tagger DTAG export (NOT YET PROVIDED) <<<
The operator will supply a real humpback DTAG export from their separate whale-tagger
project. **Expected drop path:** `infra/orca/biologging/data/operator_humpback_dtag/`
(create on arrival, with sibling `LICENSE`/`PROVENANCE`). **Expected schema** — same
animaltags/tagtools shape as the open orca set, so it slots into the same loader:

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

| Axis | **Orca (resident)** | **Humpback** |
|---|---|---|
| Body size | mid odontocete (~6–9 m) | large rorqual (~12–15 m) |
| Typical foraging depth | shallow median (~4 m), foraging tail to ~150 m | lunge dives ~98 m; bubble-net ≤~20 m |
| Fluke cadence | **faster** (~0.2–0.35 Hz dom.) | **slower, more powerful** (0.2–0.25 cruise, 0.34 lunge) |
| Roll / banking | **heavy** — near-90° & inverted rolls (\|roll\|p95 133–171°) | **low for krill** (little roll); turning, not rolling |
| Maneuvering | sharp, high tortuosity in prey pursuit | discrete lunge bouts; bubble-net spiral |
| Speed | cruise 2.1–2.7 m s⁻¹, bursts higher | cruise ~2 m s⁻¹, lunge 3.0–3.7 m s⁻¹ |
| Bout structure | many short dives; foraging dives deeper/longer | 0–6 lunges/dive, ~1 min apart, ~46 s filter |

One line: **orca = shallower-median, faster-fluking, roll-heavy, sharp maneuvering;
humpback = deeper powerful lunges, slow high-amplitude fluking, comparatively flat (low
roll), discrete lunge bouts.**

---

## 4. Concrete parameter table for the OG motion driver

Driver-consumable defaults. Orca rows are **measured from open CC-BY data** where marked
[D] (download) or [W] Wright 2017; humpback rows are **literature** [L] pending the
operator export (replace with [O] operator-measured on arrival). Ranges are
"typical → extreme"; the driver should prefer per-segment live values (e.g. `dsf().fpk`,
actual `p` track) over these constants and use the table only as bounds/fallback.

| Parameter | Orca (resident) | Humpback | Orca source |
|---|---|---|---|
| `depth_typical_m` (foraging) | 5 → 60 | 20 → 100 | [D] p95 16–142 m; [W] |
| `depth_max_m` | 150 (resident) / 270 obs / 767 (Antarctic cited) | ~150 | [D] foraging_data; cited |
| `depth_median_m` | ~4 | mode-dependent (~20 bubble-net) | [D] |
| `descent_rate_mps` | 1.5 → 2.5 | 2.0 → 2.7 | [W] speed; [L] |
| `ascent_rate_mps` | 1.5 → 2.5 | 2.0 → 2.7 | [W]; [L] |
| `fluke_hz_cruise` | 0.25 (0.20–0.35) | 0.22 (0.20–0.25) | [D] FFT Aw_z; [L] |
| `fluke_hz_burst` | up to ~0.5 | 0.34 (lunge) | [D] band; [L] |
| `cruise_speed_mps` | 2.1 → 2.7 | ~2.0 (lunge 3.0–3.7) | [W]; [L] |
| `roll_envelope_deg` (p95) | 130 → 180 (inc. inverted) | 15 → 45 (krill; higher fish) | [D] \|roll\|p95; [L] Cade 2016 |
| `pitch_envelope_deg` (p95) | 40 → 90 | up to 71 (lunge) | [D]; [L] |
| `bout_structure` | many short dives; deeper foraging dives | 0–6 lunges/dive, ~1 min apart, ~46 s filter | [D]/[W]; [L] |

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

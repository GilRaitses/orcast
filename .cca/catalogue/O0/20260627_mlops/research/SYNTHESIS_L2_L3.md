# Synthesis: ranked L2/L3 action plan (Agent RF)

Date: 2026-06-27 (America/New_York). Lane: O0 ML-ops L2/L3 push research waveset.
Charter: `RESEARCH_CHARTER.md` (section E, RF; Q7). Dispatch: `RESEARCH_DISPATCH.md`.
Locked decisions: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
Consolidates: `research/L3_response_variable.md` (RA), `research/L3_conditioning.md` (RB),
`research/L3_diel_temperature.md` (RC), `research/L2_burstiness_timing.md` (RD),
`research/L2_data_volume.md` (RE).

Synthesis/writing only: no fits, no convergence-file edits, no confidence promotion, nothing
committed. This is a decision aid for the operator, not a gate pass. Effective confidence stays 0%.

## Headline

The research wave changed the blocker map more than it changed any gate. Three honest results stand
out:

1. **L3 is not limited by its response variable** (RA) — it is limited by **pooling off-season
   presence against a summer run** (RB). Conditioning on the SRKW summer window surfaces a real but
   exploratory candidate signal (Jun-Sep r=0.251, p=0.013).
2. **L2 cross-station is NOT gated on the 3-node ingest** (RE, refuting the carried-in framing). The
   ingest moves the *same cached records* into production and adds **zero new observations**. The
   binding issue is scoring **resolution + burstiness + an effectively-unreachable 24-bin target**.
3. **L2 time-rescaling has no honest event-level fix** (RD). A Hawkes intensity is the correct GOF
   and explains *why* it fails (branching ratio 0.79-0.96 = detector repeat-triggering); the honest
   path forward is a **bin-level timing gate**, which is a methodology change, not a refit.

Nothing here promotes confidence by itself. Two findings dead-end honestly (RA counts, RC
temperature/diel). Three are strong enough to graduate to an operator-gated W4 build/integrate wave.

## Ranked action plan

Payoff scale is relative within this wave. "Ceiling" states what the move can and cannot earn; no
single move promotes confidence (B.1).

### UNGATED moves (do now — no operator/deploy gate; methodology/desk work only)

| # | Move | Source | Expected payoff | Cheapest next experiment | Honest ceiling |
|---|------|--------|-----------------|--------------------------|----------------|
| U1 | **Re-score cross-station consistency at coarser bins (8-12) + min per-bin count** | RE | Highest leverage on L2. Makes diel reproducible (orcasound_lab diel split-half 0.08 @24 bins → **0.42 @12 bins** at the same 1029 detections; N* drops ~22k → ~1,750) and brings **lunar over 0.5** at current volume on both dense stations (haro_strait lunar 0.65 @12 bins, orcasound_lab 0.54 @12 bins). | Re-run the consistency scorer at 8/12 bins with a minimum per-bin count; report split-half reliability as the honest ceiling. No new data. | Cannot make **tide** reliable (goes negative at 12/8 bins — anti-structure or phase-aliasing, not a volume problem). Cannot reach the **24-bin** bar. Does not promote. |
| U2 | **Partial pooling: score consistency vs the joint fitted kernel + station random effect** | RE | Reports an upper-bound cross-station consistency that respects sparse nodes via shrinkage, instead of correlating raw per-station 24-bin marginals. | Add a station random-effect read-out to the consistency scorer; report split-half as the ceiling. | Shrinkage **mechanically inflates** correlation, so it is an upper bound, **not a pass**. Honest only when reported alongside split-half. |
| U3 | **Burst-dedup to encounter onsets before counting** (shared RD/RE) | RD, RE | Measures reliability per independent encounter, not per bursty detection (63-91% of detections within 6 min of the prior). Cleaner denominator for U1/U2 and for any L3 count test. | Reuse the W2 encounter-onset (burst-dedup) re-score read-only; recount per-onset. | Reduces effective N (makes the volume bar *harder*, not easier) — it corrects honesty, it does not add signal. Onset process is itself clustered (RD: pooled KS p~7.5e-22). |
| U4 | **Pre-registered SRKW-summer (Jun-Sep) L3 conditioning + counts confirmation** | RB (+ RA) | Turns L3 from "flat, no signal" into a real candidate: Jun-Sep r=**0.251**, p=**0.013**, z=+3.06; May-Oct r=**0.182**, p=**0.012**, z=+2.58; both at a consistent **+20 d** lag (run leads presence). | Pre-register Jun-Sep + the lag sign as the biological hypothesis; hand the summer mask to RA's counts/NB-GLM formulation; re-run on the summer subset only. | **Exploratory, not promotable.** Multiplicity (Bonferroni over ~4 windows pushes p≈0.012 → ≈0.05); rests on **36-63 summer presence-days** (mostly orcasound_lab 2020-2021); still binary; no held-out year. L3 stays WITHHELD. |
| U5 | **Hawkes self-excitation diagnostic + bin-level GOF prototype** | RD | Quantifies *why* event-level time-rescaling fails (branching ratio 0.79-0.96; pooled KS stat 0.773 → 0.134, near-zero fraction 81.6% → 0.14% under Hawkes, still p=3.3e-33). Surfaces the held-out bin-level GOF (NB PIT p=0.364 calibrated; CV deviance skill +0.078 beats climatology). | Already prototyped (RD section 2). Surface as a diagnostic read-out only; do not touch the served intensity. | The diagnostic is ungated; **changing the gate to credit it is GATED** (G1). NB PIT alone is near-automatic (free dispersion alpha=88.1) — only honest **paired** with the non-automatic CV-skill gate. |

### Operator/deploy-GATED moves (need a deploy or a recorded supervisor/promotion decision)

| # | Move | Source | Expected payoff | Cheapest next experiment | Honest ceiling |
|---|------|--------|-----------------|--------------------------|----------------|
| G1 | **Redefine the L2 timing gate to a bin-level criterion** (NB PIT calibrated AND held-out CV skill > climatology), carrying Hawkes as the event-level diagnostic | RD | The *only* change that lets L2 earn timing credit on current data, scoring GOF at the served target (per-bin presence) instead of event-level Exp(1) on detector chatter. | Wire `bin_level_verdict` into `_time_rescaling_report` and swap `tr_pass`→`timing_gate` in `_confidence_from_gates` (RD spec section 4). | A **methodology change with publication implications** (time-rescaling is named the gold-standard GOF). Must be a recorded supervisor decision (B.1), not a refit side effect. Event-level Exp(1) stays WITHHELD. |
| G2 | **3-node production `acoustic_detections` ingest (`dry_run=False`)** | RE | Correct plumbing: moves multi-station data into production and **starts forward accumulation**. | Land the ingest (Agent D's `ingest_multistation.py`). | **Necessary but NOT sufficient.** It moves the *same cached records* (orcasound_lab 1029, andrews_bay 265, nsj 34) — **zero new observations**, so post-ingest split-half reliability **equals current** and clears 0.5 for **no** kernel. It is a precondition for *future* accumulation, not a fix. |
| G3 | **Held-out-year L3 confirmation once summer volume allows** | RB | Out-of-sample test of the U4 summer signal: fit the lag on N-1 summers, test on the held-out summer. | Deferred until forward accumulation (G2 + seasons) provides more summer detections. | Blocked on volume today (36-63 summer presence-days, provenance-mixed). |

### DEAD-END (honest "no gain" / withheld — do NOT build)

| Move | Source | Why it dead-ends (measured) |
|------|--------|------------------------------|
| **Counts-based L3 test** (raw / log1p / rank / conditional / rate-proxy / NB-Poisson GLM) | RA | Every encoding fails the same circular-shift null binary fails. Best p of any formulation = **0.193** (endogenous rate proxy); count GLM is **worst at p=0.681** (observed LR 178.4 sits *below* the null mean 262.7±137.1; z=-0.62). The response variable is **not** the limiter. NB MLE was numerically degenerate. *(Caveat: this is the POOLED verdict — see conflict C1; counts should still be re-tested on the U4 summer window before final close-out.)* |
| **Temperature / SST as an animal kernel** | RC | NO-GO per B.2: SST ≈ f(day-of-year) over the Salish Sea, **collinear with `k_season`** (itself withheld/no-skill) and redundant with `k_salmon`; not separately identifiable. Coverage is excellent (CO-OPS 9449880 ~9 km, NDBC 46088 ~20-24 km, full 2020-2026) but availability was never the blocker. At most a minor, low-priority **L0 detectability** term (L0 already PASSES, ROC AUC 0.879). |
| **Diel-window conditioning for L3** | RC | Conditioning on the fitted `k_diel` active window does not move the salmon lag: full p=0.394 → active-window p=0.326, r 0.076 → 0.072 (sits on its own null mean). Time-of-day is irrelevant at the daily/seasonal salmon timescale; daily presence already integrates over the diel cycle. |

## Graduate-to-W4 candidates (operator decides)

Three findings are strong and well-specified enough to graduate to a real W4 build/integrate wave.
Graduating means "worth building/wiring," not "promoted" — none raises confidence on its own.

1. **RD — bin-level timing-gate redefinition + Hawkes diagnostic.** GRADUATE as an *operator-gated*
   build wave (G1). Concrete wiring spec exists (RD section 4: `_time_rescaling_report` adds
   `self_exciting` + `bin_count_gof` blocks; `_confidence_from_gates` swaps `tr_pass` for a
   `timing_gate` satisfied by event-level Exp(1) OR (NB PIT calibrated AND CV skill > 0)). Load-
   bearing constraint: the CV-skill pairing must not be dropped, or the gate becomes near-automatic.
   Document honestly as "event-level Exp(1) is inappropriate for a detector-chatter stream," not as
   "time-rescaling passed."

2. **RE/RB — consistency re-score at coarser bins + partial pooling + burst-dedup.** GRADUATE as an
   *ungated* methodology change to the consistency scorer (U1+U2+U3). It is the single highest-
   leverage L2 move available without new data: diel becomes reproducible and lunar clears 0.5 at
   current volume. Report split-half as the honest ceiling; flag tide as not-yet-reliable regardless
   of binning.

3. **RB — pre-registered SRKW-summer L3 conditioning with a counts confirmation and a held-out
   year.** GRADUATE as a *pre-registered confirmatory study* (U4 now; G3 when volume allows). Lock
   Jun-Sep and the +20 d lag sign *before* the confirmatory run; report the current p=0.013 as
   exploratory. L3 stays WITHHELD until a pre-registered, counts-based, ideally out-of-sample summer
   test holds.

**Honest dead-ends (do NOT graduate):** RA counts-based L3 test (no encoding beats the null pooled),
and RC temperature/SST animal kernel + diel-for-L3 conditioning. Report both as withheld/no-gain
(B.3). Temperature survives only as an optional, low-priority L0 detectability term — not a build
wave.

## Corrected L2/L3 blocker map (for the charter)

The charter (section A) and the dispatch's shared context state cross-station consistency is "data-
volume bound: the binding dependency is the operator/deploy-gated 3-node production ingest." **RE
refutes this and it must be corrected.** Updated map:

- **L2 time-rescaling — WITHHELD (modeling, ungated to prototype; gate change is operator-gated).**
  Cause is detection **burstiness/self-excitation**, confirmed: Hawkes branching ratio 0.79-0.96 =
  detector repeat-triggering on single encounters, not independent animal events. No event-level
  Exp(1) fix passes on dense data (best, single-exp Hawkes, p=3.3e-33; only the n=34 sparsest
  station "passes" at low power). **NOT data-volume.** Honest path: a bin-level GOF timing gate (NB
  PIT + CV skill), a methodology change graduating via an operator-gated build wave (G1).

- **L2 cross-station consistency — NOT simply gated on the 3-node ingest (CORRECTED).** The binding
  issue is **scoring resolution + burstiness + an effectively-unreachable 24-bin target**, not the
  ingest:
  - The 24-bin split-half bar needs **thousands to tens of thousands of detections per station**
    (diel N* ~14k-22k, tide ~6k-13k); at orcasound_lab's ~180/yr that is **decades** (~72-116 yr for
    24-bin diel). Effectively unreachable for years.
  - The 3-node ingest moves the **same cached records** into production (orcasound_lab 1029,
    andrews_bay 265, nsj 34) — **zero new observations**; projected post-ingest reliability **equals
    current** and clears 0.5 for no kernel. The ingest (G2) is correct plumbing and a precondition
    for forward accumulation, but it does **not** clear the bar.
  - Burstiness deflates the effective independent N below the raw count, so the volume requirement is
    *harder* than the raw N* suggests.
  - The reachable-now lever is **coarser bins + partial pooling + burst-dedup** (U1-U3), which alone
    makes diel reproducible and lunar clear 0.5 at current volume. **Tide stays unreliable** (negative
    split-half at 12/8 bins) regardless of data — flag as not-yet-reliable, possibly genuine
    heterogeneity or phase-aliasing.

- **L3 k_salmon — WITHHELD.** The feed is real, complete, single-source, stock-aligned Albion (all
  years 2020-2026); the limiter is neither the feed nor the response encoding:
  - **Response variable is NOT the limiter** (RA): binary, counts, log, rank, conditional, rate-
    proxy, and NB/Poisson GLM all fail the same null pooled (best p=0.193, GLM worst at 0.681).
  - **Pooling off-season presence against a summer run IS the limiter** (RB): only 18.9% of
    detections fall in Jul-Sep; presence is fall/winter-concentrated while the run peaks Jul-Aug.
  - **Conditioning sharpens it** (RB): SRKW-summer window beats the null (Jun-Sep r=0.251 p=0.013;
    May-Oct r=0.182 p=0.012) at +20 d — exploratory, not promotable.
  - **Temperature/SST and diel are dead-ends for L3** (RC): SST collinear with season, diel
    irrelevant at the salmon timescale.
  - Path: pre-registered summer conditioning + counts confirmation + held-out year + more summer
    detections via forward accumulation (G2/G3).

## Conflicts between agents — resolved honestly

- **C1. RA "counts do not help" vs RB "conditioning helps."** Not a true conflict. RA tested response
  *encodings* on the **pooled, full-year** series (where every encoding fails the null); RB
  *conditioned* the series to the **summer window** (where binary presence beats the null). They
  agree on the lesson: **the lever is conditioning, not the response encoding** (RA rec 2 explicitly
  hands off to RB; RB rec 1 hands the summer mask back to RA's counts formulation). **Resolution:**
  the dead-end verdict on counts is for the *pooled* test; the open, pre-registered confirmatory test
  is **counts on the Jun-Sep window** (U4). Do not close the counts question until that conditioned
  test is run.

- **C2. Carried-in charter framing vs RE.** The charter/dispatch say L2 cross-station is "the binding
  operator/deploy-gated 3-node ingest dependency." **RE refutes this with the decisive fact** that
  the ingest reads the same cached records the consistency study already analyzes. **Resolution:**
  adopt RE's correction (above). The ingest is correct plumbing and a forward-accumulation
  precondition, but it is **not** the binding cross-station fix; the binding issues are resolution,
  burstiness, and an unreachable 24-bin target. The charter blocker map should be updated.

- **C3. RD bin-level GOF "passes" vs the honest WITHHELD verdict.** RD resolves this internally: the
  NB PIT (p=0.364) is near-automatic under a free dispersion parameter (alpha=88.1), so it is honest
  *only* when paired with the non-automatic held-out CV-skill gate (+0.078 beats climatology), and
  event-level Exp(1) stays WITHHELD with the clustering reason. **Resolution:** no conflict if G1
  keeps the CV-skill pairing load-bearing and never asserts a clean event-level time-rescaling pass.

## Risks

- **Window-shopping on L3 (highest risk).** The U4 p=0.013 is one of ~4 windows scored; Bonferroni
  puts it at the edge (~0.05). If a future agent tunes the window to minimize p, the result is
  meaningless. Lock Jun-Sep + the +20 d lag sign by pre-registration before any confirmatory run, and
  scrutinize the lag-sign mechanism (Albion is lower-Fraser CPUE; the run-leads-presence direction is
  not obviously mechanistic) before narrating any causal story.
- **Gate-definition drift on L2 (G1).** Dropping the CV-skill pairing makes the bin-level timing gate
  near-automatic and over-credits the model. The pairing is load-bearing and must survive the build
  wave. The redefinition has publication implications and must be documented as a GOF-scope change,
  not a "time-rescaling pass."
- **Mistaking the ingest for a fix (G2).** Landing the 3-node ingest can look like progress on cross-
  station consistency; it is not. Communicate it as plumbing/forward-accumulation, or the corrected
  blocker map will silently revert.
- **Coarser-bin over-claiming (U1/U2).** Coarser bins and partial pooling raise reliability partly by
  reducing degrees of freedom and by shrinkage — report split-half as the honest ceiling and keep
  tide flagged as not-yet-reliable; do not treat the inflated numbers as a consistency pass.
- **Provenance and labeling.** Findings rest on a sparse, mixed-provenance cache (years/stations
  non-overlapping; haro_strait absent from the cached index; reviewed-outcome records mixing
  confirmed/false_positive/unknown). A confirmed-only choice lowers N further. Conclusions are
  conditional on this data; a denser, ecotype-labeled SRKW series could change the L3 picture.
- **No promotion.** Effective confidence stays 0%. No move here is a gate pass; graduation to W4 is a
  build decision the operator makes, and any confidence change remains a gate pass + recorded
  supervisor decision (B.1).

# L3 conditioning: season / per-station / SRKW summer window

Agent RB, L2/L3 push research waveset. Date 2026-06-27 (America/New_York).
Charter: `RESEARCH_CHARTER.md` (agent RB) + `RESEARCH_DISPATCH.md`. Locked decisions:
`20260627_mlops-handoff/HANDOFF_CHARTER.md` section B. Investigation-first; no convergence-file
edits; no fit, no S3/model/store write; no promotion. An honest "no gain" is valid.

Report JSON: `modeling/studies/reports/L3_conditioning.json`.

## Headline

Conditioning **does** sharpen the salmon alignment, and one principled conditioning crosses the
significance bar. The pooled binary-presence lag scan is diluted by **off-season presence**: most
SRKW acoustic presence in this cache falls in **fall/winter**, when the Albion (Fraser-summer
Chinook) run index is ~0. Restricting the correlation to the **SRKW summer window (Jun-Sep)** raises
the best-lag correlation from r=0.076 (pooled, p=0.394) to **r=0.251, p=0.013** at a consistent
**+20-day** lag (run index leads presence). The wider May-Oct window gives r=0.182, p=0.012.

This is a genuine improvement, but it is **exploratory, not promotable**: it rests on 36-63 summer
presence-days, the window choice is a researcher degree of freedom (multiplicity), and it is still
binary presence. The honest verdict is **L3 stays WITHHELD**, but conditioning has turned the L3
picture from "flat, no signal on the correct stock" into "a real candidate signal in the SRKW summer
window worth a pre-registered, counts-based confirmation." This is **not** "no gain".

## Method (read-only reuse of `salmon_lag.py`)

- Imported, never edited: `_aggregate_daily_presence`, `_build_run_index`, `_best_lag`,
  `_permutation_null`, `_pearson`, `_circular_shift`, plus `LAG_MIN/LAG_MAX/N_PERMUTATIONS/
  PERMUTATION_SEED` and `common.load_orcahello_index`. Run index = `SalmonRunAdapter` →
  **source=albion for all years 2020-2026** (real, stock-aligned Fraser-summer Chinook), matching
  the baseline.
- Response variable: **binary daily presence** (identical to the baseline; the counts reformulation
  is Agent RA's lane).
- Null: **circular shift of presence** over the full contiguous daily array, best `|lag corr|`
  statistic over lags [-30, +30], 1000 permutations, seed 20260627 — the same null family as the
  pooled baseline (so the numbers are directly comparable).
- Season restriction implemented as a **masked correlation**: off-season days are dropped from the
  correlation only; lag indexing stays on the full contiguous array (so a +20-day lag never crosses
  a season seam), and the circular-shift null is re-scored under the same mask. This drops the
  off-season zeros exactly as the charter asks while keeping the lag/null machinery faithful.
- Lag sign: `corr( run_index[i-lag], presence[i] )`. **lag = +20 ⇒ the run index 20 days earlier
  correlates with presence**, i.e. run timing leads acoustic presence by ~20 days.
- Refit safety: no `fit_kernels` import, no fit, no S3/model/store write. Ran under `.venv-modeling`.

## The data reality that explains the pooled null (the key context)

The cached OrcaHello index (1359 detections, 3 nodes; `haro_strait` is **not** in this cache) and the
Albion run are **temporally disjoint**:

- Detection presence by month (days): Jan 16, Feb 16, Mar 21, Apr 7, May 4, **Jun 8, Jul 3, Aug 5,
  Sep 20**, Oct 23, Nov 24, Dec 16 → presence is concentrated in **fall/winter**.
- Albion run index >0 by month (days): Apr 6, May 17, **Jun 74, Jul 137, Aug 153, Sep 74**, Oct 49 →
  run is a **summer** signal (peaks Jul-Aug).
- Per station × year: `orcasound_lab` 1029 (mostly 2020-2021, fall/winter), `andrews_bay` 296 (all
  2026, Feb/Mar/Jun), `north_san_juan_channel` 34 (2025-2026). A sparse, non-overlapping mosaic.

So the pooled scan correlates a mostly-fall/winter presence series against a summer run index: the
off-season days (run≈0, presence sometimes high) are pure dilution. That is exactly what conditioning
removes.

## Results

All best lags land at **+20 days** (run leads presence) except the two degenerate sparse stations.

### 1. Season restriction (drop off-season zeros)

| Conditioning | in-season days | presence days | best lag | r | null mean\|r\| | z | p | beats p<0.05 |
|---|---|---|---|---|---|---|---|---|
| baseline pooled | 2088 | 163 | +20 | 0.076 | 0.081 | -0.18 | 0.394 | no |
| run-active (run_index>0) | 510 | 28 | +20 | 0.188 | 0.138 | +1.10 | 0.150 | no |
| calendar DOY 90-310 (Apr-Nov) | 1222 | 76 | +20 | 0.158 | 0.098 | +2.01 | 0.059 | no |

Restricting to the run season **more than doubles** the correlation (0.076 → 0.16-0.19) and lifts the
effect z from negative to +1.1/+2.0, but neither crosses p<0.05. The run-active mask is the most
aggressive (only 28 in-season presence days) and the null widens accordingly (mean |r| 0.138), so its
p stays at 0.150. The calendar window is borderline (p=0.059).

### 2. Per-station (each station scored separately)

| Station | scope | days | presence | best lag | r | p | verdict |
|---|---|---|---|---|---|---|---|
| orcasound_lab | pooled | 2087 | 151 | +20 | 0.085 | 0.329 | mirrors the pool (it **is** the pool) |
| orcasound_lab | in-season | 509 | 27 | +20 | 0.194 | 0.151 | same lift as the pooled season restriction, n.s. |
| andrews_bay | pooled | 131 | 12 | +4 | 0.293 | 0.604 | not scorable (12 days, p high) |
| andrews_bay | in-season | 13 | 1 | +5 | 0.927 | 0.528 | **degenerate** (1 presence day) |
| north_san_juan_channel | pooled | 348 | 4 | 0 | -0.038 | 1.000 | not scorable (4 days) |
| north_san_juan_channel | in-season | 103 | 0 | 0 | 0.000 | 1.000 | **no in-season presence** |
| haro_strait | — | 0 | 0 | — | — | — | **absent from cached index** (production-stream-only) |

**No station shows independent alignment.** `orcasound_lab` dominates the cache and simply reproduces
the pooled/season-restricted result; the other two nodes are too sparse to score (their large raw
correlations are small-sample artifacts with p≈0.5-1.0). The per-station path is **data-volume bound**,
consistent with Agent C/RE's cross-station finding — sparse nodes cannot reproduce themselves, let
alone a salmon lag.

### 3. SRKW summer presence window (condition on the summer season)

| Window | in-season days | presence days | best lag | r | null mean\|r\| | z | p | beats p<0.05 |
|---|---|---|---|---|---|---|---|---|
| Jun-Sep (months 6-9, core) | 629 | 36 | +20 | **0.251** | 0.129 | +3.06 | **0.013** | **yes** |
| May-Oct (months 5-10, wide) | 1001 | 63 | +20 | **0.182** | 0.105 | +2.58 | **0.012** | **yes** |

Conditioning on the SRKW summer window is the only conditioning that **beats the permutation null**.
Both a tight (Jun-Sep) and a wide (May-Oct) biologically-motivated window agree: r ≈ 0.18-0.25 at the
same +20-day lag, p ≈ 0.012-0.013, effect z ≈ +2.6 to +3.1. The Jun-Sep window is biologically
pre-specifiable (the classic SRKW Salish Sea core-summer presence season), which is the strongest
form of this test.

Note the null here is, if anything, **conservative**: shifting the (fall/winter-heavy) presence over
the full array can rotate dense presence clusters into the summer slots and inflate null correlations,
yet the observed summer alignment still clears it.

## Honest caveats (why this is suggestive, not promotable)

1. **Multiplicity / researcher degrees of freedom.** I scored 4 season/SRKW windows (run-active,
   DOY 90-310, Jun-Sep, May-Oct). Two cross p<0.05. A Bonferroni correction over ~4 windows pushes
   p≈0.012 to ≈0.05 — right at the edge. The lag scan's own multiplicity (±30 lags) is already in the
   null via the best-|r| statistic, but the *window* choice is not. The Jun-Sep result is only fully
   honest if Jun-Sep is **pre-registered** as the biological window before the test.
2. **Small presence counts.** The headline rests on 36 (Jun-Sep) to 63 (May-Oct) summer presence-days,
   most from `orcasound_lab` in 2020-2021. The effect is real in this sample but thinly supported.
3. **Still binary presence.** This is the same response variable that under-performs by design (it
   discards count magnitude, saturates busy days). The counts/rate/GLM reformulation (Agent RA) is the
   natural confirmatory test and should be re-run **on the summer window** specifically.
4. **Provenance mosaic.** Years and stations do not overlap; the summer signal is effectively the
   `orcasound_lab` 2020-2021 + 2025-2026 summer days. No out-of-sample year was held out.
5. **Lag direction.** A consistent +20-day lag (Albion run leads acoustic presence) is the same across
   every conditioning, which suggests it is driven by the smooth seasonal **shape** of the run index
   meeting the summer presence sub-window, not a sharp, mechanistically-resolved 20-day delay. Treat
   the +20 d as "run leads presence by ~weeks," not a precise interval, and scrutinize the direction
   (Albion is lower-Fraser CPUE; whales intercept Fraser Chinook in the marine approach upstream of
   timing at Albion, so the sign warrants a mechanistic check before any claim).

## Ranked recommendation

Does conditioning move L3 toward a real signal, or confirm withheld? **Both, honestly:** it confirms
L3 is not promotable today, *and* it surfaces a real candidate signal that the pooled test had hidden.

1. **Confirm with COUNTS on the SRKW summer window (cheapest, highest value).** Hand the summer-window
   mask to Agent RA's counts/rate/NB-GLM formulation. If daily counts (not binary presence) on the
   Jun-Sep window beat the null at the same +20 d, the signal is much more credible. This is an
   ungated desk experiment.
2. **Pre-register the window and lag sign.** Fix Jun-Sep (or May-Oct) and the lag direction as the
   biological hypothesis *before* the confirmatory run, so the p-value is honest. Report the current
   p=0.013 as exploratory.
3. **Get more summer detections (the binding data dependency).** The summer presence sample is tiny
   and provenance-mixed. The operator/deploy-gated 3-node production `acoustic_detections` ingest plus
   accumulating summer seasons is what would let this signal be tested out-of-sample. Same dependency
   Agent RE quantifies for cross-station consistency.
4. **Hold out a year** once volume allows: fit the lag on N-1 summers, test on the held-out summer.
5. **Do not promote.** A single conditioned p<0.05 on a chosen window is not a gate pass. k_salmon
   stays WITHHELD until a pre-registered, counts-based, ideally out-of-sample summer test holds.

## Risks

- **Over-reading the p=0.013.** Multiplicity + small n means this could be a sample artifact; the
  counts test (RA) and a held-out year are the cheap insurance before anyone treats L3 as "moving".
- **Window-shopping.** If a future agent keeps tuning the window to minimize p, the result becomes
  meaningless. Lock the window.
- **Per-station dead-end.** Three of four target stations are not scorable here; `haro_strait` (the
  production stream's main node, 761 detections) is **not in the cached index** at all, so a real
  per-station test needs the production ingest, not this cache.
- **Lag-sign mechanism.** The +20 d (run-leads-presence) direction is not obviously mechanistic for
  Albion CPUE vs marine-approach presence; do not narrate a causal story on it yet.

## Reproduce

```
PYTHONPATH=. .venv-modeling/bin/python -m modeling.studies._rb_conditioning
```

(Scratch driver `modeling/studies/_rb_conditioning.py` is a standalone read-only experiment; it
imports `salmon_lag.py` helpers and writes only `reports/L3_conditioning.json`. It is not wired into
`run_studies`/`mlops-gate` and edits no convergence file. Delete it after the wave if not kept.)

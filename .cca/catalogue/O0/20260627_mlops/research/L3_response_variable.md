# L3 response variable: counts vs binary presence (Agent RA)

Date: 2026-06-27 (America/New_York). Lane: O0 ML-ops L2/L3 push research waveset.
Charter: `RESEARCH_CHARTER.md` (section E, RA). Locked decisions: `HANDOFF_CHARTER.md` B.
Owner surface: this doc + `modeling/studies/reports/L3_response_variable.json`.

## Question

The L3 lag scan (`modeling/studies/salmon_lag.py`) correlates BINARY daily presence
(1 if any detection that day) with the lagged daily Albion (Fraser-summer Chinook) run
index, pooled across detection years 2020-2026. It does not beat the permutation null
(best lag +20 d, r 0.076, p 0.394). Binary presence discards count magnitude and
saturates on busy days. **Is the response variable the limiter?** Do daily COUNTS,
counts-per-effort (rate), or a count GLM (Poisson/NB) recover a salmon signal that
binary presence throws away?

## Method (read-only reuse of the convergence machinery)

All formulations reuse `salmon_lag.py` functions imported READ-ONLY (`_aggregate_daily_presence`,
`_build_run_index`, `_best_lag`, `_lag_corr`, `_pearson`, `_permutation_null`, the lag range
`[-30, +30]`, 1000-permutation circular-shift null, seed `20260627`). Detections come from
`modeling.studies.common.load_orcahello_index()` (the same cached 3-node OrcaHello index the lag
scan uses, 1359 records); the run index from `SalmonRunAdapter().fetch_run_index(year)`, which
returns `source=albion` (real, stock-aligned Fraser-summer Chinook) for every year 2020-2026.
`salmon_lag.py` was not edited. No fit-pipeline import, no S3, no model/store write, no promotion.
The experiment ran under `.venv-modeling` (numpy 2.4.6, statsmodels 0.14.6) via a uniquely-named,
untracked scratch driver (`modeling/studies/_ra_response_scratch.py`) that imports `salmon_lag.py`
read-only and writes only the owned report JSON.

Convention (matches `_lag_corr`): a positive lag of `+L` days means the run index `L` days
*earlier* is paired with today's response (salmon run leads acoustic presence).

Data shape (the regime every formulation has to work in):

| property | value |
|---|---|
| detection span | 2020-09-28 .. 2026-06-16 (2088 days) |
| detection records | 1359 |
| days with >=1 detection | 163 (7.8%; **92.2% of days are zero**) |
| daily count mean (all days) | 0.65 |
| daily count mean (presence days) | 8.34 |
| daily count max | 101 (2026-02-17) |
| count variance / mean | **27.7** (extreme overdispersion; Poisson assumes 1.0) |
| detections in Jul-Sep (Fraser summer run) | 257 of 1359 = **18.9%** (July alone: 3 = 0.2%) |
| detections in winter Dec-Feb | 488 = 35.9% |

## Measured results

Each row: best lag, effect size at that lag, permutation p (the lag-scan circular-shift null).
"Beats null" requires p < 0.05.

| Formulation | best lag (d) | effect size | permutation p | beats null? |
|---|---:|---:|---:|:--:|
| **binary presence** (baseline, reproduced) | +20 | r = 0.076 | 0.394 | no |
| daily counts (raw) | +23 | r = 0.070 | 0.271 | no |
| daily counts, log1p | +20 | r = 0.080 | 0.290 | no |
| daily counts, rank / Spearman | -20 | r = -0.095 | 0.450 | no |
| counts conditional on presence days | +23 | r = 0.070 | 0.271 | no |
| rate per active-station proxy* | +24 | r = 0.074 | **0.193** | no |
| **count GLM** (Poisson/NB + season) | +24 | LR = 178.4 | **0.681** | no |

\* "rate per effort" cannot be computed honestly: there is no independent per-day effort series
for the cached index. W1 Agent A established that `station_uptime` covers only 2026-06-20..27
(disjoint from the 2020-2026 detection span) and `haro_strait` has no uptime node, so effort
wiring is a verified no-op. The "rate per active-station proxy" divides each presence day's count by
the number of distinct stations reporting that day. That denominator is ENDOGENOUS (derived from
the detections themselves, undefined on zero days), so it is a saturation probe, not a real
effort normalization. It is the best p of any formulation (0.193) and still does not beat the null.

### Count GLM detail

Poisson/NB regression of daily counts on the lagged run index plus a 2-harmonic annual season term
(`intercept + sin/cos x2 + run_index_{lag}`), on the fixed inner window valid for all lags
(n = 2028 days). Lag selected by max likelihood-ratio deviance drop vs the season-only model, with a
500-permutation circular-shift null on the run-index series that re-runs the whole lag scan and keeps
the best LR per shuffle (so the null accounts for the lag search).

- best lag +24 d; observed LR (deviance drop vs season-only) = **178.4**.
- deviance skill vs intercept-only = +0.090; **vs season-only = +0.024** (the salmon term's own
  contribution is tiny once season is in the model).
- Poisson run-index coefficient = +2.41, Wald p = 0.0 — **not trustworthy**: Pearson dispersion
  is ~19, so model-based SEs are ~sqrt(19)x too small. This is exactly why a nonparametric null is
  required.
- NB MLE was numerically degenerate on this 92%-zero, bursty series (Hessian inversion failed, no
  SE, alpha collapsed toward 0). It yields no usable inference.
- **Permutation null: p = 0.681.** The observed LR (178.4) is BELOW the null mean (262.7 +/- 137.1);
  effect-size z = -0.62. Circular shifts of the run index reduce deviance by MORE than the true
  alignment, on average, because an overdispersed Poisson with a flexible season term rewards
  aligning the single seasonal run bump with any of the large detection clusters. The real
  alignment is unremarkable against that null.

## Interpretation (honest)

**No response-variable encoding beats the null.** Binary, raw counts, log counts, ranks,
conditional-on-presence counts, the effort-proxy rate, and a count GLM with a season term all fail
the same circular-shift null that binary presence fails. The best p across every formulation is 0.19
(the endogenous rate proxy); the count GLM is the worst at 0.68. **The response variable is not the
limiter.** Magnitude information does not rescue a daily salmon signal that the presence indicator
discarded, because the signal is not there to recover at the daily/seasonal scale on this detection
set.

Two upstream facts explain why, and both point away from the response encoding:

1. **The detection set is off-season-dominated.** Only 18.9% of detections fall in the Jul-Sep
   Fraser summer-run window, and July (the run peak) has 3 detections (0.2%). 35.9% are in winter
   (Dec-Feb), biologically disconnected from the Fraser summer Chinook run. These cached OrcaHello
   detections are not a clean SRKW-summer-foraging series; pooling all of them against a
   summer-run index dilutes any prey coupling with a large, salmon-irrelevant baseline. Changing how
   that baseline is *encoded* (binary vs count) cannot create alignment that the *sampling* removed.
2. **Extreme burstiness/overdispersion (var/mean 27.7).** Counts arrive in within-day bursts (max
   101 in one day), so the count magnitude is dominated by encounter clustering, not by a slow
   prey-availability gradient. This is the same burstiness W1/RD diagnosed for the L2
   time-rescaling blocker; it makes count magnitude a noisier, not richer, salmon response.

This is a valid "no gain" result per B.3. It tightens the L3 story: L3 stays WITHHELD not because the
feed is wrong (it is real, complete, single-source, stock-aligned Albion for all years) and not
because binary presence is too coarse (counts/rate/GLM fail identically), but because the daily,
year-pooled coupling between this acoustic set and the Fraser summer run is absent.

## Recommendation (ranked)

1. **Do NOT wire a counts-based L3 test into `salmon_lag.py`.** It would add code and a count
   pathway for zero measured benefit (every count formulation fails the null; the GLM is worse than
   binary). Binary daily presence is an adequate, cheaper response for this question.
2. **The promising lever is conditioning, not the response encoding — hand off to RB.** The
   off-season dominance (18.9% in-window, July 0.2%) is the dominant defect. Restricting to the
   run/summer season, conditioning on the SRKW summer-presence window, and scoring per-station
   (RB's charter) are far more likely to move L3 than any response-variable change. If RB's
   *in-season* scan shows life, a count response could be re-examined *then*, on the conditioned
   subset, not on the pooled series.
3. **Keep L3 honestly WITHHELD.** No formulation earns k_salmon credit. Effective confidence stays
   0%. No promotion.

## Risks / caveats

- Single detection set: the cached 3-node OrcaHello index (1359 records). A denser, ecotype-labeled
  SRKW-only acoustic series (e.g. after RE's gated 3-node production ingest, or with resident-vs-
  transient labels) could change the picture; this result is conditional on the current data.
- The circular-shift null preserves each series' autocorrelation, which is the right null for a
  lagged alignment but is conservative against a weak true signal smeared across many lags. Even so,
  every formulation's observed statistic sits inside the bulk of its null (best z = +/-0.2 for the
  correlation forms; -0.62 for the GLM), so a missed weak signal is unlikely.
- The "rate" formulation is a saturation probe with an endogenous denominator, not a true
  effort-normalized rate; a real rate is not computable until an independent per-day per-station
  effort series exists (W1 Agent A: not available today). This does not change the conclusion (the
  proxy still fails the null).
- NB MLE degeneracy means the count GLM's significance rests entirely on the nonparametric
  permutation null (p = 0.681), which is the appropriate test under this overdispersion anyway.

## Reproduce

```
PYTHONPATH=. .venv-modeling/bin/python -m modeling.studies._ra_response_scratch
```

(The scratch driver `_ra_response_scratch.py` reproduces every number above and writes
`modeling/studies/reports/L3_response_variable.json`. It imports `salmon_lag.py` read-only, does not
import the fit pipeline, and writes no S3/model/store output. It is left untracked for
reproducibility; nothing is committed.)

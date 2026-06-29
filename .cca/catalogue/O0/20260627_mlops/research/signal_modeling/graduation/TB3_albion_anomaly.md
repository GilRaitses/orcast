# TB3 -- real Albion feed refresh + run-anomaly covariate (D1)

Agent: TB3 (Wave TB, graduation waveset). Date: 2026-06-27 (America/New_York).
Repo: `/Users/gilraitses/orcast`. Lane home (the ONLY file this agent writes):
`.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB3_albion_anomaly.md`.

Authority: `20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B (B.1 honesty/promotion,
B.2 covariate-role honesty, B.3 withhold-over-fake, B.5 bucket footgun, B.6 refit-upload-disable, B.7
local-only pipeline, B.9 EC2-for-DFO escape hatch, B.10 no commits); `GRADUATION_WAVESET_CHARTER.md`
sections 1, 3; `GRADUATION_DISPATCH.md` (RECALIBRATION FROM DE block [BINDING], Fit safety, TB3 lane);
`SYNTHESIS_signal_modeling.md` (B3, section 1); `research/signal_modeling/M3_derived_covariates.md` (D1);
`research/forward/G3_l3_grounding.md` (live 2026 Albion fetch + the L3 decision bar).

Scope: runbook + anomaly recipe + expected-skill band + go/no-go + patch-spec ONLY. No production
fetch-that-writes, no convergence-file edit, no fit that writes a served artifact, no S3/model/store
write, no deploy, no promotion, no commit. Effective confidence stays 0.0.

## 0. Drift-guard restatement (BINDING -- read before the runbook)

Per the DE recalibration and G3, this lane is **SUPPORTING ONLY**, not the L3 lever:

- The Albion Chinook feed is **already REAL and stock-aligned** (Fraser-summer Chinook via the DFO FOS
  Albion test fishery, `cpue1`), cached for every detection year 2019-2026 (`salmon.py::_load_albion_fos`,
  G3 section 0). It is not a placeholder for the run-index predictor.
- The binding L3 constraint is summer **PRESENCE-DAYS** (the acoustic response `y`), which is TB1's lever
  (Port Townsend + Bush Point + accruing summers), NOT the feed and NOT "more prey series" (G3 section 4;
  SYN section 1).
- Therefore **D1 stays WITHHELD** on the climatology placeholder, and the **L3 result stays WITHHELD**.
  Refreshing the feed and constructing the run anomaly are NECESSARY housekeeping so a future 2026 Jun-Sep
  out-of-sample test can even be RUN; they are NOT sufficient to move L3 and they promote nothing (G3
  section 1f, section 4).
- **CUTI/BEUTI upwelling is NO-GO** (out of the 31-47 N product coverage; region ~48.5 N) and is not
  introduced anywhere in this lane.

## 1. Live-feed refresh runbook (design only -- NOT run here)

This extends `WIRING-salmon-albion.md` and G3 section 1. It changes no parser: `_load_albion_fos` already
reads `data/salmon/albion_fos/fosYYYY.csv` keyed on `cpue1` and tolerates the quoted-comma effort fields.
**No production fetch-that-writes is performed by this agent.**

### 1a. Why the refresh is needed (the concrete, measured reason)
Current cache state (verified 2026-06-27): `data/salmon/albion_fos/fos2026.csv` spans **2026-05-01 ..
2026-06-26** -- it stops BEFORE the late-July/August Fraser-summer Chinook peak. A 2026 Jun-Sep
out-of-sample test today would see a truncated, near-zero summer run index and would be invalid. Back-years
2019-2025 are cached and stable; they need no refresh. (G3 section 1d.)

### 1b. Provenance (restate for the manifest; unchanged)
- Source: DFO Fishery Operations System (FOS), **Albion test fishery**, "Catch Summary by Date" report.
  Params: `stat=CPTFM`, `fsub_id=242` (subsystem), `lboSpecies=124` (CHINOOK SALMON), `lboYears=<YYYY>`,
  `cmdRunReport=Run Report`. Licence: Open Government Licence -- Canada.
- Value used: `cpue1` = standard 8-inch gillnet CPUE = the run-timing index (`catch2/cpue2` large-mesh panel
  not used).
- Reachability (B.9): host `www-ops2.pac.dfo-mpo.gc.ca` (205.193.114.62) is DNS-blocked from the dev host
  and the backend region; it IS reachable from the **aimez-services EC2 `i-04a649f91274e9fce`** (x86_64
  Ubuntu, account 198456344617, us-east-1). All fetches run there; the parsed CSV is copied back into the
  repo cache. No live in-process pull.

### 1c. Fetch recipe (run ON the EC2; a direct POST returns the report HTML -- no Selenium needed)
```
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@<aimez-ec2-host>   # i-04a649f91274e9fce (SSM fallback 198456344617/us-east-1)

YEAR=2026
curl -sS -c /tmp/fc.txt \
  "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242" -o /dev/null
curl -sS -b /tmp/fc.txt \
  -e "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242" \
  --data "lboYears=${YEAR}&lboSpecies=124&lboFsub=242&cmdRunReport=Run+Report" \
  "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptCSbD.cfm?stat=CPTFM" -o /tmp/fos.html
```

### 1d. Parse (matches `_load_albion_fos` exactly)
- Each data row is a `<tr>` whose stripped text splits into **exactly 12 whitespace tokens**; `tokens[0]` =
  day number, `tokens[1]` = 3-letter month.
- Write CSV with header
  `day,mon,year,netlen,catch1,sets1,effort1,cpue1,catch2,sets2,effort2,cpue2`, csv-quoting the comma-bearing
  effort fields (e.g. `"16,300"`), exactly like the existing `data/salmon/albion_fos/fos2026.csv`.

### 1e. Cache write + idempotency (overwrite-in-place; PREREG_* untouched)
- Write **`data/salmon/albion_fos/fos2026.csv` (overwrite-in-place)**. The FOS report is cumulative
  season-to-date, so re-fetching yields a longer table; overwrite is idempotent and safe.
- Touch ONLY the current-year cache file. Do NOT touch back-year caches (2019-2025) and do NOT touch any
  pre-registration constant: `salmon_lag.py::PREREG_SUMMER_MONTHS` (Jun-Sep), `PREREG_LAG_SIGN`
  (run-leads, +lag only), `PREREG_LAG_MIN=0`, `PREREG_LAG_MAX=30` stay **frozen exactly as committed**.
  Window/lag shopping would destroy the only thing rescuing the binary p from the Bonferroni x4 multiplicity
  (G3 section 2a, section 4 residual risk). The refresh adds DATA to a frozen hypothesis; it never edits the
  hypothesis.
- This is the modeling pipeline's local-only data tree (B.7); the cache file is not a served artifact and
  this runbook never writes `data/models/fit_report.json` or any S3/model-bucket object.

### 1f. Provenance manifest + integrity guards (per refresh)
Record one manifest line per refresh: fetch UTC timestamp, the POST params, row count, season-to-date
`max(cpue1)` and its date, and a sha256 of the CSV. Validate: row count is **monotone non-decreasing** and
the season `max(cpue1)` does **not regress** vs the prior pull (guards a partial/truncated report).

### 1g. Refresh cadence
Albion season ~April-October; summer Chinook peak ~late-July to August. The lag test needs the run index
from ~mid-May through end-September of the test year (a +17 to +20 d run-leads lag pulls run-index values
back into mid-May). Cadence: **weekly refresh of the current year Jun-Oct**; one **final post-season refresh
in November** to freeze the year; **no refresh Nov-Mar** (off-season, run index ~0). (G3 section 1e.)

### 1h. What the refresh does and does NOT buy
- DOES: make the 2026 run index complete enough to RUN a 2026 Jun-Sep OOS test. Necessary.
- Does NOT: add a single acoustic presence-day. The run index is the predictor (`x`); the binding constraint
  is the response (summer presence-days, `y`). Extending Albion alone cannot move L3 off WITHHELD. The lever
  for presence-days is TB1 (new in-region nodes + accruing summers), not this feed. (G3 section 1f, section 4.)

## 2. Run-ANOMALY construction (D1 -- break the season collinearity)

The raw Albion run index is itself seasonal, so as a covariate it is MODERATE-HIGH collinear with `k_season`
(M3 D1; SYN B3). The independent content is the **year-to-year and within-season departure** from the
seasonal climatology. Enter the run ANOMALY, not the raw run index.

### 2a. Recipe
1. **Build a day-of-year (DOY) climatology of the REAL feed.** For each DOY `d`, average the real Albion
   `cpue1` (or the within-season min-max normalized `run_index` from `salmon.py::_build_series`) across the
   stable back-years 2019-2025 (the years not under active refresh): `clim(d) = mean_y cpue1(y, d)`. Optionally
   smooth `clim(d)` with a short centered window (e.g. +/-3 days) to suppress single-day gillnet noise. This
   DOY climatology is computed FROM the real feed, not the `salmon.py` double-Gaussian `_climatology_series`
   placeholder (the placeholder is the WITHHELD fallback, not the anomaly baseline).
2. **Form the anomaly.** `run_anom(t) = run_index_real(t) - clim(DOY(t))`. The anomaly is mean-zero over the
   climatological cycle by construction, so it is approximately orthogonal to `k_season`; standardize it
   (z-score over in-season days) before entry.
3. **Apply the pre-registered out-of-sample lag.** Use the non-negative, run-leads lag `L*` selected
   OUT-OF-SAMPLE on the training years by the existing `salmon_lag.py` machinery (`_best_lag_masked` on the
   training mask; G3 reports training-fixed lags clustered at **17-21 d**, with the 2021 held-out year at
   **+17 d**). Enter the lagged anomaly `run_anom(t - L*)` as the slow effect-modifier `k_salmon`. The lag
   range, sign, and Jun-Sep window stay the frozen `PREREG_*` values (section 1e); the anomaly transform does
   NOT re-open the lag search.

### 2b. B.2 role + collinearity
- **Role: (b) effect-modifier**, estimated from effort-stable ACOUSTIC detections with the `log E` offset.
  The run index is a measured CPUE series used as a covariate; it is never laundered into a whale GPS fix
  (a hydrophone detection is a fixed-position presence event, not a located animal). (B.2; M3 section 0.1.)
- **Collinearity:** the raw run index is MODERATE-HIGH with `k_season`; the anomaly construction removes the
  DOY-climatology component, leaving the independent year/within-season departure. Fit jointly with
  `k_season` and report the MARGINAL fold-stable CV mean-deviance-skill of the anomaly, never the raw index
  alone (M3 D1; SYN section 4).

### 2c. Scoring (when a future, operator-gated step actually runs it)
Score through the existing `block_cv` harness with the served kernels, `write_outputs=False`, in an isolated
scratch dir, under the refit-safe env (B.5/B.6): `ORCAST_STORAGE_BACKEND=aws
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`, with
`fit_kernels._maybe_write_s3 = lambda: None`. Judge by per-fold held-out CV mean-deviance-skill (>=4/5 folds
positive, across-fold lower bound >= +0.078, PIT calibrated), NEVER in-sample likelihood or added
parameters. This agent runs no such fit.

## 3. Expected-skill band (HONEST, not measured here)

| Item | Expected fold-stable Delta CV mean-deviance-skill | Basis | Status |
|------|---------------------------------------------------|-------|--------|
| D1 lagged run ANOMALY, real Albion feed, anomaly vs DOY climatology, fit jointly with `k_season` | **+0.02 to +0.08** (expectation band) | M3 D1 / SYN B3 expert prior; the strongest non-tidal biological driver, but feed- AND presence-day-gated | **NOT-MEASURED** (no fit run in this lane) |
| D1 on the climatology PLACEHOLDER (no real feed) | 0 / not creditable | B.3 withhold-over-fake | **WITHHELD** |
| Measured served CV-skill delta from D1 | -- | -- | **NOT-MEASURED** |

Notes:
- The +0.02 to +0.08 figure is the M3/SYN EXPECTATION band, explicitly NOT a measured result. No measured
  per-fold number exists for D1 in this lane (none was fit; HARD RAIL: no production write).
- Even the high end of the band does not, on its own, guarantee crossing the +0.144 bar
  (served +0.078 -> 0.49 HOLD; +0.144 -> 0.60), and the band is **conditioned on summer presence-days**
  that do not yet exist at adequate power (G3 section 2b: ~12-15 Jun-Sep presence-days/yr needed vs 5-9 now;
  current LOYO 2/5). So the realized skill is gated on TB1, not on this feed.

## 4. Go / no-go (explicit: WITHHELD, supporting-only)

- **GO (cheap, safe, supporting): the live 2026 Albion refresh runbook (section 1) and the run-anomaly
  recipe (section 2).** Design-complete, no parser change, runs on the aimez EC2, keeps `PREREG_*` frozen,
  overwrites only `fos2026.csv` in place. It is the housekeeping that lets a future 2026 Jun-Sep OOS test be
  RUN. It promotes nothing and adds no acoustic presence-day. This is a SUPPORTING step, not the L3 lever.

- **NO-GO / WITHHELD: any L3 promotion or D1 credit today.** Per G3 section 3, L3 stays WITHHELD: no fresh
  out-of-sample replication (only the in-cache 2021/2023 hits, which motivated the pre-registration and
  cannot count as confirmation), LOYO 2/5, in-sample raw p (0.013) on the Bonferroni x4 line (0.052). The
  binding constraint is summer PRESENCE-DAYS (TB1), not the feed. D1 stays WITHHELD on the climatology
  placeholder and contributes 0 until a real-feed anomaly is scored on SERVED data under the G2 gate with a
  recorded supervisor decision (B.1). **Effective confidence stays 0.0.**

- **Sequencing.** Stand up the Albion refresh now (GO, supporting); re-run `salmon_lag.py` against the
  sec-3 bar only AFTER TB1 lands new in-region presence-days + >=1 fresh well-powered summer season. Do not
  frame "validate the feed" or "more prey series" as the +0.144 lever (DE3 rows #3-9; DE1 row #5).

## 5. PATCH-SPEC (for the later single-editor, operator-gated integrate -- not applied here)

Convergence files are NOT edited in this lane (charter section 1). The integrate, if D1 ever graduates, is a
separate single-editor step. Spec:

1. **`modeling/` design (e.g. `design.py` / the salmon covariate wiring):** add a `run_anom` column =
   real-feed `run_index` minus its DOY climatology (built from back-years 2019-2025), z-scored, then lagged
   by the `salmon_lag.py` training-selected `L*`. Enter as the `k_salmon` effect-modifier alongside (not
   replacing) `k_season`. Gate entry on `real_feed_only=True AND stock_aligned=True`; on the climatology
   placeholder, keep `k_salmon` WITHHELD (no anomaly, contributes 0).
2. **`src/aws_backend/sources/salmon.py`:** no parser change required (`_load_albion_fos` already reads
   `fosYYYY.csv`/`cpue1`). Optional: expose a `run_index` minus DOY-climatology helper so the anomaly is
   computed from the same normalized series, keeping the placeholder path WITHHELD.
3. **`modeling/studies/salmon_lag.py`:** NO change to `PREREG_*`. If the anomaly response is added as a
   scored variant, it must reuse the frozen Jun-Sep window, +lag sign, and [0,30] range; the anomaly is a
   transform of the predictor `x`, not a re-tuning of the hypothesis.
4. **Refit safety (B.5/B.6):** any scoring run uses `write_outputs=False`, the AWS bucket env, and
   `_maybe_write_s3 = lambda: None`; never writes a served artifact; a confidence change is a recorded
   supervisor decision, never a refit side effect.

**DE drift note (carry forward to the integrate single-editor):** this patch-spec touches the L3/salmon
framing flagged by DE. Append the supersession caveat per **DE3 rows #3-9** (the stale "L3 blocked on / needs
a real Chinook feed" framing across the mlops-handoff chain and the wildlife register acquisition order #2 --
G3: feed is real/stock-aligned; binding lever is presence-days; CUTI/BEUTI NO-GO) and **DE1 row #5** (the
wildlife register's CUTI/BEUTI Tier-1 listing -> WITHHELD, out of 31-47 N coverage). TB3 = supporting only;
do not re-present the feed as the L3 lever.

## 6. Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB3_albion_anomaly.md`.
- **Runbook:** live 2026 Albion refresh on EC2 `i-04a649f91274e9fce` (B.9), direct POST -> parse 12-token
  rows -> overwrite-in-place `data/salmon/albion_fos/fos2026.csv`, `PREREG_*` frozen, weekly Jun-Oct +
  post-season November, manifest with monotone/non-regressing integrity guards. Current cache stops
  2026-06-26 (before the peak) -- the measured reason the refresh matters.
- **Anomaly recipe:** `run_anom(t) = run_index_real(t) - clim(DOY(t))` (DOY climatology built from real
  back-years 2019-2025), z-scored, entered as `k_salmon` at the pre-registered run-leads lag `L*` (~17-21 d,
  +17 d held-out), fit jointly with `k_season`; B.2 role = effect-modifier on effort-stable acoustic
  detections with `log E`.
- **Expected-skill band:** D1 real-feed anomaly **+0.02 to +0.08** (EXPECTATION, **NOT-MEASURED** here);
  on the climatology placeholder it is **WITHHELD** (0, not creditable). No measured fold numbers (no fit
  run).
- **Go/no-go:** GO on the refresh runbook + anomaly recipe as **SUPPORTING ONLY**; **L3 stays WITHHELD** and
  **D1 stays WITHHELD** on the placeholder. The binding L3 lever is summer PRESENCE-DAYS (TB1), not the feed
  (G3). CUTI/BEUTI NO-GO (coverage).
- **DE drift note:** DE3 rows #3-9 (stale feed-as-L3-lever framing) + DE1 row #5 (CUTI/BEUTI coverage).
- **Confirmation:** nothing fetched-to-write, nothing deployed, nothing promoted, nothing committed; no
  convergence-file edit; no served/S3/model write. **Effective confidence stays 0.0.**

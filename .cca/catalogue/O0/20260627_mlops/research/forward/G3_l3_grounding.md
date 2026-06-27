# G3 -- L3 grounding (grounds W8 / O4)

Agent: G3, W5 grounding wave of the forward-path ML-ops campaign. Date 2026-06-27
(America/New_York). Repo: `/Users/gilraitses/orcast`.

Authority: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (locked) and
`.cca/catalogue/O0/20260627_mlops/CAMPAIGN_CHARTER.md` (this campaign, O4 / W8).
Investigation-first: this is the ONLY doc this agent writes. No convergence-file edit, no fetch run,
no fit, no S3/model/store write, no promotion, no commit. **L3 stays WITHHELD.**

Hydrated from: `salmon_lag.py` (full-span scan + the pre-registered Jun-Sep summer scan +
held-out-year + LOYO + `_STOCK_ALIGNED_SOURCES` + `real_feed_only`), `salmon.py`
(`_fetch_fraser` / `_load_albion_fos`, cache `data/salmon/albion_fos/fosYYYY.csv`),
`WIRING-salmon-albion.md` (DFO FOS fetch recipe via aimez EC2), `research/L3_conditioning.md` (RB),
and the live report `modeling/studies/reports/salmon_lag.json`.

## 0. Current L3 state (the numbers this doc reasons about)

From `reports/salmon_lag.json` (regenerated 2026-06-27, real Albion feed all years 2020-2026,
`real_feed_only=true`, `stock_aligned=true`):

| Test | n (in-season days / presence-days) | best lag | r | p | verdict |
|---|---|---|---|---|---|
| Full-span pooled | 2088 / 163 | +20 d | 0.076 | **0.394** | does not beat null |
| Pre-reg Jun-Sep in-sample | 629 / 36 | +20 d | 0.251 | **0.013** | beats null (exploratory) |
| Held-out 2021 OOS @ train-lag 17 d | 122 / 9 | (fixed) | 0.390 | **0.027** | beats null -> FLAG |
| Counts Jun-Sep (informational) | 629 / -- | +23 d | 0.221 | 0.009 | beats null |

LOYO sensitivity (years with >=3 Jun-Sep presence-days; lag fixed on the other years, evaluated OOS):

| Held-out year | summer presence-days | train-lag | OOS r | OOS p | beats p<0.05 |
|---|---|---|---|---|---|
| 2020 | 3 | 20 d | 0.000 | 1.000 | no |
| 2021 | 9 | 17 d | 0.390 | 0.027 | **yes** |
| 2022 | 7 | 20 d | 0.004 | 0.953 | no |
| 2023 | 8 | 21 d | 0.265 | 0.044 | **yes** |
| 2024 | 5 | 20 d | -0.097 | 0.387 | no |

**LOYO = 2 of 5.** Jun-Sep presence-days by year: 2020:3, 2021:9, 2022:7, 2023:8, 2024:5, 2025:2,
2026:2 (2025/2026 fall below the >=3 LOYO floor). Total Jun-Sep presence = 36 days; per-year 2-9,
median ~5. Status today: **FLAGGED-FOR-DECISION** (the held-out year beat the pre-registered null);
this is surfaced for an operator/supervisor decision and does NOT self-promote (B.1).

The flag is real but **fragile**: it rests on one data-rich held-out year (2021, 9 presence-days),
the two LOYO hits are the two most data-rich years (2021, 2023), and the in-sample p sits right on
the multiplicity edge (sec 2). The binding constraint is **summer acoustic presence-days**, not the
salmon feed: the Albion run-index series is already real, complete, and stock-aligned for every
detection year.

---

## 1. Live 2026 Albion fetch design (design only -- NOT run here)

**Goal.** Keep the Albion (Fraser-summer Chinook) run-index series current so a 2026 Jun-Sep
out-of-sample test can even be RUN. This extends `WIRING-salmon-albion.md`; it does not change any
parser (`_load_albion_fos` already reads `data/salmon/albion_fos/fosYYYY.csv` and keys `cpue1`).

### 1a. Provenance (unchanged, restated for the manifest)
- Source: DFO Fishery Operations System (FOS), **Albion test fishery**, "Catch Summary by Date"
  report. Params: `stat=CPTFM`, `fsub_id=242` (subsystem), `lboSpecies=124` (CHINOOK SALMON),
  `lboYears=<YYYY>`, `cmdRunReport=Run Report`. Licence: Open Government Licence - Canada.
- Value used: `cpue1` = standard 8-inch gillnet CPUE = the run-timing index. (`catch2/cpue2` are the
  large-mesh panel; not used.)
- Reachability: the host `www-ops2.pac.dfo-mpo.gc.ca` (resolves 205.193.114.62) is DNS-blocked from
  the dev host and the backend region; it IS reachable from the **aimez-services EC2**
  (`i-04a649f91274e9fce`, x86_64 Ubuntu, account 198456344617, us-east-1). All fetches run there;
  the parsed CSV is copied back into the repo cache. No live in-process pull.

### 1b. Fetch recipe (extends the WIRING recipe; run ON the EC2)
A direct POST returns the report HTML (no Selenium / JS form-driving needed):

```
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177   # aimez EC2 (SSM fallback 198456344617/us-east-1)

YEAR=2026
curl -sS -c /tmp/fc.txt \
  "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242" -o /dev/null
curl -sS -b /tmp/fc.txt \
  -e "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242" \
  --data "lboYears=${YEAR}&lboSpecies=124&lboFsub=242&cmdRunReport=Run+Report" \
  "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptCSbD.cfm?stat=CPTFM" -o /tmp/fos.html
```

### 1c. Parsing (matches `_load_albion_fos` expectations exactly)
- Each data row is a `<tr>` whose stripped text splits into **exactly 12 whitespace tokens**;
  `tokens[0]` = day number, `tokens[1]` = 3-letter month.
- Write CSV with header
  `day,mon,year,netlen,catch1,sets1,effort1,cpue1,catch2,sets2,effort2,cpue2`, csv-quoting the
  comma-bearing effort fields (e.g. `"16,300"`), exactly like the existing
  `data/salmon/albion_fos/fos2026.csv`.
- `_load_albion_fos` reads `mon` (3-letter), `day`, `year` and the `cpue1` column; it tolerates the
  quoted-comma effort fields and skips unparseable rows. No parser change required.

### 1d. Cache path + idempotency
- Write `data/salmon/albion_fos/fos2026.csv` (overwrite-in-place). The FOS report is **cumulative
  season-to-date**, so re-fetching simply yields a longer table; overwrite is idempotent and safe.
- Current cache state: `fos2026.csv` covers **2026-05-01 .. 2026-06-26** -- i.e. it stops *before*
  the late-Jul/Aug summer peak. A 2026 Jun-Sep OOS test today would see a truncated, near-zero
  summer run index and would be invalid; this is the concrete reason the refresh matters.

### 1e. Refresh cadence
- Albion season runs ~April-October; the summer Chinook peak is ~late-July to August. The lag test
  needs the run index from ~mid-May through end-September of the test year (Jun-Sep presence at a
  +17 to +20 d run-leads lag pulls run-index values back into mid-May).
- Cadence: **weekly refresh of the current year, Jun through Oct**; one **final post-season refresh
  in November** to freeze the year; **no refresh Nov-Mar** (off-season, run index ~0). Back-years
  (2019-2025) are stable and need no refresh.
- Per refresh, record a provenance manifest line: fetch UTC timestamp, the POST params, row count,
  season-to-date `max(cpue1)` and its date, and a sha256 of the CSV. Validate that row count is
  monotone non-decreasing and the season max does not regress vs the prior pull (guards a partial /
  truncated report).

### 1f. What this does and does NOT buy
- It makes the 2026 run index complete enough to **run** a 2026 Jun-Sep OOS test. **Necessary.**
- It does **not** add a single acoustic presence-day. The run index is the predictor (x); the
  binding constraint is the response (summer presence-days, y). Extending Albion alone cannot move
  L3 off WITHHELD (sec 4).

---

## 2. Power analysis: how much more data the held-out test needs

The pre-registered test is a point-biserial / Pearson correlation of a sparse **binary** presence
series (y) against the Albion run index (x), scored against a circular-shift permutation null. Two
distinct things are under-powered: (a) within-year detectability (presence-days), and (b) the
cross-year robustness count (number of summer seasons).

### 2a. Multiplicity correction (quantified)
RB scored **4** season/SRKW windows (run-active, calendar DOY 90-310, Jun-Sep, May-Oct). The lag
multiplicity (over +lags) is already absorbed by the best-|corr| permutation statistic, but the
**window** choice is not. Bonferroni over the 4 windows:

| Test | raw p | x4 (Bonferroni) | clears 0.05? |
|---|---|---|---|
| in-sample Jun-Sep | 0.013 | **0.052** | no (just over) |
| held-out 2021 OOS | 0.027 | **0.108** | no |
| counts Jun-Sep | 0.009 | 0.036 | yes |

So under a conservative auditor (treat the window as shopped over 4), the **in-sample result fails
(0.052) and the OOS result fails (0.108)**; only the counts variant survives. The only thing that
rescues the binary in-sample/OOS p is **pre-registration**: `salmon_lag.py` fixes Jun-Sep, the +lag
sign, and lag range [0,30] a priori (`PREREG_SUMMER_MONTHS`, `PREREG_LAG_SIGN`), which legitimately
sets the window multiplicity factor to **1**. The honest hinge for the operator: if Jun-Sep is
accepted as genuinely pre-specified, raw p (0.013 / 0.027) stands; if not, the result is at/over the
0.05 edge. To clear Bonferroni x4 on its own, the **raw in-sample p must fall below 0.05/4 = 0.0125**
(currently 0.013, i.e. essentially at the line).

### 2b. Within-year power (presence-days needed)
For a Pearson correlation at alpha=0.05 (two-sided), 80% power, the required paired-observation count
is ~123 for r=0.25, ~85 for r=0.30, ~49 for r=0.39. The Jun-Sep window already supplies ~120-122
*calendar* in-season days/year -- but the series is **binary and ~94% zeros**, so the effective
information is governed by the **minority class (presence-days)**, not calendar days. The current
years carry only 5-9 presence-days; only the 8-9-day years (2021, 2023) detected the effect, the
3-5-day years did not. Practical target: **~12-15 Jun-Sep presence-days per year** to give a single
held-out year ~80% power at the observed OOS effect (r~0.39), and **~70-80 aggregate Jun-Sep
presence-days** (roughly double the current 36) to drive the in-sample raw p below the 0.0125
Bonferroni line. The 2021 year (9 days) was at the detectability margin.

### 2c. Cross-year power (how many more summer seasons)
LOYO is a k-of-n test. Against the per-year false-positive rate (each OOS test uses p<0.05, so a
true-null year "hits" with prob ~0.05), the minimum k for family-wise alpha<=0.05 is:

| n testable years | min k for FWER<=0.05 | P(X>=k \| null) |
|---|---|---|
| 5 (today) | 2 | 0.023 |
| 6 | 2 | 0.033 |
| 7 | 2 | 0.044 |
| 8 | 3 | 0.006 |
| 9 | 3 | 0.008 |
| 10 | 3 | 0.012 |

The current **2 of 5 is already significant against the false-positive null (P=0.023)** -- but a
"k=2" bar is weak: it can be satisfied by exactly the two data-rich years and gives little assurance.
A more demanding **">=3 of n" majority bar** needs n>=8 to stay valid, and to have 80% *power* to
actually reach >=3 hits depends on the true per-year detection rate p1:

| true per-year detect rate p1 | n for ~80% power at the ">=3 of n" bar |
|---|---|
| p1 = 0.4 (current-quality years) | ~9-10 seasons |
| p1 = 0.5 | ~8 seasons |
| p1 = 0.6 (after raising presence-days/yr) | ~6 seasons |

**Bottom line.** From today's 5 testable seasons, the test becomes robust at roughly **+3 to +5 more
adequately-powered summer seasons** (n~8-10), *and* each season needs to carry ~12-15 Jun-Sep
presence-days (vs 5-9 now). Equivalently: roughly **double the per-year presence-days and add 3-5
seasons.** The lever for both is the W6 multi-station production ingest (it lands `haro_strait` -- the
dense node, 761 detections, entirely absent from the cached index -- plus accumulating future
summers), not the Albion feed.

---

## 3. Decision bar (FLAGGED-FOR-DECISION -> operator promotion decision)

For the L3 flag to graduate from "flagged" to an actual operator promotion decision, **all** of the
following must hold (any one failing keeps it WITHHELD):

1. **Stock-aligned real feed.** Every contributing run-index year is Albion (Fraser-summer Chinook),
   `real_feed_only=true`, `stock_aligned=true`. *(Met today.)*
2. **Pre-registration intact.** Jun-Sep window, run-leads (+lag only), lag range [0,30] fixed before
   the confirmatory test (already in `salmon_lag.py`). The confirmatory year(s) must not re-tune the
   window. *(Met for the existing code; must stay locked.)*
3. **Out-of-sample replication on NEW data.** At least one summer season **not in the current cache**
   (2026 full Jun-Sep first, then subsequent years) held out, lag fixed from the other years, and
   beating the pre-registered null at **p<0.05** at the training-fixed lag. The in-cache 2021/2023
   hits do not count toward this; they motivated the pre-registration, replication must be fresh.
4. **LOYO majority, adequately powered.** **>=3 of n** testable years beat the null at p<0.05, with
   **n>=8** seasons each carrying **>=~10-12 Jun-Sep presence-days** (so the 2/5 result is not the
   ceiling). Per sec 2c this is the validity+power bar.
5. **Multiplicity-clean significance.** Either the raw in-sample p falls **below 0.0125** (clears
   Bonferroni x4 unconditionally), or the pre-registration in (2) is formally accepted by the
   operator as setting the window factor to 1 (raw p stands). State which basis is used in the
   decision record. *(Today: 0.013, i.e. on the line -- not yet clean.)*
6. **Supporting evidence consistent.** The counts re-test on Jun-Sep continues to agree in sign and
   lag (currently +23 d, r=0.22, p=0.009). Supporting, not sufficient.

Even if (1)-(6) all pass, this is a **B.1 supervisor/operator promotion decision**, never an
auto-promote: `salmon_lag.py` only sets `flag_for_operator_decision`, never `GATE_PASS`.

**What keeps L3 WITHHELD (today and by default):** any of -- feed not stock-aligned; window not
pre-registered or re-tuned; no fresh out-of-sample replication (only the in-cache 2021/2023 hits);
LOYO stuck at <=2/5 or on under-powered (<10 presence-day) years; raw in-sample p >= 0.0125 with
pre-registration not accepted; or insufficient per-year presence-days. **All of these hold right
now** (no fresh replication yet; LOYO 2/5; p on the Bonferroni line), so the honest status is
WITHHELD-with-a-flag.

---

## 4. Go / no-go for W8

**Split decision, stated honestly.**

- **GO (cheap, safe, now): wire the live 2026 Albion fetch (sec 1).** It is design-complete, needs no
  parser change, runs on the aimez EC2, and is *necessary* to ever run a 2026 Jun-Sep OOS test (the
  cache currently stops 2026-06-26, before the peak). This is the safe piece W5 can hand to W8. It
  promotes nothing.

- **NO-GO (today) on an L3 promotion decision.** The flag does not clear the decision bar (sec 3):
  no fresh out-of-sample replication, LOYO 2/5, in-sample p (0.013) on the Bonferroni x4 line
  (0.052). Promoting now would be over-reading a fragile, multiplicity-edge result on 36 presence-
  days. **L3 stays WITHHELD.**

- **Sequencing the real lever.** The binding constraint is summer **presence-days**, not the salmon
  feed. Extending Albion alone cannot move L3. The data that can is the **W6 multi-station production
  ingest** (`haro_strait` + accumulating summers), which is exactly the dependency G1 grounds and the
  whole campaign gates on. So W8's L3 re-test should be **gated on W6 landing + >=1 fresh well-
  powered summer season**, not launched on the Albion extension by itself.

- **Recommended W8 shape.** (i) Stand up the live Albion refresh now (GO). (ii) After W6 ingest,
  re-run `salmon_lag.py` on the denser, multi-station summer presence and re-evaluate against the
  sec-3 bar. (iii) Each new summer season, hold it out fresh and accrue LOYO toward >=3/n at n>=8.
  (iv) Only when the bar is met, route a B.1 operator/supervisor decision. Until then: WITHHELD,
  honestly, with the flag carried forward.

**One residual risk.** Window-shopping drift: if any future agent re-tunes the Jun-Sep window or the
lag to chase a smaller p, the pre-registration (and therefore the only thing rescuing the binary p
from Bonferroni) is destroyed. The window and lag sign must stay frozen exactly as
`salmon_lag.py::PREREG_*` has them; the confirmatory work may add data and seasons but must not touch
the hypothesis.

---

*No promotion. No commit. L3 WITHHELD. This doc is the only file G3 wrote.*

# G2 promotion-protocol grounding (grounds W7 / O3)

Agent: G2 promotion-protocol grounding agent, W5 of the forward-path ML-ops campaign.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`.
Home: `.cca/catalogue/O0/20260627_mlops/research/forward/G2_promotion_protocol.md` (this doc; no
other file edited).
Authority: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B; `CAMPAIGN_CHARTER.md`;
`DECISION_RECORD.md` section 4 (adopted bin-level timing gate).
Scope: investigation + spec only. No refit that writes, no promotion, no commit. Effective
confidence stays 0.0.

## 0. What I read (hydration)

- `HANDOFF_CHARTER.md` section B (B.1 promotion = passing gate on SERVED data + recorded supervisor
  decision; B.4 bucket footgun; B.5 refit-upload-disable; B.6 local-only modeling tree).
- `CAMPAIGN_CHARTER.md` + `CAMPAIGN_DISPATCH.md` (the G2 brief).
- `DECISION_RECORD.md` section 4 (adopted bin-level timing gate; the armed-cliff record now mitigated
  by P0).
- `STEP_LOG.md` (the P0 entry; the multi-station experiment entry; the W4 entries).
- `modeling/fit_kernels.py` CURRENT state: `_confidence_from_gates`, `_bin_level_timing_gate`,
  `ADOPT_BIN_LEVEL_TIMING_GATE = True`, `run_fit(write_outputs=...)`, `_maybe_write_s3`.
- `modeling/studies/level2_multistation.py` (4-station memory-store reproduction;
  `fk._maybe_write_s3 = lambda: None`, `write_outputs=False`).
- `modeling/studies/reports/level2_multistation.json` (the experiment's recorded numbers).
- `src/aws_backend/promotion/supervisor.py` (deterministic promote/hold rule).
- `research/L2_data_volume.md` (RE reliability-vs-N curve) + `research/SYNTHESIS_L2_L3.md` (RF
  corrected blocker map). G1's `research/forward/G1_ingest_deploy.md` does not exist yet, so the
  net-new estimate below uses the dispatch-stated assumption (~1029/265/34) and is reconciled against
  RE's refutation.

## 0.1 The exact mappings I saw in the CURRENT code (verbatim grounding)

**P0 confidence map** (`fit_kernels.py` `_confidence_from_gates`, constants at the top of that
block):

```
_CONF_SKILL_TAU     = 0.12   # skill scale; skill ~ TAU earns ~63% of the evidence cap
_CONF_EVIDENCE_CAP  = 0.50   # max of the joint CV/timing evidence block
_CONF_PIT_BONUS     = 0.15   # awarded only when the timing gate passes
_CONF_LEVEL1_BONUS  = 0.10   # marginal-PSTH (Level 1) modifier
_CONF_CAP           = 0.75   # hard ceiling on served confidence (strictly < 1.0)

cv_pass    = cv.gate_pass AND cv.mean_deviance_skill > 0          # else 0.0 floor
timing_gate= tr_pass OR (ADOPT_BIN_LEVEL_TIMING_GATE AND bin_level)
if not (cv_pass or timing_gate): return 0.0                       # hard floor
s          = max(cv_mean_deviance_skill, 0)
skill_sat  = 1 - exp(-s / 0.12)
gate_factor= 0.5*cv_pass + 0.5*timing_gate                        # {0.5, 1.0}
score      = 0.50 * gate_factor * skill_sat
score     += 0.15  if (timing_gate AND pit.calibrated)            # else 0
score     += 0.10  if any Level-1 kernel beats its null           # else 0
confidence = round(min(0.75, score), 2)
```

**Bin-level timing gate** (`_bin_level_timing_gate`, with `ADOPT_BIN_LEVEL_TIMING_GATE = True`,
recorded in `DECISION_RECORD.md` section 4): passes iff `pit.calibrated` AND
`cv.mean_deviance_skill > 0`. The PIT half is near-automatic under NB free dispersion; the CV-skill
half is the load-bearing, non-automatic half.

**Supervisor rule** (`promotion/supervisor.py` `_deterministic_decision`, `_PROMOTE_CONFIDENCE = 0.6`):
`recommend = "promote" if (confidence >= 0.6 AND cv_gate_pass AND pit_calibrated) else "hold"`. It
reads `cv.gate_pass`, `pit.calibrated`, `cv.mean_deviance_skill`, `time_rescaling.pooled_pass_exp`,
`level1_psth.*.beats_null`, `confidence` from the gate report.

**Refit safety surfaces**: `run_fit(store, bin_hours=1.0, write_outputs=True, ...)`; the production
model-artifact upload is `_maybe_write_s3()` (uploads coefficients + report to `settings.models_bucket`
in aws mode), called inside `run_fit` only when `write_outputs` is True. The experiment driver sets
`fk._maybe_write_s3 = lambda: None` and calls `run_fit(..., write_outputs=False)`.

### The key tension, quantified (verified arithmetic)

Confidence as a function of served held-out CV mean-deviance-skill `s`, with both joint gates passing
(`gate_factor = 1.0`), PIT calibrated (+0.15), and a Level-1 kernel beating its null (+0.10):

| served CV skill `s` | confidence | band |
|---|---:|---|
| `<= 0` | **0.00** | hard floor (gate closed); current served single-station is `-0.047` |
| `+0.050` | 0.42 | HOLD (lifts confidence, below 0.6) |
| `+0.078` (experiment) | **0.49** | HOLD (lifts confidence, below 0.6) |
| `+0.100` | 0.53 | HOLD |
| `+0.120` | 0.57 | HOLD |
| `+0.144` | **0.60** | promote-eligible (0.6 crossing) |
| `+0.150` | 0.61 | promote-eligible |
| `+0.200` | 0.66 | promote-eligible |
| `+0.300` | 0.71 | promote-eligible |
| `-> inf` | 0.75 | hard cap |

So the 3-node ingest, which is expected to flip served CV-skill toward the experiment's `+0.078`,
maps to **0.49 (HOLD)**, below the 0.6 supervisor threshold. The ingest ALONE does NOT promote.

**What it WOULD take to cross 0.6** (solving `0.50*(1 - exp(-s/0.12)) + 0.25 = 0.60`):
`exp(-s/0.12) = 0.30`, `s = -0.12 * ln(0.30) = +0.1445`. Served held-out CV mean-deviance-skill must
reach **~+0.144** (about 1.85x the experiment's +0.078) WITH both joint gates passing, PIT
calibrated, and a beaten Level-1 null. If PIT is not calibrated, the bin-level timing gate cannot
pass (it requires PIT calibrated AND skill > 0), so `timing_gate` falls back to the event-level
Exp(1) pass (currently WITHHELD), `gate_factor` drops to 0.5, the +0.15 PIT bonus is withheld, and
the maximum achievable confidence is **0.35**, which can never reach 0.6. Promotion therefore
requires the full stack: positive robust CV-skill AND PIT calibration AND a beaten Level-1 null AND
`s >= ~0.144`.

Note: `level2_multistation.json` currently records `confidence_unpromoted: 0.5`; that value was
written under the pre-P0 flat-quarter map and is stale. The CURRENT `_confidence_from_gates` maps the
recorded `+0.0778` to **0.49**. A re-run of the experiment under the current code would record 0.49.

---

## 1. "Robustly positive" held-out CV mean-deviance-skill (promotion definition)

Grounded in the existing CV machinery: `run_fit` produces `report["cv"]` with `n_folds`, `n_pass`,
`gate_pass`, and `mean_deviance_skill`; the experiment recorded `cv_folds_passing = "4/5"` at
`mean_deviance_skill = +0.0778`. The supervisor reads `cv.gate_pass` and `cv.mean_deviance_skill`.

### Two distinct bands (do not conflate)

**(A) "Lifts served confidence" (HOLD band, `0 < conf < 0.6`).** Triggered by a merely positive
served fit:
- `cv.mean_deviance_skill > 0` (so the 0.0 floor opens and `cv_pass` is true), AND
- fold stability: `n_pass / n_folds >= 0.8` (at least 4 of 5 folds individually positive), so a
  single lucky fold cannot open the gate.
- Effect: confidence rises into roughly `[0.25, 0.59]` (e.g. `+0.078 -> 0.49`). The supervisor reads
  `confidence < 0.6` and recommends **HOLD**. This is a non-promoted, sub-0.6 served state: the
  display moves off 0.0 only if the operator separately accepts a sub-0.6 served value (see section
  5). By default a HOLD recommendation does not change `effective_confidence`.

**(B) "Robustly positive -> promotes" (`conf >= 0.6` + cv + pit).** The bar that should be allowed to
raise `effective_confidence`:
1. **Fold count / scheme.** Keep the existing K = 5 cross-validation already wired into `run_fit`
   (the experiment reports `n_folds = 5`). Report per-fold skills, not only the mean, so the
   stability and variance bounds below are checkable. The scheme stays the one the pipeline already
   uses (do not re-tune folds to manufacture a pass).
2. **Point margin (load-bearing).** `cv.mean_deviance_skill >= +0.144`. This is the P0 0.6-crossing
   derived above. It is ~1.85x the experiment's `+0.078`, deliberately "about double a single lucky
   fold," so promotion means a clearly positive effect, not a marginal tick over zero.
3. **Fold stability.** At least 4 of 5 folds individually positive (`n_pass/n_folds >= 0.8`); 5/5
   preferred. The experiment's `4/5` meets this stability test but fails the margin test (+0.078 <
   +0.144).
4. **Variance bound (no lucky-fold pass).** Compute the across-fold standard error
   `SE = sd(per-fold skill) / sqrt(K)`. Require the one-sided lower bound to also stay clearly
   positive: `mean - t_{K-1, 0.95} * SE >= +0.078`, i.e. even the conservative lower estimate clears
   the experiment level. This guards the point estimate against a high-variance fold pattern that
   averages to +0.144 but swings negative on some folds.
5. **Calibration precondition.** `pit.calibrated` must be true (the supervisor requires it AND it is
   what lets the adopted bin-level `timing_gate` pass, which in turn unlocks `gate_factor = 1.0` and
   the +0.15 PIT bonus needed to reach 0.6).
6. **Level-1 corroboration.** At least one Level-1 kernel beats its null (already PASS: diel
   modulation 1.79, p = 0.0005), supplying the +0.10 modifier; without it the 0.6 crossing shifts to
   a higher skill.

Only band (B) is a promotion candidate. Band (A) is an operator display decision, not an automatic
promotion (section 5).

### Why this is the honest bar

The P0 map was built so the cliff (any positive skill -> 1.0) is gone; crossing 0.6 now demands ~2x
the experiment margin. Pinning the promotion bar to `+0.144` ties "robustly positive" to the exact
point where the served confidence the supervisor reads crosses its own threshold, so the modeling
definition and the supervisor rule cannot drift apart. The fold-stability and variance bounds make
the bar robust to fold noise; the calibration precondition keeps PIT from being credited while the
timing is demonstrably wrong (event-level Exp(1) is WITHHELD on this detector-chatter stream, Hawkes
branching 0.79 to 0.96).

---

## 2. Multi-station SERVED refit reproduction spec

Goal: reproduce the multi-station fit against the SERVED store after W6 lands, scoring confidence
under the current P0 map, without any production write and without promoting.

### Environment (B.4 / B.5 / B.7)

```
ORCAST_STORAGE_BACKEND=aws \
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
AWS_REGION=us-west-2 \
PYTHONPATH=. \
.venv-modeling/bin/python -m modeling.studies.level2_multistation
```

- `.venv-modeling` (numpy 2.4.6, pandas, scipy, boto3): the only env that runs the heavy fit (B.7).
- Bucket B.4 (`198456344617-...-raw-payloads`, us-west-2), NOT the config default
  `orcast-raw-payloads` (the documented footgun).
- Refit safety (B.5), already baked into `level2_multistation.py`: `fk._maybe_write_s3 = lambda: None`
  AND `fk.run_fit(mem, bin_hours=1.0, write_outputs=False, make_figures=False)`. `write_outputs=False`
  skips `_write_report_json`, `_write_coefficients`, and the `_maybe_write_s3` call path; the lambda
  override is belt-and-suspenders against the production `models_bucket` upload. No production store
  or model bucket is touched; `data/models/fit_report.json` (served confidence 0.0) is untouched.
- Local-only / untracked (B.6): `fit_kernels.py` + `data/models/` stay local; only
  `modeling/studies/**` + `reports/*.json` are tracked.

### How the SERVED fit becomes 4-station once W6 lands (vs the memory-store experiment)

Today the experiment in `level2_multistation.py` builds a `MemoryTimeSeriesStore` by hand: it reads
the production `haro_strait` `acoustic_detections` stream from S3, then injects the OTHER three nodes
(orcasound_lab, andrews_bay, north_san_juan_channel) from the cached OrcaHello index
(`orcahello_index.cache.json`) via `_cached_acoustic_by_station()`, plus S3 `env_currents` and
`station_uptime`. The four-station spike train is mixed-provenance (production stream + cache) and
exists only in memory, which is exactly why it is an EXPERIMENT and is never promoted.

After W6 (the operator/deploy-gated 3-node ingest, `ingest_multistation.py` with `dry_run=False`)
writes orcasound_lab / andrews_bay / north_san_juan_channel into the SERVED `acoustic_detections`
stream next to haro_strait, the served store itself becomes 4-station. The served reproduction then
no longer needs the cache injection: the standard pipeline

```
ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=<B.4> AWS_REGION=us-west-2 \
PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels --no-write
```

reads all four stations directly from the SERVED store via `read_streams`. The W7 served refit is
this single-source production read with the upload disabled (`--no-write`, which sets
`write_outputs=False`), producing a served `cv.mean_deviance_skill` and `confidence` to be compared
against `+0.144`. Distinction to record: the experiment value `+0.078` came from a mixed-provenance
memory store; the served W7 value will come from a single-provenance production store and may differ
(provenance, dedup, and the live reviewed-outcome set can shift the skill in either direction). The
promotion decision uses the SERVED number, never the experiment number (B.1).

---

## 3. Decision-record format (supervisor recommendation + human record)

### 3a. What `promotion/supervisor.py` generates (deterministic backend)

`draft_decision(report)` with the served W7 gate report yields a structured dict. Two grounded
scenarios:

**Scenario HOLD (ingest-only, served skill ~+0.078 -> confidence 0.49):**

```json
{
  "recommendation": "hold",
  "rationale": "Confidence 0.49 (< 0.6 threshold). Core gates (CV + calibration) pass. Recommend HOLD.",
  "cited_gates": [
    "held-out CV beats climatology",
    "PIT calibration holds",
    "time-rescaling GOF fails",
    "Level-1 null beaten by: diel"
  ],
  "gates_summary": {
    "confidence": 0.49, "cv_gate_pass": true, "cv_mean_skill": 0.078,
    "time_rescaling_pass": false, "pit_calibrated": true,
    "level1_beats_null": ["diel"], "n_detections": 2089
  },
  "source": "deterministic"
}
```

The supervisor recommends **HOLD** because `confidence (0.49) < 0.6`, even though both core gates
(CV + PIT) pass. No promotion; `effective_confidence` stays 0.0 unless the operator takes the section
5 sub-0.6 path.

**Scenario PROMOTE (robust skill ~+0.144 -> confidence 0.60):**

```json
{
  "recommendation": "promote",
  "rationale": "Confidence 0.60 (>= 0.6 threshold). Core gates (CV + calibration) pass. Recommend PROMOTE.",
  "cited_gates": [
    "held-out CV beats climatology",
    "PIT calibration holds",
    "time-rescaling GOF fails",
    "Level-1 null beaten by: diel"
  ],
  "gates_summary": {
    "confidence": 0.60, "cv_gate_pass": true, "cv_mean_skill": 0.144,
    "time_rescaling_pass": false, "pit_calibrated": true,
    "level1_beats_null": ["diel"], "n_detections": ...
  },
  "source": "deterministic"
}
```

The supervisor recommends **PROMOTE** when `confidence >= 0.6 AND cv_gate_pass AND pit_calibrated`.
`time_rescaling_pass` stays false and does not block promotion under the current rule (the timing
credit is carried by the adopted bin-level gate inside `_confidence_from_gates`, not by the
event-level Exp(1) pass the supervisor cites).

### 3b. The human record that finalizes it (B.1)

A supervisor recommendation is a draft only. The promotion is finalized by a recorded human decision,
appended to `DECISION_RECORD.md` (the tracked file; the served `fit_report.json` is local/untracked,
B.6), in the same form as section 4's adoption record:

```
## (date) Recorded supervisor decision -- PROMOTE multi-station L2 (W7)
- TRIGGER: served 4-station refit (post-W6 ingest), B.4 store, write_outputs=False, upload disabled.
- MEASURED: cv.mean_deviance_skill = <served value> (folds <n_pass>/<n_folds>, lower-bound <lb>),
  pit.calibrated = true (ks_pval <..>), level1 diel beats null, confidence = <P0-map value>.
- SUPERVISOR DRAFT: <promote|hold> (promotion/supervisor.py, deterministic), rationale quoted.
- ROBUST-SKILL CHECK (section 1B): margin >= +0.144 [pass/fail], fold stability >= 4/5 [pass/fail],
  variance lower bound >= +0.078 [pass/fail].
- DECISION: <PROMOTE to confidence <value> | HOLD at 0.0 | accept sub-0.6 served display at <value>>.
- OPERATOR: <name>, <timestamp>. effective_confidence set to <value> on this record (or unchanged).
```

### 3c. Where it crosses 0.6 under the P0 map

Promotion (supervisor `promote` + a recorded human PROMOTE) is reachable only when served
`cv.mean_deviance_skill >= ~+0.144` (confidence 0.60) with PIT calibrated and a beaten Level-1 null.
At the ingest-projected `+0.078` the served confidence is 0.49 and the supervisor recommends HOLD.
The band `0 < served skill < +0.144` maps to `0 < confidence < 0.6` and is HOLD by the deterministic
rule.

---

## 4. Consistency-after-ingest projection (12 bins)

This composes RE's reliability-vs-N curve (`research/L2_data_volume.md`) with G1's net-new estimate.
G1's doc (`research/forward/G1_ingest_deploy.md`) has since landed and confirms the figures used
here: the ingest writes orcasound_lab +1029, andrews_bay +265 (296 raw, deduped to 265),
north_san_juan_channel +34, total **+1328 net-new to the SERVED store** but **0 net-new to the
analysis universe** (the same cached OrcaHello rows the experiment already consumes). G1 reconciles
the two readings from different baselines exactly as below.

### Critical reconciliation (the net-new framing)

There are two different "net-new" meanings and they must not be conflated:

- **Net-new to the SERVED fit (real):** the served store today holds only haro_strait (761). Moving
  1029 / 265 / 34 into the served `acoustic_detections` stream makes the SERVED fit 4-station
  (~2089 detections). THIS is what flips served CV-skill from `-0.047` toward the experiment's
  `+0.078` and lifts served confidence to ~0.49. This is real and is the W7 trigger.
- **Net-new to the cross-station CONSISTENCY analysis (zero):** RE's decisive fact is that
  `ingest_multistation.py` reads the SAME cached OrcaHello records the consistency study and the
  experiment already consume. So for cross-station consistency, the ingest adds ZERO new
  observations; post-ingest split-half reliability EQUALS the currently measured values.

So the ingest moves the gate that depends on TOTAL multi-station volume (the joint CV-skill) but does
NOT move the gate that depends on PER-STATION reproducibility (cross-station consistency).

### Projected cross-station consistency at 12 bins after the ingest

Because the ingest adds no new observations to the consistency analysis, the post-ingest numbers are
the currently measured 12-bin numbers from `level2_multistation.json` (consistency bar 0.5,
within-station split-half as the honest ceiling):

| kernel | 12-bin cross-station mean PSTH corr | split-half ceiling (dense stations) | verdict after ingest |
|---|---:|---|---|
| diel | 0.053 | haro 0.374, orcasound 0.426 (mean 0.074) | NOT cleared; noise-bound (ceiling < 0.5) |
| lunar | 0.126 | haro 0.652, andrews 0.793, orcasound 0.537 (mean 0.661) | reproducible WITHIN station (ceiling > 0.5) but cross-station divergent -> genuine heterogeneity, model with a station random effect, not a clean 0.5 pass |
| tide | 0.263 | haro 0.159, orcasound -0.486 (mean -0.022) | FLAGGED not-yet-reliable; unstable/negative split-half, anti-structure or phase-aliasing, not a volume problem |
| season | 0.702 | coverage-confounded (per-station coverage 0.42 to 1.0) | NOT creditable; cross-station corr is over the shared window only |

Answering the brief's specific questions:

- **Does diel/lunar clear after the ingest?** Honestly, no, not as a clean cross-station 0.5 pass.
  RE's headline gain (diel split-half 0.08 at 24 bins -> 0.42 at 12 bins; lunar over 0.5 at 12 bins)
  comes from the SCORING-RESOLUTION change (coarser bins, already applied in the W4 re-score), NOT
  from the ingest's counts. After moving to 12 bins, the WITHIN-station split-half ceiling clears 0.5
  for lunar on the dense stations (haro 0.65, andrews 0.79, orcasound 0.54), so lunar is reproducible
  within a station; but the cross-station MEAN correlation is still 0.126, i.e. the stations disagree
  (genuine heterogeneity). Diel's within-station ceiling is still below 0.5 (mean 0.074), so diel
  remains a sparse-count noise artifact. The ingest does not change either, because it adds no
  observations to this analysis.
- **Is tide flagged?** Yes. Tide stays flagged not-yet-reliable: split-half is unstable and goes
  negative at finer/coarser bins (orcasound -0.486 at 12 bins), consistent with anti-structure or
  phase-aliasing, which more data does not fix.

### Residual uncertainty

- The net-new framing is settled by G1: today's ingest writes the cached records into the served
  store (+1328 served, 0 net-new to the consistency analysis), so it lifts the served CV-skill gate
  but not the cross-station consistency gate. The remaining uncertainty is forward: future
  accumulation after the ingest lands (new live detections over time) is what would move per-station
  reliability along RE's curve, and only for the densest nodes over years.
- N* extrapolations (RE) are saturating-model fits far beyond the observed range (max 1029 per
  station), and the two dense stations disagree by ~2x, so per-kernel N* is order-of-magnitude.
- Burstiness deflates effective independent N below raw counts (63 to 91% of detections within 6 min
  of the prior), so the consistency volume bar is HARDER than raw N* implies.
- Cross-station consistency is NOT a confidence-map input today (the supervisor reads CV + PIT +
  confidence, not the cross-station block). It is an L2 quality blocker the campaign tracks, but the
  W7 promotion arithmetic turns on served CV-skill, PIT, and the P0 map, not on the 0.5 consistency
  bar. This separation is why the ingest can lift confidence to 0.49 while consistency stays unmet.

---

## 5. Go/no-go template for W7

W7 launches only when W6 is done (3-node ingest landed) AND this G2 doc passes AND a SERVED refit has
been scored under the current P0 map. The promotion itself is supervisor-gated and operator-finalized
(B.1).

```
W7 PROMOTE multi-station -- go/no-go
Date: ____  Operator: ____  Served refit run id: ____

PRECONDITIONS (all must be true)
[ ] W6 ingest landed: 4 stations in the SERVED acoustic_detections store (B.4 bucket).
[ ] Served refit run under .venv-modeling, ORCAST_STORAGE_BACKEND=aws, B.4 bucket,
    write_outputs=False, _maybe_write_s3 disabled (B.5). No production / model-bucket write.
[ ] mlops-gate green; honesty guard consistent with the served confidence about to be recorded.

MEASURED (from the served report, not the experiment)
  cv.mean_deviance_skill = ______   folds n_pass/n_folds = ___/5   lower bound (mean - t*SE) = ______
  pit.calibrated = ______ (ks_pval ______)
  level1 diel beats null = ______
  P0-map confidence = ______
  supervisor draft = ______ (promotion/supervisor.py deterministic)

ROBUST-SKILL CHECK (section 1B)
[ ] margin: cv skill >= +0.144            -> ______
[ ] fold stability: n_pass/n_folds >= 0.8 -> ______
[ ] variance: lower bound >= +0.078       -> ______
[ ] PIT calibrated                        -> ______
[ ] Level-1 null beaten                   -> ______

DECISION GATES
  CASE 1  served skill >= +0.144, all robust-skill checks pass, confidence >= 0.6, cv+pit pass:
          -> GO. Supervisor recommends PROMOTE. Operator records the B.1 PROMOTE decision in
             DECISION_RECORD.md; effective_confidence set to the served confidence value.

  CASE 2  ingest yields ~+0.078 -> confidence 0.49 (HOLD), cv+pit pass but confidence < 0.6:
          -> THE EXPLICIT W7 DECISION. The supervisor recommends HOLD. Options:
             (a) WAIT for more skill: keep effective_confidence at 0.0, continue forward
                 accumulation / methodology work until served skill reaches ~+0.144. Default,
                 most honest. The display stays at 0.0 with the gate caveat (B.1).
             (b) ACCEPT a sub-0.6 served display: the operator records an explicit B.1 decision to
                 show the sub-0.6 served confidence (e.g. 0.49) WITH the "held-out positive but
                 below promotion threshold; cross-station consistency unmet; event-level timing
                 withheld" caveat. This is an operator display choice, NOT an automatic promotion,
                 and must never render sharper than the gates support (B.1). Recommended only if the
                 product needs to move off 0.0 and the caveat is shown prominently.
          -> RECOMMENDATION: default to (a) WAIT unless the operator explicitly opts into (b) with
             the caveat. Either way, do not let confidence exceed what the served gates earned.

  CASE 3  served skill <= 0 (the ingest does not flip served skill positive, or it regresses):
          -> NO-GO. Confidence stays 0.0 (hard floor). Investigate why the served single-provenance
             fit differs from the +0.078 mixed-provenance experiment before any further W7 attempt.

RESIDUAL RISKS TO STATE ON THE RECORD
[ ] Served vs experiment provenance gap (single-source store may shift skill vs the +0.078 memory mix).
[ ] Cross-station consistency still unmet (diel noise-bound, tide flagged, lunar heterogeneous,
    season coverage-confounded) -- an L2 quality caveat even on a promote.
[ ] Event-level time-rescaling WITHHELD (Hawkes self-excitation); the timing credit rests on the
    adopted bin-level gate (recorded supervisor decision, DECISION_RECORD sec 4), not Exp(1).
[ ] The 0.75 cap means even a strong served fit never expresses full certainty (honest by design).
```

---

## Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/forward/G2_promotion_protocol.md`.
- **Robust-skill definition + 0.6 requirement:** two bands. (A) "lifts served confidence / HOLD":
  served `cv.mean_deviance_skill > 0` with >= 4/5 folds positive maps to `0 < conf < 0.6` (e.g.
  +0.078 -> 0.49); supervisor recommends HOLD, no auto-promotion. (B) "robustly positive / promotes":
  served `cv.mean_deviance_skill >= +0.144` (the verified P0 0.6-crossing) AND >= 4/5 folds positive
  AND across-fold lower bound `mean - t*SE >= +0.078` AND PIT calibrated AND a beaten Level-1 null;
  this yields `confidence >= 0.6` with `cv_gate_pass` and `pit_calibrated`, so the supervisor
  recommends PROMOTE, finalized by a recorded B.1 human decision. The ingest alone (~+0.078 -> 0.49)
  does NOT promote.
- **Projection:** the ingest is net-new to the SERVED fit (1 station -> 4, ~761 -> ~2089, flips
  served skill toward +0.078 -> conf 0.49) but net-new ZERO to the cross-station consistency analysis
  (RE: same cached records). At 12 bins: diel does not clear (within-station ceiling 0.074), lunar is
  within-station reproducible (ceiling 0.66) but cross-station divergent (genuine heterogeneity),
  tide stays FLAGGED (unstable/negative split-half), season coverage-confounded. Consistency gains
  come from the coarser-bin re-score, not the ingest. G1 confirms the +1328 served / 0 analysis
  net-new split; residual is forward accumulation over years, dense nodes only.
- **Go/no-go template:** section 5, with the explicit Case 2 (+0.078 -> 0.49 HOLD: default WAIT for
  more skill to ~+0.144, or the operator explicitly accepts a sub-0.6 caveated served display; never
  an automatic promotion).
- No refit run, no production/model-bucket write, no promotion, nothing committed. Effective
  confidence stays 0.0.

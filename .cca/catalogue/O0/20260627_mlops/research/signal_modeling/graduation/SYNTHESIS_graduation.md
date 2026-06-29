# SYNTHESIS -- graduation waveset (what the TA/TB prototype-and-measure lanes actually returned)

Orchestrator synthesis, 2026-06-27 (America/New_York). Inputs: the 10 TA/TB lane docs + the 3 DE
registers in this directory. Authority above: SYNTHESIS_signal_modeling.md (the pre-execution ranked
plan), HANDOFF_CHARTER.md section B, G2 promotion protocol (the +0.144 fold-stable bar).

This doc records MEASURED outcomes. Nothing here promotes; effective confidence stays 0.0. Every number
below is held-out 5-fold `block_cv` mean-deviance-skill on the **experiment store** (4 stations / 2089
detections / ~300 effective onsets) unless marked otherwise; the **served** single-station and
post-ingest served 4-station fits are a separate, still-NOT-MEASURED gate before any promotion.

## 1. The headline: the two SYN flagships both fell; one sleeper cleared the bar

The pre-execution SYN named two flagships -- **A1 the 2-state MMPP** (cheapest gate-relevant model)
and **B1 Port Townsend + Bush Point** (cheapest new-observation lever). Measurement overturned both,
and the strongest result came from a lane SYN had labeled "small":

- **TA1 MMPP -- NO-GO.** The apparent +0.137 is `baseline_GLM x a single per-fold constant (~0.70)`:
  zero occupancy/shape content, and it breaks PIT calibration (KS p=4.4e-05). Decisively, the
  occupancy chain does **not** repair the event-level time-rescaling GOF (oracle smoothed-posterior
  intensity still leaves pooled KS p=0.0) -- the failure is sub-hour within-encounter chatter an
  hourly state cannot model. SYN A1 is superseded by measurement.
- **TB1 Port Townsend + Bush Point -- 25 net-new region presence-days, but 0 in summer.** The binding
  L3 lever is *summer* presence-days, so PT/BP add nothing to the summer-conditioned +0.144 gate.
  CONDITIONAL GO as off-season coverage; NO-GO as a summer lever on today's model. SYN B1's "cheapest
  +0.144 lever" framing is superseded -- the seasonal caveat S1's "GO" lacked.
- **TA5 smoothness shape prior -- GO, the strongest single lever measured: +0.177 (5/5 folds positive,
  across-fold lower bound +0.111, PIT calibrated), kernel-curve across-fold SD cut ~12-19x.** A hard
  `n_harmonics=1` control reaches only +0.084, proving the gain is graded shrinkage of the whole kernel
  shape, not fewer harmonics. This clears +0.144 ON THE EXPERIMENT STORE. It is NOT-MEASURED on the
  served store -- that re-measurement under the served gate is the load-bearing next step before any
  promotion conversation.

## 2. Full lane ledger

| Lane | Graduate (SYN) | Measured | Verdict | What it actually is |
|---|---|---|---|---|
| TA1 | 2-state occupancy MMPP | marginal +0.137 but artifact; PIT fails; GOF not repaired | **NO-GO** | scoring-family re-leveling, not skill; keep at most as an optional GOF diagnostic beside Hawkes |
| TA2 | hierarchical/partial-pooling NB + presence reframe | +0.047 (4/5, LB -0.048); presence reframe ~0 skill but calibrated; pooling 0.07-0.24 | **NO-GO standalone / GO as enabler** | fold-stability + calibration insurance that de-risks Tier B (cures station-held-out extrapolation), not a skill lever |
| TA3 | AIS effort/noise term in `log E` | baseline +0.078 reproduced; `log E` currently FLAT; AIS delta NOT-MEASURED (fetch infeasible in env) | **GO conditional (de-bias wire)** | B.2-correct effort offset; first real effort structure; expected ~ -0.01..+0.03, value is cleaner `k_diel`/`k_season` + fold stability, not +0.144 alone |
| TA4 | in-repo F1 (lunar x diel) + A1 (slack/max-flow) | F1 -0.0095, A1 -0.0054, both worse than the +1-harmonic control -0.0038 | **NO-GO** | pure df cost; no squeezed nonlinearity survives CV |
| TA5 | physics shape priors on existing kernels | **+0.177 (5/5, LB +0.111), PIT ok, curve SD cut ~12-19x**; control +0.084 | **GO (strongest lever)** | graded smoothness shrinkage = variance reducer; experiment-store only, served-store NOT-MEASURED |
| TB1 | Port Townsend + Bush Point (OrcaHello) | 25 net-new region presence-days, **0 summer**; Bush Pt stream stops 2024-11-02 | **CONDITIONAL GO (off-season) / NO-GO (summer lever)** | real off-season mass; needs a model that can use off-season/multi-region mass (e.g. TA2) to matter |
| TB2 | SST-front gradient (MUR/VIIRS), season-orthogonalized | probe: |grad SST| 0.013-0.074 C/km, CV~0.60, partly season-decoupled; CV-skill NOT-MEASURED | **GO conditional** | expected ~+0.01..+0.03; needs estimator support for an aperiodic per-fold season-orthogonalized covariate (currently Fourier-only) |
| TB3 | real Albion feed refresh + run-anomaly (D1) | runbook + anomaly recipe; expected +0.02..+0.08 NOT-MEASURED | **SUPPORTING-ONLY / WITHHELD** | feed already real (G3); L3 stays WITHHELD; not the lever, just housekeeping for a future summer OOS test |
| TB4 | ONC / JASCO Boundary Pass (ECHO published) | extraction FEASIBLE; **summer coverage YES (JJA 2016+2017, continuous ULS)**; disjoint 2015-2019 epoch; SRKW count ESTIMATED-positive NOT-MEASURED | **GO conditional (the real new-observation lever)** | independent operator/detector/corridor + a real summer window in a prime corridor; the thing TB1 was supposed to be |
| TB5 | SalishSeaCast subtidal currents + shear | conditional payoff damped/near-zero at 4-clustered geometry; NOT-MEASURED | **NO-GO at current N / conditional GO behind nodes** | spatial-front signal unobservable across one ~8x9 km cluster; refinement, not a primary lever |

## 3. What measurement changed vs SYN

1. **The cheapest gate-relevant model is not the MMPP -- it's the smoothness prior (TA5).** TA1 is an
   artifact and does not fix the GOF it targeted. TA5 is the single lever that cleared +0.144 on the
   experiment store, and it is cheap and low-risk (a penalty on existing kernels, default byte-identical).
2. **The new-observation lever is TB4 (ONC Boundary Pass), not TB1.** TB1 adds real mass but 0 summer
   days; TB4 has a real continuous summer window (JJA 2016+2017) in a prime SRKW corridor, an
   independent operator/detector, and a disjoint epoch -- exactly the "genuinely new summer
   presence-days" the +0.144 gap needs. Its summer SRKW count is the next thing to measure.
3. **TA2 + TA3 are insurance, not skill.** Partial pooling (TA2) cures station-held-out extrapolation
   fragility; the AIS/effort wire (TA3) de-biases the currently-flat `log E`. Both should land BEFORE
   judging any covariate (TB2/TB3/TB5) so covariates are scored against a clean, fold-stable baseline.
4. **The dead-ends held.** TA4 (in-repo nonlinearities), TB5 (currents at current N), TB3 (feed as a
   lever), and -- from the drift-guard -- LGCP/GP, ZI/hurdle-count, CUTI/BEUTI, HF-radar, terrain-on-gate
   all stayed NO-GO under measurement. No drift-guard violation occurred in any lane.

## 4. Recommended sequencing toward a served +0.144 (all operator-gated; nothing here promotes)

The honest order, cheapest-and-most-load-bearing first:

1. **Re-measure TA5 on the SERVED store** (single-station + the post-ingest served 4-station fit) under
   the G2 gate. This is the one measured lever that cleared the bar; the experiment-store result must
   reproduce on served data before any promotion. Single-editor integrate of `estimator.py` +
   `fit_kernels.py` (patch-only, nested-CV lambda, default byte-identical) is the gate-step.
2. **Land TA2 + TA3 as the clean baseline** (fold-stability + a non-flat `log E`), so subsequent
   covariate judgments are honest. Neither promotes by itself.
3. **Measure the TB4 summer SRKW presence-day count** (parse the published ECHO `Annotations.csv` UTC
   column; reconstruct ULS effort). If it is materially positive, TB4 is the new-observation graduate to
   ground (operator-gated ingest + the cross-station-consistency + disjoint-epoch handling).
4. **Then, and only then, re-judge the conditional covariates** (TB2 SST-front; TB5 currents once nodes
   are spatially separated) against the clean baseline. TB3 stays supporting; L3 stays WITHHELD.

## 5. Drift remediations still outstanding (from DE, recommended-not-applied)

The graduation lanes' patch-specs carry DE drift notes, but the source-doc fixes themselves are still
unapplied (separate operator-gated edit step): supersede M2's LGCP "GO" + (now) M2/SYN's MMPP "rank 1"
and "small" shape-prior magnitude; fix `wave_shape.yml` `signal_modeling_research` objectives; mark
CUTI/BEUTI WITHHELD + the L3-presence-days reframe across the mlops-handoff chain and
`ORCHESTRATOR_NOTES.md`. See DE1/DE2/DE3 registers for the line-level list.

## 6. Rails

Every lane confirmed: nothing deployed, fetched-to-write, ingested, promoted, or committed; no
convergence file edited; no served artifact / S3 write; `mlops-gate` ALL PASS at served_confidence 0.0.
Effective confidence stays **0.0**. Integrate / production fetch / region expansion / promotion all
remain separate operator gates.

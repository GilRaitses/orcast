# Forward-path campaign dispatch (W5 grounding agents)

Canonical prose: `CAMPAIGN_CHARTER.md`. These are the self-contained prompts for the W5 research /
grounding wave. Three agents run in parallel; each owns ONE grounding doc under
`.cca/catalogue/O0/20260627_mlops/research/forward/` and edits no other file. None deploys, refits to
a production write, promotes confidence, or commits (B.1/B.5/B.6/B.10). External feeds via aimez EC2
`i-04a649f91274e9fce`.

Shared context every agent must read first:
- `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (locked decisions)
- `.cca/catalogue/O0/20260627_mlops/CAMPAIGN_CHARTER.md` (this campaign)
- `.cca/catalogue/O0/20260627_mlops/DECISION_RECORD.md` (esp. sec 4: adopted bin-level timing gate)
- `.cca/catalogue/O0/20260627_mlops/research/SYNTHESIS_L2_L3.md` (corrected blocker map)

Repo: `/Users/gilraitses/orcast`. Reads only; create exactly one doc; no convergence-file edits.

---

## G1 -- ingest-deploy grounding (grounds W6 / O1)

You are the ingest-deploy grounding agent. Produce `research/forward/G1_ingest_deploy.md`. Do NOT
deploy or write to any production store; reads + dry-run only.

Read `src/aws_backend/ingest_multistation.py` (dry-run validated) and `src/aws_backend/ingest_timeseries.py`
(`ingest_acoustic_reviewed_outcomes`, `_put_grouped_by_station`, grouping by `record["station"]`), plus
how OrcaHello reviewed-outcome endpoints + the cached indexes are used (OrcaHello 403s; `fetch_history`
is oldest-first).

Deliver:
1. **Production deploy runbook** to land orcasound_lab / andrews_bay / north_san_juan_channel into the
   SERVED `acoustic_detections` stream (bucket B.4): idempotency + dedup key (station+window), backfill
   window + oldest-first handling, partition/schema, rate-limit + 403 retry/backoff, cost estimate,
   observability (counts per station, gaps), and an explicit ROLLBACK procedure.
2. **Pre-deploy gate checklist** (what must be true before the operator approves the write).
3. **Net-new-detection estimate**: how many NEW served detections each node adds beyond the cached
   index (this is what actually moves served CV-skill; RE showed re-using the cached index adds 0
   observations). State the assumptions and the expected served n per station.
4. **Go/no-go** for W6 with the residual risks.

Return: the doc path, the runbook summary, the net-new estimate, and the go/no-go. No write, no commit.

---

## G2 -- promotion-protocol grounding (grounds W7 / O3)

You are the promotion-protocol grounding agent. Produce `research/forward/G2_promotion_protocol.md`.
Analysis + spec only; do NOT run a refit that writes anything; no promotion.

Read `modeling/fit_kernels.py` (`_confidence_from_gates`, `_bin_level_timing_gate`,
`ADOPT_BIN_LEVEL_TIMING_GATE=True`, `_maybe_write_s3`, `write_outputs`), `modeling/studies/level2_multistation.py`
(the 4-station memory-store reproduction; sets `fk._maybe_write_s3 = lambda: None`, `write_outputs=False`),
and `src/aws_backend/promotion/supervisor.py` (deterministic rule: promote iff confidence >= 0.6 AND
cv_gate_pass AND pit_calibrated). NOTE: a P0 confidence-cliff fix to `_confidence_from_gates` may be
in flight; read the CURRENT file and design against whatever mapping is present (state which you saw).

Deliver:
1. **"Robustly positive" definition** for the served held-out CV mean-deviance-skill that should be
   allowed to promote: fold count/scheme, a stability/variance bound, and a minimum margin (so a
   single lucky fold cannot trip it). Justify with the existing CV machinery.
2. **Multi-station SERVED refit reproduction spec**: exact env (`.venv-modeling`), S3 bucket (B.4),
   `ORCAST_STORAGE_BACKEND=aws`, upload disabled + `write_outputs=False`, and how the served fit
   becomes 4-station once W6 lands (vs the memory-store experiment).
3. **Decision-record format**: the exact `promotion/supervisor.py` recommendation this would generate,
   and the human record that finalizes it (B.1), including how it composes with the P0 confidence map
   (where does it cross 0.6).
4. **Consistency-after-ingest projection**: using RE's reliability-vs-N curve + G1's net-new estimate,
   project cross-station consistency at 12 bins after the ingest (will diel/lunar clear 0.5; tide
   stays flagged). State the residual uncertainty.
5. **Go/no-go template** for W7.

Return: the doc path, the robust-skill definition, the projection, and the go/no-go template. No write,
no commit.

---

## G3 -- L3 grounding (grounds W8 / O4)

You are the L3 grounding agent. Produce `research/forward/G3_l3_grounding.md`. No promotion; L3 stays
WITHHELD.

Read `modeling/studies/salmon_lag.py` (full-span + the pre-registered Jun-Sep summer scan + held-out
year + `_STOCK_ALIGNED_SOURCES` + `real_feed_only`), `src/aws_backend/sources/salmon.py`
(`_fetch_fraser`/Albion cached loader, `_load_albion_fos`), `.cca/catalogue/O0/20260627_mlops/WIRING-salmon-albion.md`,
and `research/L3_conditioning.md` (RB). Current L3 state: full-span p=0.394; pre-registered Jun-Sep
in-sample r=0.251 p=0.013; held-out 2021 OOS r=0.390 p=0.027 -> FLAGGED-FOR-DECISION; LOYO only 2/5
years clear; 5-9 presence-days/yr.

Deliver:
1. **Live 2026 Albion fetch design**: extend the WIRING recipe to keep the series current via the
   aimez EC2 (provenance, refresh cadence, parsing, cache path `data/salmon/albion_fos/`).
2. **Power analysis**: how many more Jun-Sep presence-years (and presence-days/yr) are needed for the
   pre-registered held-out test to be robust given the current effect size and small n; quantify the
   multiplicity correction.
3. **Decision bar**: the explicit out-of-sample criterion the L3 flag must clear to graduate from
   FLAGGED-FOR-DECISION to an operator promotion decision (e.g. k-of-n LOYO, Bonferroni-adjusted p),
   and what keeps it WITHHELD otherwise.
4. **Go/no-go** for W8 (pursue the longer series vs accept WITHHELD).

Return: the doc path, the fetch design, the power-analysis numbers, the decision bar, and the go/no-go.
No promotion, no commit.

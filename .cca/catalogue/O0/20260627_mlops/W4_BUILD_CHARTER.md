# W4 build wave charter (graduate the research findings)

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (MLM + MLO)
Home: `.cca/catalogue/O0/20260627_mlops/`
Authority above this doc: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
Inputs: the research wave findings under `research/` (RA-RF) and `research/SYNTHESIS_L2_L3.md`.

W4 is the build/integrate wave that graduates the three research findings RF ranked as worth
building. It is the next execution wave after W1 (de-risk), W2 (integrate), W3 (L3 real feed). It
applies the two UNGATED methodology improvements and writes (but does NOT adopt) the one
confidence-bearing gate change, which is operator/supervisor-gated.

## A. What graduates (from research/SYNTHESIS_L2_L3.md)

1. (UNGATED) Cross-station consistency re-score (RE + RB). Re-score the L1 reproducibility criterion
   at 8-12 PSTH bins with a minimum per-bin count + partial pooling + burst-dedup to encounter
   onsets, reporting within-station split-half reliability as the ceiling. Measured payoff: diel
   split-half 0.08 -> 0.42 at 12 bins, lunar clears 0.5 at current volume on both dense stations;
   tide stays unstable (keep it flagged). This corrects an over-fine 24-bin scoring artifact; it does
   NOT by itself promote confidence.
2. (UNGATED) Pre-registered SRKW-summer L3 conditioning (RB + RA). Add a pre-registered,
   summer-conditioned (Jun-Sep, lag sign fixed) salmon lag scan with a held-out year, on the real
   Albion feed. Measured: Jun-Sep r=0.251, p=0.013 (exploratory). L3 stays WITHHELD until it holds
   out of sample; this only makes the test honest and pre-registered, it does not pass L3.
3. (OPERATOR/SUPERVISOR-GATED) Bin-level timing-gate redefinition + Hawkes diagnostic (RD). Add a
   self-exciting (Hawkes) event-level GOF diagnostic and a BIN-LEVEL timing gate (held-out NB PIT
   calibrated AND CV mean-deviance-skill > climatology) as an alternative to event-level Exp(1)
   time-rescaling, which cannot pass on a detector-chatter stream (branching ratio 0.79-0.96). This
   is the one change that could make the L2 timing gate PASS, so adopting it is a recorded supervisor
   decision (B.1), not an automatic effect. W4 writes and validates the diagnostic + the gate
   definition, but the gate adoption and any resulting `effective_confidence` change are gated.

Dead-ends (do NOT build): RA counts response variable, RC temperature animal kernel + diel-for-L3.

## B. Locked constraints (HANDOFF_CHARTER section B; unchanged)

- B.1 No confidence promotion without a passing gate + a recorded supervisor decision. Item 3 is
  exactly the confidence-bearing change; it is gated and must not auto-promote.
- B.5 Any refit sets `fk._maybe_write_s3 = lambda: None` and `write_outputs=False`; no production
  store/model-bucket write.
- B.6 The `modeling/` fit pipeline is local-only/untracked; only `modeling/studies/**` + reports and
  `tide_harmonic.py` are tracked. The honesty guard / gate definition lives in the local
  `fit_kernels.py`.
- B.8 `tools/waves/run-gate.sh mlops-gate` must stay green and honest (served confidence must not
  exceed earned) after every change.
- B.10 No commit/push without an explicit operator ask; surgical staging.

## C. Execution model (single convergence-file editor per file)

Convergence files and their SINGLE W4 editor:
- `modeling/fit_kernels.py` (local-only) + `modeling/studies/cross_station_consistency.py` (tracked):
  the MODELING INTEGRATOR. Owns item 1 (apply) and item 3 (write the Hawkes diagnostic + the
  bin-level gate definition behind an explicit, default-OFF flag; do NOT flip the gate / promote).
- `modeling/studies/salmon_lag.py` (tracked): the STUDY INTEGRATOR. Owns item 2 (pre-registered
  summer-conditioned scan + held-out year).

Items 1 and 3 share `fit_kernels.py`, so they have ONE editor (the modeling integrator), sequentially
within that agent. Item 2 is a disjoint file, so the study integrator runs in parallel. No other file
is edited by two agents. Validate with the stdlib gate + a single local memory-store refit (upload
disabled, `write_outputs=False`); no concurrent heavy fit; no production write; no agent commits.

## D. Gates

- W4 exit (UNGATED part): item 1 + item 2 landed; `mlops-gate` green; served confidence still 0.0
  (items 1-2 do not promote); the bin-level gate (item 3) is present but OFF.
- Confidence gate (item 3 adoption): a recorded supervisor decision via
  `src/aws_backend/promotion/supervisor.py` after the bin-level timing gate is reviewed (methodology
  change framed honestly: "event-level Exp(1) is inappropriate for a detector-chatter stream", paired
  with the non-automatic CV-skill criterion). Until then, `effective_confidence` stays 0%.
- Any commit/push: explicit operator ask (B.10).

## E. Return contract

Each integrator returns the diffs/specs, the measured before/after numbers (consistency split-half;
the summer-conditioned held-out L3 verdict; the bin-level gate state with confidence held at 0.0),
the `mlops-gate` result, and risks. No commit. The orchestrator does one integration step at wave
end (commit only on an explicit operator ask) and prepares the supervisor-decision packet for item 3.

## F. Status

CHARTERED. Dispatch in `W4_BUILD_DISPATCH.md`. Not launched; launch is the next operator gate.

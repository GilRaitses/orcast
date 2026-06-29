# OS2 W1 dispatch, effort/detectability frame (read-only measurement)

Lane O0, Open-Science Integration. Wave W1 of `OS2_BUILD_CHARTER.md`. Operator confirmed OS1 close + OS2
pickup; W1 (effort-measured-first) is launched, W2 (region expansion + ingest) is HELD for a separate go.
This wave MEASURES only: no region-box edit, no ingest, no `modeling/**` or `src/aws_backend/**` edit, no
store/S3 write, no fetch-to-store, no deploy, no promotion, no commit/`git add`. One findings doc + one
STEP_LOG line. Effective confidence 0.0.

## Goal

Produce a defensible per-(node, day) `log E` effort frame for the OS2 net-new summer nodes, so a later
W2/W3 can put their presence-days on the same footing as the served stations. Without this, no rate or
skill is honest. Primary node: **Tekteksen / SIMRES Boundary Pass (Saturna Island, BC)**; optional second:
**CarmanahPt / DFO (W Juan de Fuca)**.

## The key lever for the primary node

The OSF `6ctjq` propagation-loss + ambient calibration site is **East Point, Saturna Island** — the SAME
Boundary Pass location as the SIMRES Tekteksen deployment. So the banked OS1 detection-range calculator
(`data/external/osf_6ctjq/validate_detection_range.py`, VALIDATED) applies to Tekteksen DIRECTLY using the
East Point PL coefficients, NOT as a cross-site geoacoustic transfer. This is the structural reason OS1's
NO-GO does not carry over: detectability here is computed at its own calibrated site.

## Deliverables (findings doc `OS2_W1_effort_frame.md`)

1. **Uptime / duty cycle.** From SIMRES / JASCO deployment metadata (recording schedule, hydrophone
   on/off duty, gaps) for the 2022 Tekteksen deployment covering the 11 JJA-2022 presence-days and the
   surrounding effort window. Report MEASURED vs ESTIMATED per field; if duty cycle is not publicly
   recoverable, say so and bound it (do not fabricate a number). Same for CarmanahPt if attempted.
2. **Per-node detectability.** Run the banked OS1 calculator with the East Point PL coefficients +
   East Point ambient (from OSF `6ctjq`) to get the Tekteksen detection range/area, and convert to a
   per-day (or per-deployment-median) detectability term. Note the calibration is native here, not a
   transfer. Use the OS1 robustness guards (smooth-in-frequency, R_max clamp, winsorize) as a starting
   point and report whether they bind at this site.
3. **Combined `log E` per (node, day).** uptime x detectability, on the same `log E` scale as the served
   `exposure`. Report the distribution and whether it is defensible (no unphysical tails).
4. **Gate verdict to W2.** Is the effort frame defensible per node (GO to W2) or not (HOLD)? State the
   single blocker if HOLD.

## Rails / honesty

Presence-days are the deliverable; NO CV-skill credit is claimed in W1. Read-only research (web, repo,
`/tmp` scratch, gitignored `data/external/**`) + bounded local compute only. The DCLDE annotations are
already cached read-only at `/tmp/orcast_tb4/Annotations.csv` (re-use, do not re-fetch to store). Tag every
number MEASURED / ESTIMATED / NOT-MEASURED. Do not estimate a duty cycle you cannot defend. No region
expansion, no ingest, no convergence-file edit, no store write, no deploy, no promotion, no commit.

## Return

Write `OS2_W1_effort_frame.md` in `.cca/catalogue/O0/20260627_open-science-integration/` and append one
STEP_LOG line. Return: the per-node effort-frame summary, MEASURED/ESTIMATED status of duty cycle, the
detectability numbers, the combined `log E` distribution, and the GO/HOLD-to-W2 verdict with any single
blocker. STOP after the doc; do not start W2.

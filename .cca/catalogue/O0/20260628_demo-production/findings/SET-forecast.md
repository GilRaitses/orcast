# SET-forecast

Status: READY

Prerequisite: live forecast + gates respond with the honest 0% promoted and
integrity conditions, serving A1, A4.

## Read-examined check

Browser-rendered `/gates` (viewId adb6a4), main text read via CDP:

```
Fitness gates
Status: fitted · confidence 0% · promoted

Integrity conditions for this fit
  Single station
  Effort assumed continuous (not effort-corrected)
  Spike-train fit uses unreviewed acoustic candidates; Level 0 QC reports reviewed outcome mix separately.
  Season kernel extrapolated beyond observed coverage (partial annual cycle)
  In-sample event-timing goodness-of-fit (time-rescaling) still fails; calibration is assessed via held-out PIT.
  Mean held-out deviance skill is negative; fold-majority CV pass should be treated cautiously.

McFadden pseudo-R² vs climatology: 0.045 · covariates: diel, lunar
Acoustic: 761 detections, 1 station(s).
Evidence chain: Fit repr_46c561feb18ef281 -> gates run_fb8f0acab5bd91ee -> decision decision_b35d8103d4f4 -> promoted
Level 1: PSTH vs phase-shuffle null (diel/tide/lunar/season rows present; lunar+season beat null)
```

The honest "confidence 0% · promoted" renders verbatim with its gate caveat, the
integrity-conditions list renders, and the evidence chain back to the decision
record is present. This is the real promoted value, shown as 0%, not hidden or
rounded.

## Evidence

- Built surface: `web/app/gates/page.tsx`, backend `forecast`/`api/gates`
  (`GatesResponse` in `web/lib/api.ts`).
- The "0% promoted" string and integrity-conditions list observed in the rendered
  `/gates` frame.

## Ports / pids

None.

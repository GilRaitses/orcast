# Handoff charter, OS1 (open-science effort/detectability) + beyond

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `9a00e15`. All OS1 build artifacts are
gitignored/local-only; the OS catalogue docs are committed-or-uncommitted per §G. This charters a fresh
thread to take over the open-science effort/detectability lane (OS1) and decide its "beyond". Hydrate
from files, not from the chat transcript linearly.

## A. Purpose

OS1 asked: does a per-day acoustic DETECTABILITY term (how far an SRKW call carries given that day's
ambient noise), applied as an effort offset on the served kernel forecast, add genuine held-out skill?
The originating orchestrator built the full pipeline and MEASURED the answer on the dominant station:
NO-GO. This thread inherits a closed, measured OS1 and decides one of: confirm the NO-GO on the other
stations, try the one remaining variant (a fitted covariate / better ambient), reframe the term, or
formally CLOSE OS1 and bank its reusable physics for the spatially-separated nodes where detectability
actually varies (OS2 / TB). Nothing here promotes confidence.

## B. What is LOCKED / MEASURED (do not re-derive; restate in the ack)

1. **Calculator VALIDATED.** The detection-range physics (Mouy et al. 2025, PLoS One
   10.1371/journal.pone.0331942, Eq 1-5) is implemented and reproduces the paper's East Point summer
   ranges within ~5-15% (14,967 m low-noise / 1,425 m high-noise at 10 m vs paper ~15,500 / ~1,640). A
   sign bug (`-A` vs `+A` in Eq 4, ~9 dB) was found and fixed. TRUSTED and reusable.
   `data/external/osf_6ctjq/validate_detection_range.py`.
2. **DSP pipeline PROVEN.** OrcaSound audio is public on `s3://audio-orcasound-net/<node>/hls/<session>/
   live*.ts` for all 3 served nodes (~110 sessions/month across detection-heavy months 2020-2026).
   48 kHz AAC -> ffmpeg -> scipy Welch -> 46x300 Hz bands gives a physically correct ocean spectrum.
   `data/external/os1_ambient/extract_daily_ambient.py`. Extracted: orcasound_lab 2020-09..2021-09, 391
   days, 4 segments/day.
3. **ONC proxy is a DEAD END (data geometry, not license/token).** No ONC hydrophone at East Point or
   in Haro Strait; nearest continuous node (ECHO3, Strait of Georgia) is ~35-55 km away in a different
   sub-basin, raw audio only. The `ONC_API_TOKEN` in `.env` works but is unused. Do not re-investigate
   ONC ambient for the served cluster.
4. **OSF data license.** OSF node `6ctjq` (PL coeffs + ambient SPL) carries no license tag. Operator
   authorized INTERNAL-ONLY use ("assume license confirmation") to proceed. Do NOT redistribute or
   publish the raw OSF data or any derived artifact without author (X. Mouy) confirmation.
5. **OS1 served-skill verdict: NO-GO (measured).** With the robust offset (smooth-in-frequency + R_max
   clamp [500 m, 20 km] + winsorize +/-2), a kappa sweep on the offset scale shows the mean CV
   deviance-skill DECREASING monotonically: +0.2776 (baseline) -> +0.2608 (k=0.25) -> -0.1300 (k=1.0).
   No positive kappa beats the baseline mean (the load-bearing promotion metric). A small fold-unstable
   median wobble at k 0.1-0.25 does not move the mean. The detectability offset is NOT adopted.
6. **Honesty / no promotion.** Effective confidence is 0.0 and only rises on a passing gate + a recorded
   supervisor decision (`src/aws_backend/promotion/supervisor.py`). OS1 produced none; the +0.144 bar
   and `_confidence_from_gates` are unchanged. Sub-agents/threads deploy nothing, write to no production
   store, run no fit that writes, promote nothing, and COMMIT nothing without an explicit operator ask.
7. **Local-only / footguns.** The `modeling/` fit pipeline and `data/models/` are untracked; OS1
   artifacts live gitignored under `data/external/`. Heavy work uses system `python3` with
   `PYTHONPATH=/Users/gilraitses/orcast`. The served store is S3 bucket
   `198456344617-us-west-2-orcast-aws-backend-raw-payloads` (us-west-2); any S3 fit must disable the
   production upload. Never `git add -A`.

## C. The honest "why it failed" (so the next thread does not relitigate blindly)

- OrcaHello detections are SRKW calls typically well above ambient, so per-day noise may not gate the
  count the way an area-effort model assumes.
- East Point geoacoustic transfer is an approximation to orcasound_lab's true site.
- 4 segments/day make the daily ambient noisy; a noisy offset adds variance, not signal (23.5% of days
  hit the winsor bound).
- A fixed area->count multiplicative effort (coefficient pinned at 1) is stiff; the kappa sweep already
  approximated a fitted coefficient and found no mean gain.

## D. Scope for this thread: the "beyond" decision

Pick with the operator (the originating orchestrator's recommendation is to CLOSE, option 4):

1. **Other-station confirmation.** Extract andrews_bay + north_san_juan_channel ambient (same
   `extract_daily_ambient.py`) and re-measure. orcasound_lab dominates (1029/1359 detections), so this
   is unlikely to flip the verdict but makes it complete. Cost: ~1-2 h extraction each.
2. **Fitted covariate (not a fixed offset).** Let the GLM fit a detectability coefficient (adds 1
   parameter) with nested-CV selection, instead of a pinned offset. The kappa sweep is a coarse proxy
   and already shows no mean gain, so this likely confirms NO-GO; do it only if the operator wants the
   formal version. Cost: small.
3. **Better ambient + reframe.** Re-extract at more segments/day to cut noise, and/or reframe the term
   as a per-day detection-PROBABILITY weight on OrcaHello candidate confidence rather than an area
   effort. Higher cost, speculative.
4. **CLOSE OS1 as a measured NO-GO (recommended).** Bank the validated calculator + proven DSP pipeline
   for OS2 / TB spatially-separated nodes (where co-located ambient exists and detectability genuinely
   varies), and move the lane's energy to the higher-ranked OS graduates (see §E).

## E. Beyond OS1: the OS waveset graduates still open (context, not necessarily this thread)

From `OS_SYNTHESIS.md` (OS waveset is research-COMPLETE):
- **OS2 (recommended next open lever):** Tekteksen / SIMRES Boundary Pass = 11 MEASURED net-new JJA-2022
  SRKW presence-days (largest single net-new summer payload); DCLDE-2027 CC-BY-4.0 corpus ~26 net-new
  JJA days total. Gated on region expansion outside SAN_JUAN_BOUNDS + per-deployment effort.
- **OS3:** EFI metadata sidecar + report-only NB2-CRPS block (cheapest, no gate, in-repo no-op).
- **OS4:** inlabru NB cross-check (operator-gated on an R runtime; expected to reproduce, not beat).
- **OS5:** open detector (ANIMAL-SPOT/PAMGuard) independent L0 ROC (gated on weights/audio/compute).
- Dead-ends held: spatial LGCP at current N, DORI-ONC, OrcaSound re-shelving, CRPS/EFI/inlabru as skill
  levers, out-of-domain detector output as truth.

## F. Gate / metric state (one line)

Effective confidence 0.0 (unchanged). OS1 measured NO-GO on served skill (baseline mean +0.2776; no
positive offset kappa beats it). Forecast remains the existing kernel/heuristic with its honesty gate.

## G. Pending uncommitted local state

OS1 code + data are gitignored/local-only under `data/external/osf_6ctjq/` and `data/external/os1_ambient/`
(calculator, extractor, transducer, measurer, 391-day ambient JSON, anchor npy, result JSON). The OS
catalogue docs updated this step: `20260627_open-science-integration/OS1_BUILD_NOTE.md` and `STEP_LOG.md`.
This handoff home is new. `.env` holds `ONC_API_TOKEN` (gitignored; never commit). No commit without an
explicit operator ask; surgical staging only.

## H. Return contract (ack on first response)

Before acting, the new thread returns:
- Hydration confirmed + the files read.
- The locked/measured items (§B) restated in your own words, especially: calculator VALIDATED + DSP
  PROVEN (B.1/B.2), ONC proxy DEAD-END (B.3), OSF internal-only license (B.4), the OS1 NO-GO with the
  kappa-sweep evidence (B.5), no-promotion (B.6), and local-only/footguns (B.7).
- Gate state in one line (confidence 0.0; OS1 measured NO-GO).
- The "beyond" choice you propose (§D 1-4) and why, plus whether the operator wants OS2 picked up.
- One risk (e.g. re-running the same noisy ambient cannot move the mean; only a different framing or a
  genuinely co-located-ambient node could).

## I. Transcript / provenance pointer

Originating session:
`~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/1ec5be7f-9e23-43dd-9d24-0cb2c64a1926/1ec5be7f-9e23-43dd-9d24-0cb2c64a1926.jsonl`.
Search by keyword (OS1, detection range, OSF 6ctjq, OrcaSound DSP, transducer, kappa sweep, NO-GO),
do NOT read linearly. Lane home: `.cca/catalogue/O0/20260627_open-science-integration/`; the technical
provenance is in its `OS1_BUILD_NOTE.md` and `STEP_LOG.md`.

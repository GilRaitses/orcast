# PRF ADV-1 — O0 decision (vsync-uncap precondition unmet in headless)

- Lane `BSWR-PRF` (client-tier-frametime-verify). Decider: O0.
- Resolves the P0 `ADV-1` returned by `PRF-ADV_VERDICT.md` §1/§7.
- Repo base pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`. No commit.

## Context

PRF-ADV verified locally that the two vsync-uncap launch flags
(`--disable-gpu-vsync` / `--disable-frame-rate-limit`) do NOT break the ~60Hz
synthetic-compositor BeginFrame cadence in pure headless chromium, so the rAF
interval cannot resolve a sub-16.67 ms frame. This makes PRF-Q decision-2 as
literally written ("uncap the cap, then trust the rAF frame-time") unsatisfiable
in headless. PRF correctly paused rather than asserting a fabricated headroom
number, and returned three honest options.

## Decision

**Option 1 is adopted as the PRF verdict method: the vsync-quantised over-budget
oracle.** Rationale, grounded in PRF-ADV §2:

1. The charter's binding ask is the **30fps / 33.3 ms** budget, BSW-on vs BSW-off
   — i.e. catch a real miss. The rAF interval quantises to refresh multiples
   (~16.7 / 33.3 / 50 ms) and the over-budget probe proves the signal MOVES once a
   frame exceeds the vsync deadline (25 ms work → 33 ms bucket; 45 ms → 50 ms
   bucket). That is dispositive in the direction that matters.
2. The CPU-throttle lever still works on the real scene (a fixed AMOUNT of
   computation under 4x throttle takes ~4x longer and spills into the higher
   buckets); the busy-loop probe's null was a wall-clock probe artifact (ADV-2),
   not a harness defect.
3. Option 1 is free, needs no new method and no new gate, and stays inside the
   locked rAF-interval approach.

## Honesty conditions (hard, binding on the verdict wording)

- The verdict MUST state the reading is **vsync-quantised** and that it **cannot
  resolve sub-refresh headroom** (it cannot distinguish a 5 ms frame from a 16 ms
  frame; both read ~16.7 ms).
- A clamped ~16.7 ms median is reported as **"PASS 30fps with margin (true cost
  < one refresh)"**, NEVER as "the frame-time is 16.7 ms" — reporting a clamped
  value as the measured frame-time is the fabricated-headroom P0 from PRF-R4 and
  remains forbidden.
- A sustained cluster at ~33.3 ms reads "at/under the 30fps budget"; sustained
  ≥50 ms reads "FAIL 30fps, the miss is real".
- The existing emitted honesty string (emulated client tier is a LOWER BOUND; a
  pass does NOT certify the real client GPU) stays.

## Option 2 (host `--smoke`) — queued into the batched host window, confirmation only

The Linux/Xvfb/T4 host MAY make the flags genuinely uncap (ADV-3 is unconfirmed,
not closed). Authorize a single cheap `scripts/perf/client_tier_frametime.sh
--smoke` on the GPU box, to be run **inside the batched BSWR host window** (with
the OCN/ENV GPU captures and the PRF-ACCEPT A/B), NOT now and not standalone.
- If the host uncap genuinely free-runs, record the true sub-refresh numbers as a
  bonus and keep Option 1's 30fps verdict as the primary.
- If the host also clamps, Option 1 already stands; no fallback work.

## Option 3 (CDP frame tracing) — REJECTED for this lane

A real sub-refresh frame-COST meter via CDP Tracing is a methodology change beyond
the locked rAF-interval approach and is not needed for a 30fps pass/fail. Out of
scope; revisit only if a future objective needs true per-frame cost.

## What PRF does next (this resolves ADV-1)

1. Rewrite the PRF method + verdict framing to the Option-1 quantised-oracle
   wording above; close ADV-1 as an O0-accepted method (not a fabricated number).
2. Re-run the local over-budget / clamp probes only as needed to cite the
   quantised buckets; keep `subRefreshProven:false` honestly recorded.
3. Reach PRF build-complete (harness + driver + honest verdict wording), zero open
   P0/P1.
4. Stage PRF-ACCEPT: the paid host A/B (`client_tier_frametime.sh --ab`) PLUS the
   Option-2 `--smoke`, both for the batched host window. Do NOT run any host
   command. PAUSE to O0.

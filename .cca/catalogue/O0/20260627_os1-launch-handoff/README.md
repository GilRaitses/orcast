# OS1 launch handoff

Rotation package to hand the open-science effort/detectability lane (OS1) and its "beyond" to a fresh
orchestrator thread. OS1 was built and measured end-to-end in the originating session; the served-skill
verdict is a measured NO-GO. This package carries the full provenance so the next thread can decide the
"beyond" (confirm on other stations / fit a covariate / reframe / close + bank physics for OS2/TB)
without re-deriving anything.

## Read order

1. `HANDOFF_CHARTER.md` -- authority: locked/measured findings (§B), the "beyond" decision (§D), the
   ack (§H).
2. `HYDRATION_PACKET.md` -- ordered read list across the OS lane home + the OS1 code surface.
3. `ORCHESTRATOR_DISPATCH_PROMPT.md` -- paste block to launch the new thread.
4. `STEP_LOG.md` -- this rotation's trace.

## One-paragraph status

The detection-range calculator (Mouy et al. Eq 1-5) is validated against the paper; the OrcaSound S3 ->
ffmpeg -> Welch DSP pipeline is proven; orcasound_lab ambient is extracted for 391 days. The
detectability offset, made physically robust (smooth-in-frequency + R_max clamp + winsorize), does NOT
improve held-out CV mean-deviance-skill at any offset scale (kappa sweep: +0.2776 baseline -> -0.1300
full offset, monotonic), so OS1 is a measured NO-GO on served skill. The validated physics and DSP
pipeline are banked for future spatially-separated nodes with co-located ambient (OS2 / TB). Nothing
promoted; effective confidence 0.0. Lane home with full technical provenance:
`.cca/catalogue/O0/20260627_open-science-integration/` (`OS1_BUILD_NOTE.md`, `STEP_LOG.md`).

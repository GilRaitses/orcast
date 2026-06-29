# OS1 launch handoff step log

Lane O0. Effective confidence 0.0 throughout. Append one entry per handoff action.

- 2026-06-27: OS1 BUILD + MEASURE + ROTATION CHARTERED. The originating orchestrator built OS1
  end-to-end after the OS research waveset closed, then this step did the robustness fix + re-measure
  and packaged the rotation. Full technical provenance lives in
  `.cca/catalogue/O0/20260627_open-science-integration/OS1_BUILD_NOTE.md` and its `STEP_LOG.md`
  (last entry). Summary of what was done:
  - OSF `6ctjq` data fetched (PL coeffs + ambient SPL) to gitignored `data/external/osf_6ctjq/`;
    operator authorized internal-only use ("assume license confirmation").
  - Detection-range calculator built from Eq 1-5; sign bug (`-A` vs `+A` in Eq 4) found + fixed;
    VALIDATED vs the paper's East Point summer ranges within ~5-15%. TRUSTED.
  - ONC East Point ambient proxy REJECTED (no Haro-Strait hydrophone; nearest node 35-55 km away in a
    different basin, raw audio only). ONC token works but unused.
  - Pivoted to OrcaSound DSP: S3 audio -> ffmpeg -> Welch -> 46x300 Hz bands; pipeline proven; extracted
    orcasound_lab 2020-09..2021-09, 391 days.
  - Transducer (ambient -> log E_det) built; first measurement was a defect (std ~5, area swings 1e10x,
    CV mean blew up) from 4-seg/day band noise + uncapped R_max + max-over-bands.
  - ROBUSTNESS FIX: smooth-in-frequency (window 5) + R_max clamp [500 m, 20 km] + winsorize +/-2.
    std -> 1.50, physical range, median R_max 7.5 km.
  - RE-MEASURE with a kappa sweep: mean CV deviance-skill +0.2776 (baseline) -> +0.2608 (0.25) ->
    -0.1300 (1.0), monotonic decrease; no kappa beats baseline on the mean. VERDICT: NO-GO on served
    skill. Result saved to `data/external/os1_ambient/os1_skill_result.json`.
  - Rotation package written here (`HANDOFF_CHARTER`, `HYDRATION_PACKET`, `ORCHESTRATOR_DISPATCH_PROMPT`,
    `README`, this log) so the next thread can decide the "beyond" (other-station confirmation / fitted
    covariate / reframe / CLOSE + bank physics for OS2/TB). Recommendation: CLOSE OS1, move to OS2
    (Tekteksen/SIMRES, 11 net-new JJA days). Nothing promoted; +0.144 bar and `_confidence_from_gates`
    unchanged. No commit (awaiting operator ask). STOP for operator direction.

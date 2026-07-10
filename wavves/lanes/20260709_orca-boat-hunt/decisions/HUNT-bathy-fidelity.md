# HUNT — bathymetry seabed-clamp fidelity for HUNT-INT

- **Date:** 2026-07-09
- **Lane:** wavves/lanes/20260709_orca-boat-hunt
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5 (main, unchanged since charter; no commits made by this lane)
- **Question:** Should HUNT-INT wire the real `getSeabedClearanceM` probe (from the bathymetry tiles' `getSurfaceY`) into the pilot on the first integration pass, or ship with the already-implemented fixed 0-25m fallback depth band and revisit only if time remains before the July 10 event?
- **Options considered:**
  - A: Ship with the fixed 0-25m fallback band now (zero extra integration work; `orcaPilot/deadReckoning.ts` already implements this path and falls back automatically whenever `getSeabedClearanceM` is omitted or returns null).
  - B: Wire the real tiles `getSurfaceY` probe into HUNT-INT now, so dive depth is correctly clamped against the real bathymetry from the first pass.
- **Pick:** A (fallback_now).
- **Rationale:** Time budget ahead of the July 10 event; the fallback path is already implemented and functionally complete, real-probe wiring is deferred rather than dropped.
- **Implications for HUNT-INT:** HUNT-INT does NOT need to derive `getSeabedClearanceM` from `useTilesLayer`'s surface probe on this pass. `createOrcaPilot({ worldUnitsPerMeter: wupm })` is constructed WITHOUT `getSeabedClearanceM`, and the pilot uses its own `DEFAULT_MAX_DEPTH_M = 25` band automatically. If time remains after HUNT-ACCEPT, wiring the real probe is a candidate follow-up, not required for this lane's acceptance criteria.
- **Correction (HCHK-contradictions.md Finding 2, 2026-07-09):** the original rationale above incorrectly invoked "locked decision 8's flat-plane fallback language" to justify this pick. Decision 8's fallback is conditioned on the real bathymetry TILESET failing to mount; it does not license an unconditional fixed depth-clamp band once the tileset succeeds. Since HUNT-BATHY GO'd the real "full" tileset, the actual planned state is real bathymetry rendering with a flat 0-25m depth clamp that ignores it, which is a NEW, previously unnamed cosmetic risk: wherever the real seabed is shallower or deeper than the clamp assumes, the orca can visibly clip through or hover above rendered terrain. The PICK is unchanged (ship the fixed band now, time budget before the July 10 event); only the justification is corrected, and the new risk is named here rather than hidden behind a mis-applied decision 8 fallback.

# STRIKE — arcade control layout

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260710_orca-strike-game
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5
- **Question:** What is the desktop (and mobile-equivalent) control map for Orca
  Strike arcade play?
- **Operator pick (verbatim intent):**
  - **Q** — dive
  - **E** — surface / rise
  - **S** — backwards
  - **W** — forwards
  - **A** — roll left (in-place body roll, not strafe)
  - **D** — roll right
  - **Space** — breach charge (button-mash / mobile gesture); aerial tricks;
    slow-mo replay on landing; kayak over = high points; boat landing = win
  - **B** — fast tap charges blowhole; squirt water; squirting kayaks = high
    points
  - **O** — sonar ping using a **hydrophone annotation sample** (not silent
    radar-only UI)
  - **F** — retained from HUNT for radar HUD fill (unless superseded in INT)
  - **1–9** — teleport to sonar blip (HUNT carry-over)
- **Locked:** Implement via a **new** `web/lib/scene/orcaStrike/` input layer
  that maps to `OrcaPilotInput` + articulation state machine. Do **not** edit
  `web/lib/scene/orcaPilot/input.ts` (HUNT lock). Supersede
  `orcaStrikeInput.ts` depth remap with the full control map.
- **Mobile equivalents (locked defaults, refine in STRIKE-W2):**
  - Tilt steer/dive (existing) + on-screen breach mash zone + blowhole tap +
    sonar button.

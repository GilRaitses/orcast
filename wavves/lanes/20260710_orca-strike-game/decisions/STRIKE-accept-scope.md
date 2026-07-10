# STRIKE — lane ACCEPT scope

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260710_orca-strike-game
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5
- **Question:** Is W5 multiplayer required for STRIKE lane ACCEPT?
- **Options considered:**
  - A: ACCEPT at W4 (solo complete); W5 multiplayer is a follow-on lane
  - B: ACCEPT requires W5 (room codes + ghost orcas must ship)
- **Pick:** **A**
- **Rationale:** Operator pick. Bash.tv can ship playable solo first; PartyKit
  multiplayer is a second build pass after solo ACCEPT.
- **Implications for BUILD:**
  - `waveset.md` ACCEPT criteria: solo controls, FSM, scoring, breach,
    blowhole, O-sonar, lobby, spawn picker, standalone `(game)` shell on Bash.tv.
  - W5 is **out of ACCEPT scope**; charter a `STRIKE-MP` or extend lane when
    solo lands.
  - Dispatch W2–W4 now; do not block W2 on W5.

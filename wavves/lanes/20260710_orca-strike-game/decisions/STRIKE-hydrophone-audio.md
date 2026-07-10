# STRIKE — hydrophone audio delivery

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260710_orca-strike-game
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5
- **Question:** How do Bash.tv and clean-clone builds obtain the O-key hydrophone
  slice (`orcasound_lab_20210825_srkw.m4a`, gitignored)?
- **Options considered:**
  - A: Operator attaches m4a to Bash.tv agent once; agent places in
    `public/hydrophone/slice/`
  - B: Build prompt instructs agent to run
    `modeling/acoustic/fetch_orcasound_clip.py` per `PROVENANCE.md`
  - C: Both — attach primary; fetch script as documented fallback
- **Pick:** **C**
- **Rationale:** Operator pick. Attach is reliable on Bash.tv; provenance fetch
  covers orcast repo continuity and clean clones.
- **Implications for BUILD:**
  - Bash.tv build prompt must list attach step for the m4a **and** inline
    `PROVENANCE.md` fetch fallback.
  - `hydrophoneSonar.ts` loads `/hydrophone/slice/orcasound_lab_20210825_srkw.m4a`.
  - STRIKE-ACCEPT O-sonar check fails if file missing after both paths attempted.
  - `classification.json` is already committed; no attach needed for that file.

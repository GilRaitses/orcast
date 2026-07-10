# STRIKE — multiplayer and match format (phase gate)

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260710_orca-strike-game
- **Operator intent:** MMO-style swim with other orcas; Dodo-code-style room
  codes to invite friends to your island; timed rounds like Counter-Strike
  structure but **cooperative/high-score**, not orca-vs-orca combat.
- **Locked product shape:**
  1. **Lobby:** pick orca skin → pick spawn on context map (island sub-map).
  2. **Room code** (6-char, Dodo-style) creates/joins a session on one island
     instance.
  3. **Round:** fixed timer (default 180 s); team or solo score tally.
  4. **Scoring:** breach-over-kayak, blowhole-on-kayak, boat landing (instant
     round win), ram-sink boats (HUNT carry-over), sonar discovery bonuses.
  5. **No PvP damage** between orcas in v1.
- **Locked engineering phasing:**
  - **STRIKE-W3/W4:** solo round + scoring + spawn picker (no network).
  - **STRIKE-W5 (GATED):** multiplayer sync; requires W1e architecture pick
    before any socket code.
- **Stack pick (2026-07-10 `/mod-decide`):** **PartyKit** rooms; deploy host
  **Bash.tv** (not EC2). See `decisions/STRIKE-mp-stack.md`.
- **Default architecture (superseded):** ~~Cloudflare Durable Objects~~ —
  retained in W1e as fallback only if PartyKit blocks on Bash.tv.

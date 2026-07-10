# STRIKE — multiplayer stack and deploy host

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260710_orca-strike-game
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5
- **Question:** Which multiplayer stack and deploy host for STRIKE-W5?
- **Options considered:**
  - A: Cloudflare Durable Objects + Worker WebSocket; authoritative scores on DO
  - B: PartyKit rooms; room handler in repo; managed WS on PartyKit cloud
  - C: Defer W5 entirely (solo only)
- **Operator input (verbatim intent):** "a (but this will be build on the bash.tv
  ecosystem so it wont need ec2) it will be or B if you think its going to work
  better"
- **Pick:** **B — PartyKit**, deploy host **Bash.tv** (not EC2)
- **Rationale:** Operator leaned A but delegated the Bash.tv fit call. Bash.tv
  is a single serial-agent VM with no confirmed long-running WS server on-box
  (BREC). PartyKit keeps the room server in the same repo (`partykit/`
  handler) and deploys to PartyKit cloud, so the Bash.tv build only hosts the
  game client. Cloudflare DO is stronger for score anti-cheat but requires a
  separate Workers + wrangler deploy pipeline that a Bash.tv agent pass is
  likely to fumble. PartyKit room handlers can still hold authoritative score
  tallies for co-op arcade v1.
- **Implications for BUILD:**
  - Retire EC2 (`i-04a649f91274e9fce`, port 3010) as STRIKE deploy target;
    Bash.tv is the primary ship target for the standalone game.
  - W5 file layout: `partykit/` room server + `web/lib/scene/orcaStrike/net/`
    client; no `workers/orca-strike-rooms/` CF folder.
  - Room codes remain 6-char Dodo-style; protocol sketch in W1e applies with
    PartyKit `onConnect` / `onMessage` instead of DO.
  - EC2 URL `orca-strike.aimez.ai` may remain a dev/staging mirror only if
    operator keeps it; not required for lane ACCEPT.
  - W5 remains gated until W2–W4 solo path lands.

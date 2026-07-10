# STRIKE-W1e — multiplayer architecture recommendation

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Locked product shape:** `decisions/STRIKE-multiplayer.md`  
**Gate:** No W5 socket code until O0 approves this pick.

## Requirements (from charter)

- Dodo-style **6-character room codes** join/create sessions
- One **island instance** per room (spawn bounds from `islands/definitions.ts`)
- **Co-op scoring**, no orca-vs-orca damage
- Sync: remote orca **positions + scores** (not full physics sim on server v1)
- Client: thin; EC2-hosted Next.js game at `orca-strike.aimez.ai`
- Phased: solo W3/W4 first, network W5 gated

## Options evaluated

| Option | Pros | Cons |
|--------|------|------|
| **PartyKit** | Room primitives, WebSocket, quick JS/TS SDK, Dodo-like codes | Third-party dependency; vendor lock-in; score authority requires custom room logic |
| **Cloudflare Durable Objects** | Strong per-room authority, global edge, fits island=room | Separate Workers deploy pipeline; EC2 frontend + CF backend split ops |
| **Ably / Liveblocks** | Managed pub/sub | Cost at scale; less game-shaped |
| **Self-hosted WS on EC2** | Same box as Next | Couples game deploy to net scale; SSM patch tarball model ill-suited for long-lived WS |
| **Colyseus** | Game server framework | New process on EC2; ops burden |

## Default recommendation: **Cloudflare Durable Objects**

**Pick:** One **Durable Object instance per room code**, fronted by a **Cloudflare Worker** WebSocket upgrade. Next.js client connects via `wss://rooms.orca-strike.aimez.ai` (or Workers custom domain).

### Rationale

1. **Authoritative score events.** Co-op leaderboard integrity requires server-side tally. DO holds canonical `scores: Map<playerId, number>`; clients send intent events, DO validates and broadcasts.
2. **Room = island instance.** DO state `{ islandId, players[], orcaStates[], matchPhase, timerS }` maps 1:1 to operator intent.
3. **Thin EC2 client unchanged.** Solo game stays on EC2 port 3010; W5 adds a WS client module only. No second process on the hackathon host.
4. **Latency.** Salish Sea players benefit from edge-terminated WS; position sync at 10–15 Hz is sufficient for ghost orcas.
5. **Workspace fit.** Repo already uses Cloudflare plugins; Workers deploy is a separate artifact from tarball SSM patches.

PartyKit is the **fallback** if O0 wants zero Cloudflare account work in week 1 of W5. It is faster to prototype but weaker on score anti-cheat without a dedicated authority layer.

## Room code protocol sketch

### Code format

- 6 chars, uppercase consonants + digits, ambiguous chars excluded: `CFGHJKMNPQRSTWXYZ23456789`
- Example: `K7NP3X`
- Collision: Worker hashes code → DO id `room:K7NP3X`; create-if-absent

### Client → server messages

```typescript
type ClientMsg =
  | { t: 'join'; code: string; playerId: string; displayName: string; skinId: string }
  | { t: 'spawn'; lat: number; lon: number; depthM: number }
  | { t: 'pose'; x: number; y: number; z: number; yaw: number; pitch: number; roll: number; mode: string; seq: number }
  | { t: 'score'; event: ScoreEvent; seq: number }  // DO validates against pose/mode
  | { t: 'leave' };
```

### Server → client messages

```typescript
type ServerMsg =
  | { t: 'joined'; code: string; islandId: string; players: PlayerMeta[]; timerS: number }
  | { t: 'state'; tick: number; orcas: RemoteOrcaState[]; scores: Record<string, number>; phase: MatchPhase }
  | { t: 'score'; playerId: string; event: ScoreEvent; total: number }
  | { t: 'round_end'; winnerId?: string; totals: Record<string, number> }
  | { t: 'error'; code: string; message: string };
```

### Join flow

```
Client opens WS → send join{code}
  → DO loads island def, assigns playerId
  → if first player: start lobby timer
  → broadcast joined to all
Host presses Start (or auto at 4 players / 60s lobby)
  → DO phase countdown → active, timerS=180
Each frame client sends pose @ 12 Hz
DO broadcasts state @ 12 Hz to all members
Score events validated (e.g. deck_win only if DO saw pose over deck)
Round end → results → lobby reset, same code
```

## State sync model

| Field | Authority | Rate | Notes |
|-------|-----------|------|-------|
| Local orca pose | Client sim (existing pilot) | 60 Hz local | Unchanged solo path |
| Remote orca ghosts | DO broadcast | 12 Hz | Interpolate + 100ms buffer |
| Scores | **DO authoritative** | event-driven | Client prediction optional, reconcile on broadcast |
| Match timer | DO | 1 Hz | Clients display interpolated |
| Island bounds | DO config | static | Anti-cheat: clamp pose if outside bounds (soft snap) |

Remote rendering: `RemoteOrca.tsx` loads same `orca.glb`, applies received pose, no full `OrcaController` (LOD simplified).

## Latency approach

- **Interpolation:** buffer 2 server ticks (≈167 ms at 12 Hz)
- **Extrapolation:** max 150 ms if packet late, then freeze
- **No client-side rollback v1:** arcade co-op, not PvP
- **Score validation:** permissive v1 (trust client event + mode string); tighten W5b with pose sanity checks

## Phased rollout

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| **W3–W4** | Solo only | `match.ts` local timer, no WS |
| **W5a** | Infra | Worker + DO stub, join by code, echo pose |
| **W5b** | Ghosts | `RemoteOrca.tsx`, 12 Hz sync, island bounds |
| **W5c** | Scores | DO validates/applies score events, HUD team total |
| **W5d** | Polish | Reconnect, late join spectator, room browser defer |

## File layout (W5)

```
web/lib/scene/orcaStrike/net/protocol.ts   // types above
web/lib/scene/orcaStrike/net/client.ts     // WS + reconnect
web/lib/scene/orcaStrike/net/RemoteOrca.tsx
workers/orca-strike-rooms/                 // CF Worker + DO (new repo folder or sibling)
  src/index.ts
  src/RoomDurableObject.ts
```

## Operator decision requested

O0 must confirm:

1. **Cloudflare DO** as default (this doc) OR **PartyKit fallback**
2. Subdomain for WS (`rooms.orca-strike.aimez.ai`) and CF account ownership
3. Whether W5 is in-scope for lane ACCEPT or deferred post-W4

Until confirmed, W5 remains gated; solo W2–W4 proceed independently.

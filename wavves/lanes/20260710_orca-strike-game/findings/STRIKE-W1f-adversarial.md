# STRIKE-W1f — adversarial scope and lock audit

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Auditor:** STRIKE-W1 orchestrator  
**Baseline:** HUNT landed uncommitted; STRIKE chartered 2026-07-10

## Verdict

**GO for STRIKE-W2** with documented preflight items. No HUNT lock violation
requires `/mod-decide` before W2. W4 standalone migration and hydrophone fetch on
clean clones remain tracked escalations.

---

## 1. STRIKE scope vs HUNT locks

| HUNT lock | Source | STRIKE impact | Status |
|-----------|--------|---------------|--------|
| `orcaPilot/input.ts` untouched | waveset, STRIKE-controls | Full Q/E/A/D remap via `orcaStrike/controls.ts` + `inputAdapter.ts` + scene key listeners | **COMPATIBLE** |
| `worldUnitsPerMeter: 1` | HUNT-movement-scale | Unchanged in `OrcaStrikeScene.tsx:123` | **OK** |
| No OrbitControls | HUNT-orbit-coexistence | Chase cam only | **OK** |
| Fixed 0–25 m depth band | HUNT-bathy-fidelity | Q/E depth rate must clamp same band in FSM | **OK** (implement in W3a) |
| Metric tileset fit | OrcaStrikeScene correction | `TILESET_METRIC_DIAMETER_UNITS` | **OK** |
| Boats ram/sink | HUNT carry-over | Reuse `checkRamCollisions`, scoring adds points | **OK** |
| Kayaks non-target | KayakEntity.ts | STRIKE adds kayak scoring; new hitboxes, no boat collision fork | **OK** |
| F radar + 1–9 teleport | STRIKE-controls | Retained; O-key is additive | **OK** |
| Teleport vs pilot XZ | HCHK Blocker 2 | Frame-order pattern preserved in W1b integration spec | **OK** |

### Genuine tension (managed, not blocking)

**A/D semantics change.** HUNT: turn assist into `deadReckoning` `left`/`right`.
STRIKE: body roll. Resolution: `inputAdapter` forces `left:false, right:false`;
roll applied to `pose.roll` in FSM post-step. **Do not edit** `deadReckoning.ts`
for roll; overlay roll after integration.

**Depth input change.** HUNT sandbox uses S-dive/Space-rise via `orcaStrikeInput.ts`.
STRIKE replaces with Q/E. Remove `applyOrcaStrikeDepthInput` at W4; delete or
deprecate sandbox helper after `(game)` migration.

**Space key conflict.** HUNT scene binds Space to climb (`OrcaStrikeScene.tsx:241-254`).
STRIKE assigns Space to breach mash. W4 convergence must remove climb listener.

---

## 2. Standalone boundary violations risk

| Risk | Current state | Mitigation |
|------|---------------|------------|
| Route in `(sandbox)/` not `(game)/` | Live URL uses sandbox group | W4 creates `(game)/orca-strike/layout.tsx` fullscreen, no SiteNav |
| Global navbar overlap | Sonar HUD positioned `top: 76` to clear site nav (`OrcaStrikeScene.tsx:742`) | Standalone layout removes nav; reset HUD to `top: 12` |
| Workbench / SalishScene coupling | None imported in OrcaStrikeScene | Forbidden list holds |
| `web/app/layout.tsx` nav wiring | Game inherits root layout today | `(game)/layout.tsx` minimal shell in W4 |
| Honesty-legend UI in HUD | Not present | Keep forbidden |

**Risk level:** MEDIUM until W4. Solo W2/W3 library work is safe; early `(game)` shell stub in W2 is optional but recommended to test standalone CSS.

---

## 3. Control remap without editing `input.ts`

**Feasible.** Precedent already in scene:

- F-key sonar: scene-level `keydown` listener (`OrcaStrikeScene.tsx:324-331`)
- Space climb: scene-level listener (to be replaced)
- Digit 1–9 teleport: scene listener (`593-602`)
- Mobile overlay: separate sampler

W2e pattern:

```
createOrcaPilotInputSampler()  // unchanged WASD + mouse
createStrikeControls(dom)      // NEW: Q E B O Space edges + held state
merge → inputAdapter → pilot.update()
```

Keys not in `input.ts` (Q, E, B, O) captured only in `controls.ts`.
W/S/A/D/Shift pass through sampler; adapter rewrites semantics before DR.

**No lock violation.**

---

## 4. Missing asset blockers

| Asset | Blocker? | Note |
|-------|----------|------|
| `web/lib/scene/orcaStrike/**` | Expected | W2–W3 create |
| `web/app/(game)/orca-strike/**` | Expected | W4 migration |
| `orca.glb`, DTAG driver | **Present** | Verified on disk |
| Hydrophone m4a | **Soft blocker** | Gitignored; **present locally** (2.2 MB). Clean clone needs `PROVENANCE.md` fetch before O-sonar ACCEPT |
| `classification.json` | **Present** | |
| Island defs / thumbs | Missing | W2a |
| VFX / replay / net | Missing | W2d, W2c, W5 |

**W2 can start** with hydrophone stub pointing at `/hydrophone/slice/...m4a` and
documented fetch script for CI.

---

## 5. ASSET_DEPENDENCY_MAP accuracy

W1a found **8 path corrections** (materials/, physics/, spawn file names, mobileInput.ts).
O0 should patch map before W2 dispatch or W2 agents use W1a as override authority.

---

## 6. Multiplayer gate

W1e recommends **Cloudflare Durable Objects**. O0 must approve before W5.
Does not block W2–W4.

---

## 7. Go / no-go matrix

| Wave | Decision | Blockers |
|------|----------|----------|
| **W2** | **GO** | Patch asset map paths; optional hydrophone fetch on dev machine |
| **W3** | **GO** (conditional on W2 gates) | controls compile, island defs render |
| **W4** | **GO** (conditional on W3) | Single convergence editor; standalone layout |
| **W5** | **GATED** | O0 picks DO vs PartyKit; WS subdomain |
| **ACCEPT** | **GATED on W4** | Visual verify list in waveset |

---

## 8. Escalations to operator

1. **Hydrophone m4a:** gitignored; add fetch step to deploy/CI checklist or LFS policy.
2. **Multiplayer provider:** confirm Cloudflare DO default (W1e) or PartyKit fallback.
3. **Asset map corrections:** O0 commit map fixes alongside W1 findings.
4. **No `/mod-decide` needed** for A/D roll vs HUNT turn assist; covered by STRIKE-controls lock superseding HUNT input semantics at adapter layer.

---

## 9. Forbidden actions confirmed

- Edit `orcaPilot/input.ts` — **NOT DONE**, **NOT PLANNED**
- Start W2 in this orchestrator pass — **NOT DONE** (per dispatch)
- Run git — **NOT DONE**

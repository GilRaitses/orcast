# DE3 -- strategy dead-end drift register (operator-facing prose)

Agent: DE3 (Wave DE, graduation waveset). Date: 2026-06-27 (America/New_York).
Scope: operator-facing strategy prose -- `ORCHESTRATOR_NOTES.md`, handoff charters/dispatch/README/
hydration under `*handoff/`, plus cross-referenced strategy pointers (`WILDLIFE_SOURCES_REGISTER.md`
via hydration). Authority: SYN sections 1-2 (observation-first), M2 sections 8-9, M3 sections 3-4,
G3 sections 0/4 (L3 binding constraint = summer PRESENCE-DAYS, not feed). Mode: read-only audit;
recommend only; no edit, no commit. (Audit run by the DE3 subagent; landed to disk by the orchestrator
because the read-only explore agent cannot write files. Content is the subagent's verbatim register.)

Drift count: 16 total -- P0: 2, P1: 7, P2: 6, P3: 1.

## Executive summary

The PINN caveat in `ORCHESTRATOR_NOTES` is intact (section 3: "Do not jump to a full PINN").
Hawkes-as-skill does not appear in operator strategy prose. No live recommendations for reservoir/ESN,
EDM, neural TPP, SDE-movement, synthetic augmentation, HF-radar, or terrain-on-the-temporal-gate were
found in scope. The main drift cluster is (1) unconditional LGCP-backbone steering in
`ORCHESTRATOR_NOTES`, (2) stale "L3 blocked on real Chinook feed" across the mlops-handoff chain
(contradicts G3: Albion is real/stock-aligned; binding constraint is presence-days), and (3) a stale
wildlife P0 order that still ranks "real Chinook index" as gate #2 and lists CUTI/BEUTI without a
coverage caveat. The signal-modeling-launch-handoff charter/dispatch/hydration is largely aligned with
the post-SYN observation-first framing.

## Register

| # | File (+ section) | What it recommends | Dead-end / conflict | Why drift (cite) | Recommended caveat / edit | Priority |
|---|------------------|-------------------|---------------------|------------------|---------------------------|----------|
| 1 | `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 4 (architecture critique, 1st bullet) | Move backbone to hierarchical Bayesian LGCP with partial pooling; replace binary gate with posterior | Spatial GP/LGCP at current N unless fold-stable held-out gain proven | SYN section 2 dead-ends: "GP-modulated intensity / spatial LGCP at current N"; M2 rank 2 is GO conditional on fold-stable held-out gain + M1 coordination, not unconditional backbone swap | Reframe: "LGCP is a conditional prototype (M2 rank 2): must beat GLM on fold-stable held-out CV-skill toward +0.144; coordinate with M1 hierarchical NB (TA2) to avoid double-counting. Default path: Tier A (MMPP, partial-pooling NB), not backbone replacement." | P0 |
| 2 | Same file, section 6 experiment 3 | Prototype the LGCP backbone on cached acoustic series; compare PIT + held-out log-likelihood | Same as #1 | SYN section 4 residual-risk trap: flexible GP fits better in-sample; M2 section 10: LGCP credit cannot come from in-sample likelihood | Gate experiment identically: `block_cv` fold-stable skill vs +0.144 bar; no promotion from PIT alone; sequence after A1 MMPP / A2 hierarchical NB | P0 |
| 3 | `20260627_mlops-handoff/HANDOFF_CHARTER.md` section A purpose | Frontier includes "validating a real Chinook feed for L3" | "More prey series" as L3 lever | G3 sections 0/4: Albion run index already real, complete, stock-aligned; binding constraint is summer acoustic presence-days (SYN section 1, Tier B1 nodes). Feed refresh is necessary but not sufficient | Replace with: "L3 stays WITHHELD; binding lever is Jun-Sep presence-days (S1/TB1 new nodes + accruing summers). Albion refresh (W8/TB3) is supporting only." | P1 |
| 4 | `20260627_mlops-handoff/HANDOFF_CHARTER.md` section D primer | "L3 needs a real Chinook run-timing feed to replace the climatology placeholder" | Same | G3: placeholder narrative is stale post-W3/W7; real Albion 2019-2026 cached | Update to G3/SYN: feed met; L3 gated on presence-days + LOYO bar (>=3/n, n>=8, ~12-15 presence-days/yr) | P1 |
| 5 | `20260627_mlops-handoff/HANDOFF_CHARTER.md` section E dispatch row "M-L3 real Chinook feed" | Validate Albion/DART parsers; re-run lag scan on real feed | Same | G3 section 1f: extending Albion does not add a single presence-day; DART is stock-mismatched (PATCH-salmon caveat) | Rename lane to "L3 re-test (presence-day-gated)"; primary dependency = new observation nodes (SYN B1), not parser validation | P1 |
| 6 | `20260627_mlops-handoff/HANDOFF_CHARTER.md` section E row "WILDLIFE ingest follow-on" | P0 order: multi-station acoustic, real Chinook, held-out visual | Stale prey-series priority | Points to register (#9) whose #2 blocker contradicts G3/SYN | Point to SYN + graduation TB1/TB3 instead of stale wildlife P0 | P1 |
| 7 | `20260627_mlops-handoff/README.md` | "L3 withheld pending a real Chinook feed" | Same | G3/SYN | One-line G3 alignment (presence-days-first) | P1 |
| 8 | `20260627_mlops-handoff/ORCHESTRATOR_DISPATCH_PROMPT.md` | "L3 withheld pending a real Chinook feed"; next: validate Albion/DART | Same | G3/SYN | Same as #7; reorder "next" to TB1 dry-run + TA1 MMPP parallel | P1 |
| 9 | `20260627_wildlife-sources/WILDLIFE_SOURCES_REGISTER.md` "What the gate state says we need" + "Recommended acquisition order" #2 | #2 blocker = "real Chinook prey index"; M-L3 withheld on climatology placeholder; step 2 = validate Albion/DART | More prey predictors as L3 lever | G3: feed real; SYN section 1: +0.144 gap is observation first; M3 section 4: prioritize sourcing nodes over transforms | Add banner: "Superseded for forecast skill path by SYN (2026-06-27). L3 lever = presence-days. CUTI/BEUTI = NO-GO (coverage)." Revise acquisition order #2 to presence-day nodes (Port Townsend/Bush Point, Boundary Pass) | P1 |
| 10 | `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 4 (4th bullet) | For sparse counts, zero-inflated or hurdle model (or LGCP) vs NB GLM | NB->ZI/hurdle count upgrade | SYN section 2 dead-end: "NB -> ZI/hurdle count upgrade"; TA2 graduate is presence-hurdle reframe (Bernoulli/cloglog on presence), not ZI count model | Distinguish: GO = TA2 presence-hurdle reframe alongside hierarchical NB; NO-GO = ZI/hurdle count upgrade on the hourly NB target | P2 |
| 11 | `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 3 move 2 | High-value PIML #2: build `k_salmon` as advected run-timing field (transport kernel + lag) | Indirect prey-engineering priority vs observation | G3/SYN: salmon covariate (M3 D1) is feed-gated AND presence-day-gated; cannot close L3 without TB1 presence-days | Keep as M3 derived-covariate idea; demote priority; prefix: "After B1/TB1 adds presence-days; D1 stays WITHHELD until then" | P2 |
| 12 | `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 6 experiment 4 | Run M-L3 salmon lag scan on real Albion/Bonneville series | Feed-as-lever framing | G3 section 4: Albion extension alone cannot move L3; Bonneville/DART stock mismatch | Reframe: "Refresh Albion (TB3) + re-test only after presence-day lift from new nodes/summers" | P2 |
| 13 | `20260627_wildlife-sources/WILDLIFE_SOURCES_REGISTER.md` Tier 1 row | CUTI/BEUTI upwelling as prey-base indicator | CUTI/BEUTI (out of coverage ~48.5 N) | SYN section 2 dead-end: "CUTI/BEUTI upwelling (out of product coverage, 31-47 N)" | Mark NO-GO / out-of-coverage; do not list in acquisition order without caveat | P2 |
| 14 | `20260627_mlops-handoff/HYDRATION_PACKET.md` section 3 | P0 order via wildlife register: multi-station, real Chinook index, visual | Inherits #9 | Steers operators to stale register | Add: "For the skill path, read SYNTHESIS_signal_modeling.md first; wildlife register prey priority is stale on L3" | P2 |
| 15 | `20260627_mlops-handoff/HANDOFF_CHARTER.md` section C registry | "M-L3 salmon lag \| lag scan on climatology placeholder; withheld" | Stale state | G3/W3: real Albion exercised; L3 WITHHELD for power/presence-days, not placeholder | Update registry row to match G3 FLAGGED/WITHHELD + presence-day constraint | P2 |
| 16 | `20260627_orcast-handoff/HANDOFF_CHARTER.md` section E | "MLM L3 + PIML \| salmon series, effort model, NOTES PIML plan" | Inherits ORCHESTRATOR_NOTES drift (#1, #10-12) | Points to undifferentiated PIML plan without SYN sequencing | Add pointer: "PIML strategy subordinate to SYN ranked plan + G3 L3 constraint" | P3 |

## Still-correct strategy (explicit clean bill)

| Source | Verdict |
|--------|---------|
| `ORCHESTRATOR_NOTES.md` section 3 opening + PINN caveat ("Do not jump to a full PINN") | Clean -- matches M2 NO-GO on full PINN |
| `ORCHESTRATOR_NOTES.md` section 3 move 1 (harmonic tide) | Clean -- implemented PIML win; not a dead-end |
| `ORCHESTRATOR_NOTES.md` section 3 move 3 (`s_space` frontal/bathymetry habitat) | Clean -- M3 E-family: validation/`s_space` only, not temporal gate |
| `ORCHESTRATOR_NOTES.md` section 3 move 4 (energy/movement SDE) | Clean -- Level 4+, partnership-gated |
| `ORCHESTRATOR_NOTES.md` physics shape priors (section 3 closing) | Clean -- TA5 graduate |
| `ORCHESTRATOR_NOTES.md` section 5 PIML literature (PINN papers as bibliography) | Clean -- citation list with section 3 caveat |
| `20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` (A, B W6 reality, F L3 GO-fetch/NO-GO-promote) | Clean -- observation-first + G3-aware |
| `20260627_signal-modeling-launch-handoff/ORCHESTRATOR_DISPATCH_PROMPT.md` | Clean -- +0.144 bar, dead-ends stated, W6 0 net-new |
| `20260627_signal-modeling-launch-handoff/HYDRATION_PACKET.md` | Clean -- includes G3, G2, SYN lineage |
| `20260627_mlops/CAMPAIGN_CHARTER.md` O4 | Mostly clean -- mentions "more presence-years"; could cross-link SYN B1 explicitly |
| Hawkes | No drift in operator strategy scope -- diagnostic nuance preserved (DE2/DE1) |

Not in scope but noted: `PATCH-salmon.md` is historical Wave-1 spec (pre-Albion EC2 path);
stock-mismatch caveat present. `SIGNAL_MODELING_CHARTER.md` lists PINN/reservoir as research-brief
topics for M2 -- acceptable pre-SYN charter language; post-SYN operators should read SYN first.

## Prioritized remediation list

1. P0 -- `ORCHESTRATOR_NOTES.md` section 4 + 6.3 (LGCP): add M2/SYN conditional language; demote LGCP from default backbone to gated prototype; require fold-stable held-out gain and M1/TA2 coordination before any integrate conversation.
2. P1 -- mlops-handoff authority chain (`HANDOFF_CHARTER.md` A/D/E, `README.md`, `ORCHESTRATOR_DISPATCH_PROMPT.md`): replace "L3 needs real Chinook feed" with G3/SYN framing -- presence-days first (TB1/S1 nodes), Albion refresh supporting (TB3), L3 WITHHELD until LOYO/power bar met.
3. P1 -- `WILDLIFE_SOURCES_REGISTER.md` + `HYDRATION_PACKET.md` pointer: supersede stale gate narrative and acquisition order #2; add SYN cross-link; mark CUTI/BEUTI NO-GO.
4. P2 -- `ORCHESTRATOR_NOTES.md` section 4 ZI/hurdle bullet: split TA2 presence-hurdle reframe (GO) from ZI/hurdle count upgrade (NO-GO).
5. P2 -- `ORCHESTRATOR_NOTES.md` section 3.2 + 6.4 (salmon/advection experiments): subordinate prey-transport and lag-scan work to presence-day sequencing per G3/M3.
6. P2 -- `mlops-handoff/HANDOFF_CHARTER.md` section C registry snapshot: update L3 row from "climatology placeholder" to G3 current state.

Nothing deployed, fetched-to-write, promoted, or committed; effective confidence stays 0.0.

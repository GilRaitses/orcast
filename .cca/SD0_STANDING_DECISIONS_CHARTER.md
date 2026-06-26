# Wave Set SD — Standing Decisions & Resolutions charter

Date: 2026-06-26
Purpose: capture every settled authorial / architectural / claim decision in orcast as a **ratified standing decision with a resolution**, in one canonical register, so later waves and drafts cannot silently re-open or contradict them. This is the decision-log layer above `CLAIM_BOUNDARIES.md` (which holds *values*); SD holds the *decisions and their rationale*, including the "accepted as-is" residuals.

Deadline context: Devpost submission June 29, 2026 5:00 PM ET. SD is documentation-only and operator-safe; it ships no product change.

Canon it must stay consistent with: `.cca/CLAIM_BOUNDARIES.md`, `docs/devpost/casting/PROVENANCE_GRAPH_CONTRACT.md`, `docs/devpost/WAVES_REGISTRY.md`.

---

## Deliverable: `.cca/STANDING_DECISIONS_REGISTER.md`

One row per decision, with this schema:

| field | meaning |
|-------|---------|
| `id` | SD-NNN, stable, never reused |
| `decision` | the ruling, stated as an imperative ("WP2 scope term is *orchestrator-in-the-loop agentic systems*") |
| `rationale` | why — the trade-off that was weighed |
| `status` | `ratified` / `superseded by SD-NNN` / `open` / `accepted-as-is` |
| `resolved` | date + how (chat decision, reconciliation, adversarial finding) |
| `enforces_via` | the gate/file that makes it stick (e.g. `CLAIM_BOUNDARIES.md` row, a doc-grep, a render rule) |
| `surfaces` | files that must reflect it (so drift is checkable) |

`accepted-as-is` is a first-class status: a residual the author has chosen NOT to change, recorded WITH the reason, so it is canonical rather than an unexplained gap.

---

## Seed inventory (entry state — discovery will verify + expand)

Decisions already made in this campaign that the register must capture:

| seed | decision | status |
|------|----------|--------|
| A | WP2 scope term = "orchestrator-in-the-loop agentic systems"; Magentic-UI kept as the cited human-in-the-loop instance | ratified 2026-06-26 |
| B | $R_\mathrm{uncited}$ Maps-only baseline = **60–100%** (8-scenario); the **85%/89%** figure is a *separate* 3-query probe metric, not the same number | ratified |
| C | WP page counts: WP1 10 full / 7 share; WP2 5 full / 4 share | ratified |
| D | Authorship voice: first-person singular (Gil Raitses) + aimez.ai as the lab; no "we/our" | ratified |
| E | Provenance contract edges (`grounded_in` C→R; no-signal badge on a claim with no `supports` edge) are canonical for every provenance figure | ratified |
| F | Primary-anchor gate: no "gap"/"no existing system" claim without a cited primary study; otherwise reframe as an open question | ratified |
| G | Gate naming: pipeline = L0 QC + E1–E6 (E4 composite, E5 deviance skill, E6 PIT); kernel-program levels L1–L3 are a *separate* namespace | ratified |
| H | Companion paper (WP2) is "built / technical report," never "in preparation" or "peer-reviewed" | ratified |
| I | ~~Deploy canon: Vercel builds from repo-root `vercel.json` (web/ monorepo pin)~~; `web/.env.example` is tracked | **superseded by SDR SD-011** (root pin broke the build; canon = Root Directory=`web` + minimal `web/vercel.json`) |
| J | Git identity for this repo = Gil Raitses <gilraitses@gmail.com> | ratified 2026-06-26 |
| K | Forbidden claims (predicts whale locations, LeCun AMI gap filled, "high accuracy") remain forbidden | ratified |
| L | Accepted-as-is residuals (e.g. fig shorthand `R_uncited` vs `$R_\mathrm{uncited}$`; nine-table canonical count cited in captions; already-pushed commits stamped `Mac.lan`) — recorded with reason, not "fixed" | accepted-as-is |

---

## SD-0 — Discovery (readonly, parallel) [AGENT]

Mine the settled decisions from the record. Lanes run concurrently:
- **SD-0a Decision archaeology:** scan `.cca/STEP_LOG.md`, `.cca/CLAIM_BOUNDARIES.md`, the two cleanup charters/registers (`HANDOFF_WAVESETS_CHARTER.md`, `P2X_*`), and recent git log on both repos for rulings, reconciliations (e.g. 60-91→60-100), and supersessions. Emit candidate SD rows.
- **SD-0b Accepted-as-is sweep:** collect every "WONTFIX", "accepted", "deferred", "left as-is" note across `.cca/**` and the defect registers; each becomes an `accepted-as-is` row WITH its stated reason. (This directly answers the standing question "what residuals are accepted as-is, and are they canonical?")
- **SD-0c Contradiction probe:** for each candidate decision, check whether any current surface already contradicts it (so the register doubles as a drift report on entry).

Gate: a draft `STANDING_DECISIONS_REGISTER.md` exists with every seed A–L plus discovered rows, each with a real `resolved` provenance pointer.

## SD-1 — Classification / ratification [AGENT, parent]

Parent dedupes, assigns `status`, links supersessions (old decision → `superseded by SD-NNN`), and fills `enforces_via`. Any decision that is genuinely still **open** is flagged for the user (not silently ratified). `accepted-as-is` rows must each carry a one-line reason or they get demoted to `open`.

Gate: every row has status + rationale + enforces_via; open rows listed for author sign-off.

## SD-2 — Wire-in [AGENT]

Make the register load-bearing, not just a list:
- Add a pointer from `CLAIM_BOUNDARIES.md` and `docs/devpost/WAVES_REGISTRY.md` to the SDR as the decision-of-record.
- For each `ratified` row with a checkable surface, note the existing gate (doc-grep / render rule) or add a one-line grep assertion to the relevant `tools/waves` doc-grep so future drift trips a gate.
- No product/code behavior change.

## SD-3 — Adversarial review (readonly) [AGENT]

One readonly subagent checks the register against `CLAIM_BOUNDARIES.md` + the provenance contract for: internal contradiction, a "ratified" decision that a live surface violates, or an `accepted-as-is` row whose reason is actually a real defect (should be escalated). Findings:
- contradiction / mis-ratification → fix, re-run SD-3.
- a residual that should NOT be accepted → escalate to a fix wave.
- clean → SD-4.

## SD-4 — Verify + commit [AGENT]

`./tools/waves/run-gate.sh s-doc-grep` (+ any new SD assertions); commit `STANDING_DECISIONS_REGISTER.md` + the pointer edits; push; add Wave Set SD = done to `WAVES_REGISTRY.md`.

Loop exit: register covers all seeds + discovered decisions, zero contradictions in SD-3, open rows surfaced to the author, gates PASS, pushed.

---

## Execution order
1. SD-0 (3 readonly lanes) → draft register.
2. SD-1 ratify (parent); surface open rows to author.
3. SD-2 wire-in.
4. SD-3 adversarial; loop to SD-1 if needed.
5. SD-4 verify + push + registry.

Note: SD makes decisions *durable and enforced*; it does not itself re-decide anything. Any decision discovered to be genuinely open is returned to the author rather than ruled on by the wave.

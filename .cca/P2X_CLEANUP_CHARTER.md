# Wave Set P2X — P2 residual cleanup charter

Date: 2026-06-26
Purpose: clear every P2 finding left open after the 2026-06-26 adversarial wave (the three auditors that followed the `60–100%` reconciliation). P0/P1 from that wave are fixed and pushed (`orcast bad9ea2`, `aimez 2b8ed73`); this charter is scoped **strictly to the P2 residue** plus any new flags the discovery wave surfaces.

Deadline context: Devpost submission June 29, 2026 5:00 PM ET.

Canon: every fix is gated against `.cca/CLAIM_BOUNDARIES.md` (capability table, exact-numbers table, forbidden list, prose register), `docs/devpost/casting/PROVENANCE_GRAPH_CONTRACT.md` (node/edge schema + render rules), and the visual-verification rule (read every regenerated PNG before declaring it fixed).

---

## P2 gap inventory (entry state)

Carried from the three auditors. Severity-within-P2: `p2a` = visible to a judge/reader, `p2b` = hygiene/repro only. Paths are entry hypotheses; discovery confirms exact `file:line`.

| id | src audit | sev | gap | entry location |
|----|-----------|-----|-----|----------------|
| C1 | claim | p2a | standalone `85%` shown without "Maps-only grounding baseline" context | `web/app/components/ProvenanceGraph.tsx`, `web/app/gates/page.tsx`, GitHub bio |
| C2 | claim | p2a | hedging ("may") where a canonical firm statement exists | WP1/WP2 `LX/Sections/*.tex` (discovery locates) |
| C3 | claim | p2b | framing drift ("world model systems") vs canonical scope wording | WP2 `LX/Sections/*.tex` |
| C4 | claim | p2b | specific canonical number omitted where the exact-numbers table has one | WP captions + outreach drafts |
| D1 | deploy | p2b | no `vercel.json` at repo root; `rootDirectory` null in project settings → fresh-clone deploy ambiguity | repo root, Vercel project |
| D2 | deploy | p2b | env vars documented but no `.env.example`/guard → fresh clone breaks at runtime | `web/`, docs |
| D3 | deploy | p2a | placeholder arXiv-link text on site/drafts (acceptable until IDs exist; needs a single canonical token) | `aimez/docs/index.html`, `.cca/outreach_drafts/*` |
| D4 | deploy | p2b | stale HTML comment (placeholder gallery) | `aimez/docs/index.html:136` |
| W1 | consistency | p2a | Paper 2 called "in preparation" though it exists (5pp/4pp built) | `docs/whitepaper/LX/Sections/08_geospatial_limits.tex` |
| W2 | consistency | p2a | gate labeling drift: `L0–L5` vs `E1–E6` across figures/captions | `Appendix_Diagrams.tex`, fig-1/fig-2 mmd |
| W3 | consistency | p2b | `\graphicspath` flagged "dead" — **likely false positive** (LX root pulls `docs/figures/` drawio PNGs); verify then keep or prune | `Raitses_orcast_2026{,_share}.tex:24/28` |
| W4 | consistency | p2b | caption omits a number the body states | WP1 appendix captions |
| W5 | consistency | p2b | inconsistent notation for the same quantity ($R_\mathrm{uncited}$ etc.) across papers | WP1/WP2 sections |
| W6 | consistency | p2a | fig-3 claim-node ordering differs from its caption (borderline P1) | `docs/whitepaper/LX/Figures/fig-3-provenance-graph.mmd` + appendix caption |

---

## P2X-0 — Discovery (readonly, parallel) [AGENT]

Three readonly subagents, one per audit domain, run concurrently. Each emits rows into `.cca/P2X_DEFECT_REGISTER.md` with exact `file:line`, `canonical value` (cite the gating doc), `actual value`, `proposed fix`, and a `confidence` (the auditor was sometimes wrong against stale gates — every row must re-verify against the *current* tree, not the prior report).

- **P2X-0a Claim/number lane:** resolve C1–C4. For each `85%`/`89%` mention, record whether the surrounding text already supplies "Maps-only baseline"; only un-contexted ones are defects. Sweep WP `.tex` for `may`/hedging and `world model systems`; cross-check the exact-numbers table for omissions.
- **P2X-0b Deploy/hygiene lane:** resolve D1–D4. Confirm current Vercel `rootDirectory`, presence of `vercel.json`, and which env vars are runtime-required; list each placeholder/stale-comment with line.
- **P2X-0c Figure/citation lane:** resolve W1–W6. Build (read) the fig-3 PNG and compare node order to caption; confirm L0–L5 vs E1–E6 usages; **verify W3 graphicspath is actually exercised** (grep includegraphics targets) before proposing any prune.

Gate: `P2X_DEFECT_REGISTER.md` exists with one verified, file-grounded row per surviving defect; false positives explicitly marked `WONTFIX (false positive)` with reason.

## P2X-1 — Classification [AGENT, parent]

Parent agent dedupes the register, drops false positives (expected: W3), confirms severity-within-P2, and partitions survivors into the four remediation lanes below. Any row that on inspection is actually P0/P1 is **escalated out of this waveset** and fixed immediately (not deferred).

Gate: every register row is labeled `FIX → lane {A|B|C|D}`, `WONTFIX (reason)`, or `ESCALATE (P0/P1)`.

## P2X-2 — Remediation (parallel write lanes) [AGENT]

- **Lane A — WP prose/number** (`LX/Sections/*.tex`): C2, C3, C4, W4, W5, W1. Edits must keep every claim inside `CLAIM_BOUNDARIES.md`. No new claims; only tighten/contextualize/normalize notation. "In preparation" → factual status (built, page counts known) without overclaiming peer review.
- **Lane B — web/site copy** (`web/app/**`, `aimez/docs/**`): C1 (add "Maps-only baseline" context to standalone `85%`), D3 (single canonical "arXiv link pending" token), D4 (remove/refresh stale comment). Keep first-person-singular / aimez.ai register.
- **Lane C — figures/captions** (`LX/Figures/*.mmd`, `Appendix_Diagrams.tex`, `docs/figures/**/figure.drawio`): W2 (unify gate labeling), W6 (reorder fig-3 nodes OR fix caption to match — pick the one matching `PROVENANCE_GRAPH_CONTRACT.md`). Every regenerated PNG is read before sign-off.
- **Lane D — deploy hygiene** (repo root, `web/`): D1 (`vercel.json` pinning rootDirectory/build), D2 (`.env.example` + documented required vars). No secrets committed.

Lanes A/B/C/D touch disjoint paths and may run as parallel subagents. Lane C must finish before P2X-4 PDF rebuild.

## P2X-3 — Adversarial review (readonly) [AGENT]

One readonly subagent re-audits the **diff only** against all three gating docs + the visual-verification rule. It must answer: did any Lane edit (a) introduce a forbidden/overclaim, (b) break a number against the exact-numbers table, (c) create a new figure/caption mismatch, or (d) change a claim's primary-anchor status? Findings:
- new P0/P1 → fix, then re-run P2X-3 on the new diff.
- residual/again-P2 → **loop to P2X-1**.
- clean → proceed to P2X-4.

## P2X-4 — Verify + gate + deploy [AGENT]

1. Rebuild any affected PDFs via the biber sequence (`pdflatex → biber → pdflatex×2`); confirm page counts still match the gate (WP1 10/7, WP2 5/4) or update the gate with evidence.
2. Visual-verify every changed figure PNG (Read the file).
3. `./tools/waves/run-gate.sh s-doc-grep` and `a-doc-grep` (doc consistency); lint changed web files.
4. Commit per repo (`orcast`, `aimez`) with a register-referenced message; push (Vercel + Pages deploy).
5. Update `docs/devpost/WAVES_REGISTRY.md` status matrix with P2X = done and link this charter + the register.

Loop exit: `P2X_DEFECT_REGISTER.md` has zero open `FIX` rows, P2X-3 returns clean on the final diff, all gates PASS, both repos pushed, and registry updated.

---

## Execution order

1. P2X-0 (3 readonly lanes, parallel) → register.
2. P2X-1 classification (parent).
3. P2X-2 Lanes A/B/D parallel; Lane C parallel but gates the PDF rebuild.
4. P2X-3 adversarial; loop to P2X-1 if needed.
5. P2X-4 verify + push + registry.

Operator-gated leftovers (real arXiv IDs for D3, Vercel dashboard `rootDirectory` toggle for D1) are flagged in the register but do **not** block loop exit — the agent lands the repo-side fix (`vercel.json`, pending-token) and marks the human step.

# Diagram defect register — draw.io rebuild (2026-06-26)

Source: 3 parallel adversarial review subagents (figs 01–04, 05–08, mp1–mp3) + 1 drawio CLI research agent. All 11 figures now have editable `.drawio` sources; PNGs are regenerated from them (`drawio -x -f png -s 2 -b 10`). TikZ originals saved as `figure.tikz.png.bak`.

Status legend: FIXED (done + re-rendered + verified) · DEFERRED (real, larger content rebuild) · FALSE-POSITIVE (reviewer claim not supported by source of record).

## Fixed this pass

| id | fig | severity | defect | fix |
|----|-----|----------|--------|-----|
| D1 | fig-06 | P0 | `derived_from` (X2→D) edge passed through the no-signal badge interior | Rerouted X2→D above the badge (exit west, corridor at y≈497, enter D top) |
| D2 | fig-08 | P1 | No legend (V6) | Added legend: solid=direct call, dashed=schedule/callback/session/partner, bold=PRIMARY SoR, bands=host grouping |
| D3 | fig-08 | P1.5 | `trigger`/`callbacks` left-margin labels too close | Widened corridor separation (x74 vs x114) |
| D4 | fig-02/03/04/05 | P2 (V6) | Palette drift (`#e1d5e7`/`#9673a6`/`#9b6bb3`/`#c06aa0`) | Normalized to spec `#E8DDF4` headers, `#A86FB2` strokes, `#FAF7FC` light fills (kept intentional yellow status note) |
| D5 | fig-mp3 | P1 | `-25pp` arrowhead overlapped the `75` label | Moved `75` right of bar; arrow ends at bar corner |
| D6 | fig-mp3 | P1 | S4 callout arrow crossed the `0%` label | Moved `0%` right of bar |
| D7 | fig-mp1 | P1.5 | S4 (planner step-log, 0%) styled as generic lilac RAG bar; no green legend | Colored S4 green + added third legend entry |

## Corrected (initially misfiled as false positives — reviewer was right)

The contract **does** exist at `docs/devpost/casting/PROVENANCE_GRAPH_CONTRACT.md` (my first search was wrongly scoped to `docs/figures/` only). Both reviewer claims were valid per the canonical edge table and render rules; fixed 2026-06-26.

| id | fig | severity | defect (per contract) | fix |
|----|-----|----------|-----------------------|-----|
| F1 | fig-06 | P1 | Contract edge table: `grounded_in` = **C → R** ("claim traces to research origin"); fig wired it X1 → R1 | Rerouted `pe_gi` to `C1 → R1` via the x500 corridor (clears M1/X1) |
| F2 | fig-06 | P1 | Render rule 5: no-signal badge hangs off *any claim with no `supports` edge*; fig wired it off M2 (a method). Unbound claim in the example is C2 | Rerouted `pe_unbound` to `C2 → nosig`, relabeled `no supports edge → unbound` |

## Deferred — real but larger content rebuilds (need a decision/next pass)

| id | fig | severity | defect | note |
|----|-----|----------|--------|------|
| R1 | fig-01 | P1 | Shows ~6 tables; `description.md` lists 9 (missing `user-journal`, `partner-api-keys`, `managed-agents`) | Archived ERD was a "Page 1 fragment". Decision: add 3 tables to match the 9-table claim, OR retitle as an explicit core-tables subset. |
| R2 | fig-01 | P1 | S3 artifact box styled identically to DynamoDB tables | Apply dashed border + "(S3 — not DynamoDB)". |
| R3 | fig-03 | P1 | Missing `FreezeSnapshot` state; live ASL is `Ingest → FreezeSnapshot → FitAndGate` | Verify against `forecast_orchestrator.asl.json`, insert state. |
| R4 | fig-03 | P1 | `EventBridge rate(1 hour)` in wrong swimlane; gate diamond labeled "configured gate threshold?" vs actual `GatesPassed? (confidence ≥ 0.6)` | Content accuracy; relabel + move. |
| R5 | fig-03 | P1/P1.5 | `ApplyPromotion` box too narrow; floating `gate_note` with no connecting edge | Widen box; anchor note with a dashed callout. |
| R6 | fig-05 | P1 | Shared vertical FK bus merges multiple relationships → untraceable | Route each FK as a dedicated orthogonal path; stagger bus x. |
| R7 | fig-05 | P1 | `engine_runs` "NB-GLM fit + gates" lacks "(target schema — not yet at L1)" caveat | Add caveat to avoid implying a completed fit run. |
| R8 | fig-07 | P1 | Four IC→c_eff return edges read as a tangled bundle | Faithful to original TikZ (4 dashed returns); optional fan-out for clarity. |
| R9 | fig-02/04 | P2 | Bottom-line text tight against box borders; a couple of edge labels near nodes | Padding/label nudges. |
| R10 | fig-mp1 | P2 | Five `100` labels sit just outside the plot frame | Nudge inside or widen frame. |

## Content rebuilds + confirmation wave (round 2)

| id | fig | severity | defect | status |
|----|-----|----------|--------|--------|
| R1 | fig-01 | P1 | Only ~6 tables vs 9 | FIXED — added user-journal, partner-api-keys, managed-agents (3×3 grid) |
| R2 | fig-01 | P1 | S3 artifact not distinguished | FIXED — dashed border |
| R3/R4/R5 | fig-03 | P1 | Diverged from live ASL | FIXED — added FreezeSnapshot; `GatesPassed? (fitted, conf ≥ 0.6)`; `HumanVerdict? (promote?)`; accurate Retry/Catch; note connected to gate |
| R6 | fig-05 | P1 | Shared FK bus | FIXED — `f_map→engine_runs` on dedicated right-margin corridor |
| R7 | fig-05 | P1 | Missing target-schema caveat | FIXED — `(target schema – not yet at L1)` added |
| R9a | fig-02 | P2 | "Network sources" line clipped | FIXED — box height +31px |
| R9b | fig-04 | P2 | `reads/writes app records` over DynamoDB text | FIXED — white label bg + pulled toward source |
| R9c | fig-04 | P2 | `WorkOS session required` label overlap | FIXED — white label bg |

Confirmation wave verdict (2 reviewers): **9/11 figures 6/6 clean**; no P0/P1 remain. Accepted-as-is residuals: fig-07 IC-return bundle (faithful to source, non-blocking) and minor label density in the fig-04 auth flow (pre-existing, complex flow).

## Circle-back on accepted-as-is residuals + contract audit (2026-06-26)

| id | fig | resolution |
|----|-----|-----------|
| F1/F2 | fig-06 | FIXED — `grounded_in` C→R; no-signal badge off unbound claim C2 (per PROVENANCE_GRAPH_CONTRACT.md). See corrected table above. |
| R8 | fig-07 | RE-EXAMINED → CANONICAL, kept. Returns `gr1`–`gr4` are already staggered (corridors x1155–1185, entries 0.35–0.65) and the `reduce c_eff` convergence is exactly E4 (`c_eff = c_raw · Π gk`) — every failed gate multiplicatively reduces confidence. Legible; no change. |
| R9b | fig-04 | FIXED — three inter-box labels overlapped body text. Shortened to fit the ~45px gaps + white label bg: `redirect to *.authkit.app`→`redirect`, `allow-list + rate limit`→`allow-list`, `WorkOS session required`→`auth required`. Re-exported + verified. |
| — | fig-01 | AUDITED vs MANAGED_AGENTS_CONTRACT.md: managed-agents table (PK `id`, SK `version`, `instructions/skills[]`, `policy`, `model`/`active`) matches the contract schema. No drift. |

Gotchas reviewed: `id="null"` silent-drop (addressed — fig-07 uses `gnull`); `--crop` no-op for PNG and `-z` zoom-not-export are informational CLI notes, not defects. No P0/P1/P2 figure defects remain open.

## CLI reference

See `DRAWIO_CLI_NOTES.md`. Export commands of record:
- PNG (whitepaper): `drawio -x -f png -s 2 -b 10 -o out.png in.drawio`
- PDF (vector, cropped): `drawio -x -f pdf --crop -o out.pdf in.drawio`
- Gotcha: a cell with `id="null"` is silently dropped from export — never use `null`/empty ids.

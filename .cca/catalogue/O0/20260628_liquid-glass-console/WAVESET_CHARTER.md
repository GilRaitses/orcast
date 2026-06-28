# LGC — Liquid-Glass Research Console (Waveset Charter)

Lane code: **LGC**
Owner: O0 (central orchestrator), dispatched to a fresh thread
Type: implementation lane (research-first; W3 and W7 gated)
Date: 2026-06-28 (America/New_York)
repo_state_verified_against: `origin/main` @ `b9e2e13` (branch `main`)

Authoritative charter input: `LIQUID_GLASS_CONSOLE_MANIFEST.md` (repo root). That
manifest is the design language, contracts, honesty locks, rubric (M1-M10), and
wave plan (W0-W7). This file does NOT restate it. This file records the ORCAST
grounding O0 verified, the locked decisions that correct the manifest's stale
stack assumption, and the run protocol.

---

## 1. Intent (operator framing)

Stand up the same liquid-glass "Friend" console from the pax reference build,
retargeted as a whale-behavior research tool: frosted-glass surfaces over the
live map and probability cloud, a single-focus center model, self-hiding
chat/dock, edge panels, and consent-gated layout persistence. Operator: "fire
this up on a new thread to own this because it's a big project."

The six features (manifest F1-F6) and the qualification rubric (manifest M1-M10,
Part I) are the acceptance authority. W3 (design acceptance) and W7 (final
acceptance) are GATED to O0.

---

## 2. Grounding (verified by O0 before dispatch)

O0 read the real ORCAST tree at `b9e2e13`. The manifest was written against a
stale picture of the ORCAST frontend. The corrected, verified picture:

- ORCAST has THREE frontends in the repo:
  1. Root vanilla-JS app (`css/`, `js/`) — this is what the manifest cites
     (`css/base.css`, `js/forecast_transparency.js`, `js/transparency_integration.js`,
     `css/transparency_ui.css`). Confirmed present, but it is NOT the deployed
     console.
  2. `orcast-angular/` — an Angular app. Also not the live console path.
  3. `web/` — a Next.js / React / TypeScript app. This IS the live, deployed
     hackathon console at `https://orcast-h0.vercel.app`, and the surface all
     recent console, trips, streaming, and scene work has targeted.
- `web/` styling is plain CSS via `web/app/globals.css`. There is no
  `tailwind.config`. The manifest's Tailwind reference does not apply.
- `web/` already contains the analogs the console needs:
  - map / scene: `web/app/components/MapHero.tsx`, `web/app/components/scene/SalishScene.tsx`,
    `web/app/components/scene/realism/water.ts`, terrain/bathy under `web/lib/scene/**`.
  - console panels: `web/app/components/console/` (HydrophoneSignalPanel, KayakPanel,
    SidequestPanel, OrchestratorTrace), plus trip panels.
  - honesty / transparency: `web/app/components/IntegrityConditions.tsx`,
    `ConfidenceBadge.tsx`, `web/lib/scene/bathy/honesty/*` (honesty.test.ts,
    measuredOverlay.ts), `ProvenanceGraph.tsx`, `ProvenanceModal.tsx`,
    `PromotionBreadcrumb.tsx`.
  - auth / gate: `web/app/components/AuthStatus.tsx`, `web/lib/agentAuth.ts`,
    panel allowlist via the planner + `ActiveSurfaceHost.tsx`.
- An existing prose / copy gate already governs user-facing copy:
  `.cca/PROSE_GATE_RULES.md`, `.cursor/rules/prose-gate.mdc`, `.cca/CX_COPY_INVENTORY.md`,
  and the `copy-gate` battery.

---

## 3. Locked decisions (do NOT reopen)

1. **Target surface is `web/`** (Next.js / React / TypeScript), the live console.
   Root `css/` + `js/` and `orcast-angular/` are OUT of scope. The manifest's
   cited ORCAST seams (`css/base.css`, `js/forecast_transparency.js`, etc.) are
   the legacy root app and must NOT be edited. W0 confirms target with O0 as the
   first gate before any W1 design work.

2. **Stack-drift inversion.** The manifest assumes ORCAST is Angular + vanilla-JS
   and prescribes a React-to-Angular rewrite. That is FALSE for the live console.
   `web/` is React/Next, the SAME stack as the pax reference (`pax_v0`). Therefore:
   - Focus model (manifest Part C) ports near-VERBATIM as a TS module
     (`web/lib/focus/focusModel.ts` + `focusModel.test.ts` as the M4 proof).
   - GlassSurface (Part B) is a React component, not the Angular sketch in the manifest.
   - consolePreload (Part E) ports as a TS module (`web/lib/console/consolePreload.ts`).
   The Angular reference shape in the manifest is not used.

3. **Plain CSS, not Tailwind.** Design tokens (manifest Part A) drop into
   `web/app/globals.css :root`. GlassSurface paints via a `.glass-surface` CSS
   class set plus the two hard rules (AA opacity floor clamp in CSS, `blur=0`
   over the always-repainting canvas). No Tailwind utilities.

4. **Honesty layer for M2 is the `web/` components**, not the root JS:
   `IntegrityConditions.tsx`, `ConfidenceBadge.tsx`, `web/lib/scene/bathy/honesty/*`,
   provenance components. W0 enumerates the real H1-H4 captions on these surfaces.

5. **M8 prose gate is the EXISTING battery**, not net-new. New console copy runs
   through `.cca/PROSE_GATE_RULES.md` + `copy-gate`. This also discharges the
   operator's standing concern that internal / dev-facing copy (promotion,
   blocker, confidence, gate, waveset, fit, refit jargon) must never reach
   end-user surfaces. Any such leak found during the restyle is an M8 failure.

6. **Collision lock.** Two lanes are concurrently editing the SAME `web/`
   surfaces this lane touches:
   - the 3D-twin sea-level / camera lane (`web/app/components/scene/**`,
     `SalishScene.tsx`, `scene/realism/water.ts`),
   - the console ghost-text / suggestion-bubble lane (chat input + `ExploreGuidePanel.tsx`).
   LGC F1/F2 (glass over the map canvas) and F3 (chat self-hide) overlap both.
   LGC must `git pull --rebase` before editing, treat `scene/**` and the chat
   shell as shared convergence files, and coordinate the edit order through O0.
   Do not edit a shared file in parallel with another lane.

7. **Researcher-gate do-not-touch seams (M7).** The ORCAST analog of the pax
   `researchAuth.ts` + directive allowlist is the server-side gate plus the panel
   allowlist (`web/lib/agentAuth.ts`, planner panel allowlist, per-pane server
   gates). Style never edits these. Public reach unchanged: the public surface
   must not be able to summon a researcher pane even via chat. The preload
   restore path is a different trust tier and must call the console open API
   directly, never through the agent-directive allowlist parser.

8. **The map is the focus sink.** The focus model's universal sink
   (`{kind:"map"}`) binds to the live map/scene component. W0 confirms whether
   that is `MapHero.tsx`, `SalishScene.tsx`, or a composed host, so the focus
   binding wires to the right surface.

---

## 3a. Folded-in console UX scope (operator add, 2026-06-28)

Beyond the manifest's F1-F6, this lane also owns three console-UX behaviors the
operator requested. They were grounded against the real `web/` console (the
anonymous home is `AdaptiveExplore`, mounted at `web/app/page.tsx:20`):

1. **Ghost-text composer (F3-adjacent).** The home composer is a plain controlled
   `<textarea>` in `web/app/components/AdaptiveExplore.tsx` (~335-343) with
   button-only submit and no Enter-to-send. The Tab-accept / Enter-run ghost-text
   pattern ALREADY exists on `/ask` in `web/app/components/SightingCheckPanel.tsx`
   (`handleKeyDown` ~155-167; `.chat-composer`/`.chat-ghost`/`.chat-hint` in
   `web/app/globals.css` ~320-397). Port that pattern in, and change the initial
   `message` state from `STARTER_PROMPTS[0]` to `""` so ghost text is visible.
2. **Persistent-history replay.** History persists in Postgres for completed
   narrations (`exploration_turns`, `session_store.list_turns` exists), but no GET
   route exposes it and the UI keeps turns in React state only, so a refresh loses
   them. Add a turns GET route plus client hydration (and persist `session_id` in
   `sessionStorage`). This is a real new API surface, not a restyle.
3. **Proactive AI-question bubbles.** No floating proactive bubble exists today.
   Feed a new overlay from data the planner already returns (sidequest
   `items[].prompt`, branch prompts, `prepare.annotations`, stream `meta.deep_links`),
   or add a planner `suggested_questions` field. Render as glass bubbles that
   recede under the focus model, never concealing an error or a needed control (M5).

These fold under the manifest's focus + self-hide model. They share the chat shell
and `ActiveSurfaceHost` with the copy-leak redaction lane (see §3 collision lock).

## 4. Wave structure (manifest Part J, W0-W7)

Run under O0 with parallel subagents per wave. Gated waves require explicit O0 go.

| Wave | Work | Gate |
|---|---|---|
| W0 | Research: read the real `web/` seams (map/scene host, chat/agent UI, honesty components, agentAuth + panel allowlist), confirm the **target surface** with O0, record drift vs the manifest. One adversarial member owns honesty-caption AA legibility, canvas perf, researcher-gate, self-hide-conceals. | **report to O0 (target-surface confirm)** |
| W1 | Candidate design space (token plan in globals.css, focus-model binding options for React, persistence options) scored against M1-M10 | — |
| W2 | Select design; architecture note | — |
| W3 | **Design acceptance** on prototype evidence (must clear M1, M2, M4, M5, M6, M7; credible plan for M3, M8, M9, M10) | **GATED** |
| W4 | Implementation: tokens, GlassSurface, focus model + React binding, self-hide, edge panels, preload | — |
| W5 | Testing: static gates (M8 via copy-gate + tsc/lint), focus unit test (M4), Playwright walkthrough (M9), perf A/B (M3), Read-verified frames (M10), researcher-gate (M7) | — |
| W6 | Adversarial review; exits at zero open P0/P1 | — |
| W7 | **Final acceptance**: M1-M10 all hold on the running app with Read-examined evidence; gated to O0 for commit / push / promotion | **GATED** |

Waves may repeat on a failed gate. The manifest + this charter + the registry
stay authority across repeats.

---

## 5. Acceptance criteria

The manifest's M1-M10 rubric (Part I) verbatim. No measure passes by assertion;
each pass cites the file or the Read-examined rendered frame it was checked
against. M10 requires a Read-examined frame for every visual claim. W7 ships only
with Read-examined runtime evidence for all of M1-M10.

Execution-wiring requirement (waveset-orchestration skill, EXECUTION_WIRING.md):
W5/W6/W7 gates are RUN as harnesses, not asserted. The perf A/B (M3) and the
walkthrough (M9) write their JSON summary plus log to `gate_captures/` in this
lane home. Read-examined frames for M10 are saved to `gate_screenshots/`.

---

## 6. Escalation (operator-protection catch)

The dispatched orchestrator answers to the dispatching O0, NOT the human
operator. Pause and return the question to O0 (do not solicit the operator
directly) on any of:
- the target-surface confirmation (W0 first gate),
- any manifest seam that is missing or renamed in `web/` (do not fabricate it),
- any honesty caption that cannot render at AA contrast over glass (M2 fail),
- any researcher-gate ambiguity (M7),
- any collision with the twin lane or the console ghost-text lane on a shared file,
- W3 and W7 (both gated),
- any commit / push / deploy (gated to O0).

---

## 7. Return contract

1. On hydration: ack the lane, the locked decisions, and the target-surface
   question, then start W0.
2. After W0: return to O0 a drift report (manifest vs real `web/` seams), the
   target-surface recommendation with evidence, the enumerated H1-H4 captions,
   the identified researcher-gate seam, and the collision map against the two
   concurrent lanes. Pause for the O0 target-surface gate before W1.
3. Thereafter: report at each wave boundary; pause at W3 and W7; never commit or
   push without O0 go.

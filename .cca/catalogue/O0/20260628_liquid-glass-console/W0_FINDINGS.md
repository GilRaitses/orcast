# LGC W0 Findings and Target-Surface Confirmation

Lane code: **LGC**
Wave: **W0** (read-only research, drift confirmation, target-surface determination)
Owner: LGC fresh-thread owner, reporting to O0
Date: 2026-06-28 (America/New_York)
Repo state read: branch `main` @ `d19fd56` (charter pinned `b9e2e13`; tree has advanced, all charter-cited seams still present and verified at `d19fd56`)
Discipline: read-only on product code. No edit under `web/` or `src/`. No commit, push, or deploy. No token drop (that is LGC-W4, after the W3 gate).

This doc is the W0 return to O0. Every claim cites the exact file and line range read.

---

## 1. Target-surface confirmation, `web/` (recommended RATIFY)

The live console is the Next.js / React / TypeScript app under `web/`. Evidence:

- `web/package.json` declares `"name": "orcast-web"`, `next ^14.2.5`, `react ^18.3.1`, `react-dom ^18.3.1`, `typescript ^5.5.3`, plus the r3f scene stack (`@react-three/fiber ^8.18.0`, `@react-three/drei ^9.122.0`, `three ^0.169.0`) and Google Maps (`@vis.gl/react-google-maps`). See `web/package.json:1-42`.
- The home route renders the live console: `web/app/page.tsx:9-21` is an async server component that resolves auth server-side and returns `<AdaptiveExplore signedIn={signedIn} />`. `AdaptiveExplore` is the anonymous home surface.
- The home surface mounts the map/scene host: `web/app/components/AdaptiveExplore.tsx:294-300` mounts `<SceneHost ... />`, which lazy-loads the r3f scene `SalishScene` and falls back to `MapHero` Google Maps when WebGL is unavailable (`web/app/components/scene/SceneHost.tsx:11-18, 40-83`).

Root `css/` + `js/` and `orcast-angular/` are out of scope per the charter §3.1 locked decision. Nothing in W0 contradicts that. No improvisation of a different target.

**Recommendation to O0: confirm `web/` as the LGC target surface. The charter's locked decision §3.1 holds against the real tree at `d19fd56`.**

---

## 2. Confirmed drift vs the manifest

The charter (§2, §3) already inverted the manifest's stale stack picture. W0 confirms that inversion against the live tree, and confirms the manifest's own corrected sections are right.

### 2.1 Stack is React/Next, not Angular + vanilla-JS

The manifest's authoritative body now states the target is `web/` Next 14 / React 18 / TS 5 and that the port is near-verbatim React (`LIQUID_GLASS_CONSOLE_MANIFEST.md:15-22`, Part B `:144-156`, Part C `:160-166`, Part K `:406-420`). That matches the live tree (§1 evidence). The manifest's Angular shape survives only as an explicit "legacy fallback only (NOT the target)" note (`LIQUID_GLASS_CONSOLE_MANIFEST.md:151-154`). So the React-to-Angular rewrite prescription is correctly marked wrong for the live target. The port lands as TS/React:

- GlassSurface as a React component at `web/app/components/ui/GlassSurface.tsx` (does not yet exist; glob returned 0).
- Focus model as a pure TS module at `web/lib/focus/focusModel.ts` plus its test (the `web/lib/focus/` directory does not yet exist; glob returned 0).
- consolePreload as a TS module at `web/lib/consolePreload.ts` (does not yet exist; glob returned 0).

The pax reference (`pax_v0`) is an external repo, not present in this tree (glob for `**/pax_v0/**/GlassSurface.tsx` returned 0). The port is a copy-in from that external reference, consistent with the manifest's provenance note.

### 2.2 Styling is plain CSS, no Tailwind

No `tailwind.config.*` exists anywhere in the repo or under `web/` (both globs returned 0 files). Styling is plain CSS via `web/app/globals.css`. The manifest's Tailwind reference does not apply, matching charter §3.3.

### 2.3 `:root` holds base tokens only, the LGC glass tokens are absent

`web/app/globals.css:1-13` defines the `:root` block. It contains only the base palette:

```1:13:web/app/globals.css
:root {
  --bg: #0a0e14;
  --surface: #121821;
  --surface-2: #1a2230;
  --border: #233040;
  --text: #e6edf3;
  --text-muted: #8b97a7;
  --accent: #4fb8d8;
  --pass: #46c08a;
  --fail: #e0625f;
  --warn: #d8b24f;
  --radius: 10px;
}
```

None of the manifest Part A glass tokens are present. A repo-wide grep for `--glass-`, `--text-ink`, `--accent-ink`, `--warm-ink` across `web/` returns zero matches in any CSS or `:root` context. So the Part A drop (LGC-W4) is genuinely net-new, the `TOKEN_HANDOFF.md` dependency is real, and the downstream consumers (TWIN W-LABELS, demo B3) are correctly blocked.

The base set is broader than the charter shorthand "(--bg/--surface/--accent/--warn)". The full base set is `--bg`, `--surface`, `--surface-2`, `--border`, `--text`, `--text-muted`, `--accent`, `--pass`, `--fail`, `--warn`, `--radius`. The glass/ink families are the additive layer LGC-W4 introduces; no rename or removal of the base set is implied.

### 2.4 One pre-existing `backdrop-filter` over the scene region (M3 watch item)

A repo-wide grep for `backdrop-filter` across `web/` returns exactly one component, `web/app/components/scene/SearchAffordance.tsx:44-47`, which paints `backdrop-filter: blur(14px) saturate(150%)` on a surface inside the `scene/` tree. If that surface composites over the always-repainting r3f canvas, it already conflicts with the manifest's blur=0-over-canvas rule (Part B rule 2, `:119-123`; `TOKEN_HANDOFF.md:28-34`). This is a pre-existing condition, not introduced by LGC, but the LGC restyle and the M3 perf gate must reconcile it. Flagged below under M3 and as a collision touch-point.

---

## 3. Grounded collision surfaces

The charter §3.6 collision lock names two concurrent lanes. W0 grounds the real shared paths.

| Shared file | LGC need (manifest F#) | Twin camera/labels lane | Ghost-text / bubble lane | Evidence |
|---|---|---|---|---|
| `web/app/globals.css` | `:root` Part A tokens (LGC-W4); `.glass-surface` class; chat-shell glass | reads `--glass-tint-cool` + opacity floor + scrim + ink + hairline for `.scene-label` | reuses `.chat-composer`/`.chat-ghost`/`.chat-hint` | `web/app/globals.css:1-13` (`:root`), `:320-404` (chat-composer/ghost/hint) |
| `web/app/components/scene/SalishScene.tsx` | F1/F2 glass over the map canvas; focus `{kind:"map"}` sink binding | owns the `.scene-label` family + scene mount + camera | n/a | `web/app/components/scene/SalishScene.tsx:5` (drei `Html`), `:363-365` (`.scene-beacon-label` over canvas), `:76-79, 737-743` (modeled-honesty labels) |
| `web/app/components/scene/realism/water.ts` | F1 glass-over-water perf (M3) | owns sea-level / water | n/a | file exists (glob), charter §3.6 |
| chat shell (`AdaptiveExplore.tsx` home composer; `SightingCheckPanel.tsx` `/ask` ghost-text; `ExploreGuidePanel.tsx`) | F3 self-hide; folded-in ghost-text + history + bubbles | n/a | ghost-text composer + proactive bubbles | `web/app/components/AdaptiveExplore.tsx:75, 335-353`; `web/app/components/SightingCheckPanel.tsx:155-167, 258-288`; `web/app/components/ExploreGuidePanel.tsx` |
| `web/app/components/ActiveSurfaceHost.tsx` | F4 dock self-hide controller; audience redaction | n/a | shares surface controller with copy-leak lane | `web/app/components/ActiveSurfaceHost.tsx:371-420` |

Key grounded facts for the lock:

- The scene already renders an over-canvas DOM label via drei `<Html>` (`SalishScene.tsx:363-365`, class `.scene-beacon-label`). This is the exact surface the twin W-LABELS lane will restyle as `.scene-label`, and the exact surface where the M3 blur=0 rule bites. LGC owns the `:root` token drop and the `.glass-surface`/chat-shell classes; the twin lane owns `.scene-label` and the scene mount. Neither edits the other's region. Edits to `globals.css` and `SalishScene.tsx` serialize through O0.
- The ghost-text precedent is real and reusable, not net-new. `SightingCheckPanel.tsx:155-167` implements Tab-accept on an empty box and Enter-to-run; `:258-288` renders `.chat-composer` + `.chat-ghost` + `.chat-hint`; the classes live at `globals.css:320-404`. The folded-in F3-adjacent work ports this pattern to the home composer.
- Minor drift vs charter §3a.1: the home composer's initial `message` state is already `""`, not `STARTER_PROMPTS[0]` (`AdaptiveExplore.tsx:75`). The charter's "change initial state to empty" step is already satisfied, so that sub-step is a no-op. The composer is still a plain `<textarea>` with button-only submit and no Enter-to-send (`AdaptiveExplore.tsx:335-353`), so the ghost-text port itself is still needed.

---

## 4. Honesty captions H1-H4 (M2 enumeration)

All four families exist today on `web/` surfaces. None is absent. H4 is the weakest and needs explicit attention at W3.

| Lock | Caption intent | Live surface + evidence | State |
|---|---|---|---|
| H1 modeled-not-observed | forecast is modeled, not an observed sighting | `ActiveSurfaceHost.tsx:52` "This forecast is modeled, not a direct observation. It is a likelihood, not a certainty."; `:300` local-area variant; scene honesty label "modeled, not measured" via `attachModeledLabel` (`SalishScene.tsx:69, 737-743`); `ProvenanceModal.tsx:64-66` out-of-region | present, explicit |
| H2 detection-confidence | hydrophone/CV detection is a confidence score, not ground truth | honesty-label ladder measured/published/modeled/heuristic rendered as badges (`ActiveSurfaceHost.tsx:148-166`, `SidequestPanel.tsx:15-57`); hydrophone "Annotate this detection" gated action (`HydrophoneSignalPanel.tsx:79`) | present via label ladder; detection-confidence wording is implicit, verify at W3 |
| H3 prediction-not-certainty | probability/accuracy is a prediction, not a guarantee | `ConfidenceBadge.tsx:25-28` "the forecast is always shown... governed by the fitness gates and a human promotion step"; `KayakPanel.tsx:132-134` "Harmonic tide predictor, not observed currents"; `ActiveSurfaceHost.tsx:52, 300` "a likelihood, not a certainty" | present, explicit |
| H4 agent-simulated | multi-agent transcript is machine-generated, not expert testimony | chat labels the assistant "Guide" (`AdaptiveExplore.tsx:379`); orchestrator trace exposes agent ids only to the reviewer audience, redacted for public (`OrchestratorTrace.tsx:18-20, 57-65`; `ActiveSurfaceHost.tsx:383-392`) | **no explicit "machine-generated, not expert" caption found on the public chat shell** |

W0 finding for O0: H1 and H3 are explicit and strong. H2 reads through the honesty-label ladder rather than a sentence, so confirm the detection-confidence meaning survives the restyle. H4 has no explicit public-facing "machine-generated, not human expert" disclaimer on the chat shell; the public path instead redacts agent internals. This is a research-level gap, not a fabrication. Per escalation, W0 does not invent a caption. O0 should rule at the W3 gate whether H4 needs an explicit public caption or whether the redaction posture satisfies M2. All four must clear AA over glass at W3/W5, proven on a Read-examined worst-case composited frame (M1/M2/M10), not asserted.

---

## 5. Researcher-gate seam (M7)

The ORCAST analog of the pax `researchAuth.ts` plus directive allowlist is a server-side identity gate plus an audience split, not a single client file. Evidence:

- `web/lib/agentAuth.ts:13-46` is the server-side identity resolver. `agentUserFromHeaders` validates `x-orcast-agent-key` against `ORCAST_AGENT_KEY` and never exposes the key to the browser bundle (`:12, :8`). `resolveReviewer` resolves a WorkOS session or the agent key for keyed proxy routes (`:27-36`). `reviewerProxyHeaders` stamps the trusted-proxy + reviewer-role headers (`:38-46`).
- The page resolves auth server-side only and passes a boolean `signedIn` down; every surface stays visible to anonymous users (`web/app/page.tsx:9-21`, comment `:6-8`).
- The audience redaction is enforced in `ActiveSurfaceHost.tsx`: `audience="public"` is passed from the anonymous home (`AdaptiveExplore.tsx:363`), and the host hides reviewer internals (agent ids, skill manifest, schema version, promotion/confidence internals) for the public audience (`ActiveSurfaceHost.tsx:18-22, 48-61, 383-392`).

M7 rule for LGC: style never edits `web/lib/agentAuth.ts`, the audience split, or the per-pane server gates. Public reach must stay unchanged. The preload restore path (LGC-W4 / Part E) is a different trust tier and must call the console open API directly, never through any agent-directive allowlist parser. No researcher-pane summon path through chat may be introduced by the restyle.

One ambiguity to flag (not a blocker for the target-surface gate): the manifest describes a pax-style agent-directive allowlist parser as the do-not-touch seam, but the live `web/` enforces reach through the server identity gate plus the `ActiveSurfaceHost` audience split rather than a single named directive-allowlist file. W1 should map the exact preload-restore call site against this real seam shape so the Part E trust-tier rule binds to a concrete API, not the pax file name.

---

## 6. Focus sink binding (charter §3.8)

The map focus sink `{kind:"map"}` binds to a composed host, not a single component. The chain is `AdaptiveExplore` (`:294-300`) mounts `SceneHost` (`SceneHost.tsx:40-83`), which renders `SalishScene` (r3f, the primary surface) or `MapHero` (Google Maps fallback). The focus binding should target the `SceneHost` composition (the durable mount), so the sink resolves whether the scene or the fallback is live. W1 fixes the exact binding point; W0 confirms it is the `SceneHost`-rooted scene, with `SalishScene.tsx` as the live primary and `MapHero.tsx` as the fallback.

---

## 7. Candidate design space scored against M1-M10 (research level, no build)

Candidate = Part A tokens into `web/app/globals.css :root`; GlassSurface React component + `.glass-surface` class; focus model as pure TS module bound via a React `FocusProvider`; consent-gated `localStorage` preload calling the console open API directly. Research-level read only. No measure passes here; these are feasibility reads for the W1/W3 plan.

| M | Measure | W0 research read | Risk |
|---|---|---|---|
| M1 | Text contrast on glass | Feasible. Ink-on-glass model + AA opacity floor clamp in CSS (`max(opacity, var(--glass-opacity-floor))`) is portable into plain CSS. Worst case is over the r3f canvas. | med. must prove on a Read-examined worst-case composited frame, not by code |
| M2 | Honesty-caption legibility/truth | All four families exist (§4). H1/H3 explicit. | med. H2 wording implicit, H4 has no explicit public caption, both need a W3 ruling |
| M3 | Canvas perf no-regression | The blur=0-over-canvas rule is enforceable via the GlassSurface contract. One pre-existing over-region `backdrop-filter` in `SearchAffordance.tsx:44-47` must be reconciled. | med-high. pre-existing blur over the scene, perf A/B must include it |
| M4 | Focus-model determinism | Strong. The reducer + hide derivation is pure and framework-free (manifest Part C); ports as `web/lib/focus/focusModel.ts` with the ported state-table test as the proof. | low |
| M5 | Self-hide never conceals | Feasible. `hidden = shouldHide && !forceShown` plus force-shown predicates for error/awaiting-confirm/consent/pending-review. The home already keeps errors visible (`AdaptiveExplore.tsx:354`) and an `aria-live` narrating state (`:381`). | low-med. must drive thinking + error in the M9 walkthrough |
| M6 | No covert persistence | Feasible. One key `orcast_console_preload_v1`, consent-gated, no telemetry, step log in-memory. No such key exists yet, so the ledger is clean to introduce. | low |
| M7 | Researcher-gate integrity | Seam grounded (§5). Style does not touch the gate, preload is a different trust tier. | med. bind Part E to the real seam shape, not the pax file name |
| M8 | Build + prose gates | Existing `copy-gate` battery + `tsc --noEmit` + `next lint` + `node --test lib/**/*.test.mts` (`web/package.json:10-12`). New console copy runs the prose gate, internal jargon leaking to users is a fail. | low-med. copy-leak watch on chat + dock |
| M9 | Runtime walkthrough | Playwright is wired (`web/playwright.config.ts` per registry; demo scripts at `web/package.json:13-17`). Target spec `web/e2e/orcast-research-walkthrough.spec.ts`. | low |
| M10 | Visual verification | Every visual claim needs a Read-examined frame in `gate_screenshots/`. No visual pass by code. | process gate |

Tie-breakers (manifest Part I) favor this candidate: it reuses ORCAST's existing transparency layer (§4) and the existing ghost-text + Playwright + copy-gate machinery rather than net-new mechanisms, and it minimizes convergence-file edits by serializing `globals.css` and `SalishScene.tsx` through O0.

---

## 8. Readiness for LGC-W1 and what O0 must ratify at the target-surface gate

W0 is complete and read-only. No product code touched. No tokens dropped.

**Ready for W1** once O0 ratifies the target-surface gate.

What O0 must ratify before W1 starts:

1. **Target surface = `web/`** (Next 14 / React 18 / TS 5), confirmed against the live tree at `d19fd56` (§1). Root `css/`+`js/` and `orcast-angular/` stay out of scope.
2. **The drift is confirmed and benign**: stack is React/Next (not Angular), styling is plain CSS (no Tailwind), and the Part A glass/ink tokens are genuinely absent from `:root` (§2). The Part A drop is net-new and stays in LGC-W4 after the W3 gate. The `TOKEN_HANDOFF.md` dependency on TWIN W-LABELS and demo B3 is real.
3. **Collision lock is grounded** to real paths (§3): `globals.css`, `scene/SalishScene.tsx`, `scene/realism/water.ts`, the chat shell, and `ActiveSurfaceHost.tsx`. LGC must `git pull --rebase` before editing and serialize every edit to those files through O0.
4. **Two items O0 should rule on at W3, not now** (W0 does not improvise these):
   - H4 has no explicit public "machine-generated, not human expert" caption on the chat shell (§4). Decide whether M2 requires one or whether the existing redaction posture suffices.
   - The pre-existing `backdrop-filter` in `scene/SearchAffordance.tsx:44-47` must be reconciled with the M3 blur=0-over-canvas rule (§2.4, §7-M3). Decide whether the LGC M3 gate owns that reconciliation or whether it routes to the twin lane.
5. **M7 seam shape note** (§5): the live researcher gate is the server identity resolver plus the `ActiveSurfaceHost` audience split, not a single pax-style directive-allowlist file. W1 binds the Part E preload trust-tier rule to the real seam.

LGC pauses here at the target-surface gate per the charter return contract (§7.2). No W1 work begins until O0 ratifies.

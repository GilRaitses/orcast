# ORCAST Liquid-Glass Research Console — Charter Manifest

Date 2026-06-28 (America/New_York)
Status portable charter input — for ORCAST O0 to charter a waveset
Source of truth (reference implementation) `pax_v0` @ commit `793b86e` (LGC waveset, lane `20260628_liquid-glass-console`)

## 0. Purpose

This manifest carries the full liquid-glass console design language and behavior
set from the pax "Friend" console into ORCAST, so ORCAST can stand up the **same
console** — frosted-glass surfaces over a live map, a single-focus center model,
self-hiding chat/dock, and consent-gated layout persistence — but built as a
**whale-behavior research tool** instead of a pedestrian-routing tool.

**Target surface (verified): `web/` — Next.js 14 + React 18 + TS 5 (`orcast-web`).**
This is the SAME stack as the pax reference, so the port is near-verbatim React,
not a framework rewrite. The orcast LGC waveset is already chartered against `web/`
(`docs/devpost/waves.registry.yaml`, family `LGC`, `LGC-W0…W7`); this manifest is
its design input. The legacy `orcast-angular/` and the root `css/`+`js/` bundles
are NOT the target and should not receive the port. Where a legacy surface ever
needs it, the design tokens and the (framework-free) focus model still port as-is
and GlassSurface reduces to a CSS utility — but the live work is `web/`.

It is **not** a code drop. It is the charter input: tokens, contracts, behavior
rules, honesty locks, a qualification rubric, and a wave plan ORCAST can run
under its own orchestrator with its own subagents.

---

## 1. What you get (scope)

Six features, mirroring the pax F1–F6, retargeted to whale research:

| ID | Feature | ORCAST meaning |
|---|---|---|
| F1 | Liquid-glass design language | Frosted translucent surfaces over the Google-Maps + probability-cloud canvas |
| F2 | Map-centered single focus | The San Juan Islands map owns the center; one surface focused at a time |
| F3 | Chat (research agent) self-hide | The Gemma multi-agent chat recedes when not focused, **never** while thinking-with-an-error or awaiting a researcher confirm |
| F4 | Console dock self-hide | The analysis console dock recedes to a glass reopen pill when not focused |
| F5 | Frameless glass edge panels | Sightings / Hydrophones / Environmental panels summoned from edges, hidden at rest |
| F6 | Console preload | A researcher saves a console layout (which panes, orientation) and it restores on reload — consent-gated, no covert telemetry |

Hard non-goals (locked, same as pax): no change to the data trust model, no
weakening of honesty captions, no covert persistence, no change to who can see
researcher-only panes.

---

## 2. Part A — Design tokens (port verbatim)

Framework-agnostic CSS custom properties. Drop into the `:root` of
`web/app/globals.css` (the orcast `web/` target; `css/base.css` only if a legacy
surface is ever in scope). Channels are space-separated RGB so they compose with `rgb(... / a)`.
These values are the audited set from the reference build — do not edit a value
without re-running the M1 contrast gate.

```css
:root {
  /* fills */
  --glass-tint: 248 250 252;        /* frost base (chat / dock / panels) */
  --glass-tint-cool: 226 232 240;   /* "instrument" frost for researcher / detection panes */
  --glass-hairline: 255 255 255;    /* light inner border, used @ .5 alpha */
  --glass-scrim: 11 16 21;          /* = ink; thin AA-insurance wash under text */

  /* text/glyph INK rendered on glass (never as a fill) */
  --text-ink: 11 16 21;             /* primary text on glass */
  --text-muted-ink: 51 65 85;       /* muted text on glass (slate-700) */
  --accent-ink: 6 95 70;            /* deep green accent AS text/glyph */
  --warm-ink: 154 52 18;            /* deep terracotta warning AS text/glyph */

  /* opacity ladder */
  --glass-opacity-floor: 0.62;      /* HARD AA clamp floor on every surface */
  --glass-opacity-hud: 0.66;        /* map HUD chips */
  --glass-opacity-dock: 0.74;       /* console dock */
  --glass-opacity-cv: 0.78;         /* denser: live-frame/detection panes (unbounded luminance) */
  --glass-scrim-alpha: 0.14;

  /* blur ladder — ONLY for surfaces NOT over the always-repainting canvas */
  --glass-blur: 12px;
  --glass-blur-strong: 16px;
}
```

Token rules:
- **Ink-on-glass, not glass-on-color.** Accent and warning are rendered as text
  and glyph color (`--accent-ink`, `--warm-ink`), never as a surface fill. The
  surface is always frost/cool; meaning is carried by ink contrast.
- **Cool tint for instruments.** Detection/CV/probability panes that sit over
  unbounded-luminance content use `--glass-tint-cool` + a scrim, not the plain
  frost.

---

## 3. Part B — GlassSurface primitive (contract)

A purely presentational surface. It holds no domain state and no focus state. It
paints: a translucent frost/cool fill, an optional AA scrim wash, an optional
light hairline, and an optional capped `backdrop-filter` blur.

### Prop / attribute contract

| Prop | Type | Default | Meaning |
|---|---|---|---|
| `opacity` | number | `0.74` | Requested fill alpha; **clamped** to `max(opacity, floor)` |
| `blur` | number (px) | `12` | `backdrop-filter` radius; **`0` disables `backdrop-filter` entirely** |
| `tint` | `frost \| cool` | `frost` | `frost` = chat/dock/panels; `cool` = detection/instrument panes |
| `scrim` | boolean | `false` | Paint AA-insurance wash under children (required over live frames) |
| `hairline` | `light \| none` | `light` | 1px inner border at `rgb(var(--glass-hairline)/.5)` |
| `fadeOnIdle` | boolean | `false` | Recede to ~0.70 opacity when idle, full on hover/focus-within |
| `radius` | `lg \| xl \| 2xl` | `xl` | Corner radius |
| `elevation` | `flat \| raised` | `raised` | Shadow weight |

### Two HARD rules (do not relax without re-running the gate)

1. **AA opacity floor (M1 guardrail).** Fill alpha is clamped in CSS to
   `max(opacity, var(--glass-opacity-floor))`. The token (`0.62`) is the single
   source of truth: passing a lower `opacity` can never drop below the audited
   floor; raising the token re-clamps every surface at once.
2. **`blur=0` over the canvas (M3 rule).** Every surface mounted over the
   always-repainting map/probability-cloud canvas (map HUD chips, detection
   overlays, live-frame panes) MUST pass `blur=0` — fill + scrim only, no
   per-frame backdrop re-sampling. `backdrop-filter` is reserved for the chat
   shell and the console dock (capped at `--glass-blur` / `--glass-blur-strong`).

### Fill composition (the exact CSS the integrator paints)

```css
/* fill, with AA floor enforced in CSS so the token governs */
background: rgb(var(--glass-tint) / max(0.66, var(--glass-opacity-floor)));

/* scrim variant (wash painted over fill, behind children) */
background:
  linear-gradient(rgb(var(--glass-scrim)/var(--glass-scrim-alpha)),
                  rgb(var(--glass-scrim)/var(--glass-scrim-alpha))),
  rgb(var(--glass-tint-cool) / max(0.78, var(--glass-opacity-floor)));

/* blur ONLY when blur>0 and NOT over the canvas */
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);

border: 1px solid rgb(var(--glass-hairline) / 0.5);
```

### Port target: `web/` React (near-verbatim)

Because `web/` is React/TS, copy `pax_v0/components/ui/GlassSurface.tsx` into
`web/app/components/ui/GlassSurface.tsx` essentially as-is (adjust import aliases
to the orcast `web/` tsconfig paths). No rewrite. The prop contract above is the
React component's prop contract unchanged.

Legacy fallback only (NOT the target): for the Angular `orcast-angular/` or the
root `css/`+`js/` bundles, the same contract reduces to a `.glass-surface` CSS
class set plus a `data-blur="0"` attribute selector that suppresses
`backdrop-filter`. Do not port there unless a directive explicitly says so.

Reference file: `pax_v0/components/ui/GlassSurface.tsx` → `web/app/components/ui/GlassSurface.tsx`.

---

## 4. Part C — Focus model (port verbatim, framework-free)

The single source of truth for "which surface owns the center right now." It is
intentionally React-free and side-effect-free so it can be unit-tested
exhaustively. **Copy this module as-is into `web/lib/focus/focusModel.ts`**; only
the UI binding (`FocusProvider`) is framework-specific and it is already React here.

### Invariants (these ARE the M4 gate)

1. `active` is a **single** value — exactly one focus target at a time, structural not convention.
2. `claim` is **total** — every `(active, target)` pair has a defined next state (it overwrites).
3. `yield` is **total + idempotent** and always resolves to the map. The map is the universal sink: every state has a one-hop path back to center. **No dead-ends.**
4. `pending` (chat "thinking") is **NOT stored** in focus state. It is a render-time input passed by the chat subscriber, so thinking-flicker never churns focus.

### Targets (ORCAST vocabulary)

```typescript
export type PanelEdge = "left" | "right" | "bottom";

// ORCAST console views (replace pax inspect/comparison/hub_cutaway):
export type ConsoleView = "sighting" | "detection" | "forecast" | "dive";

export type FocusTarget =
  | { kind: "map" }                          // San Juan Islands map + probability clouds (rest state / sink)
  | { kind: "chat" }                         // Gemma multi-agent research chat
  | { kind: "panel"; edge: PanelEdge }       // edge panels: sightings / hydrophones / environmental
  | { kind: "console"; view: ConsoleView };  // analysis console
```

### Reducer + hide derivation (verbatim logic)

```typescript
export interface FocusState { active: FocusTarget; }
export type FocusAction = { type: "claim"; target: FocusTarget } | { type: "yield" };

export const INITIAL_FOCUS_STATE: FocusState = { active: { kind: "map" } };

export function focusReducer(state: FocusState, action: FocusAction): FocusState {
  switch (action.type) {
    case "claim": return { active: action.target };
    case "yield": return { active: { kind: "map" } };
  }
}

export type FocusSurface = "chat" | "dock";

// hide BEFORE the force-shown override
export function shouldHideByFocus(active: FocusTarget, surface: FocusSurface, pending = false): boolean {
  switch (surface) {
    case "chat": return active.kind !== "chat" || (active.kind === "chat" && pending);
    case "dock": return active.kind !== "console";
  }
}

// final decision the subscriber renders against
export function isHiddenByFocus(active: FocusTarget, surface: FocusSurface, forceShown: boolean, pending = false): boolean {
  return shouldHideByFocus(active, surface, pending) && !forceShown;
}
```

Reference files: `pax_v0/lib/focus/focusModel.ts` (+ `focusModel.test.ts` is the
M4 determinism proof — port the test too), bound via
`pax_v0/components/focus/FocusProvider.tsx`.

---

## 5. Part D — Self-hide behavior (M5)

- **Chat (F3)** hides when it is not the focus target. While focused **and**
  thinking (`pending`), it also recedes — except the force-shown override.
- **Dock (F4)** hides when the console is not the focus target, receding to a
  glass reopen pill.
- **Force-shown override** can only ever keep a surface **shown** — it can never
  conceal one. This is the strictly-safer posture: `hidden = shouldHide && !forceShown`.

### ORCAST force-shown predicates (M5 — never conceal a needed control)

The chat/dock must register a `forceShown` predicate that returns `true` when any
of these is active, so self-hide can never bury them:

- an agent/network **error** is shown,
- the chat is **awaiting a researcher confirm** (e.g. "label this detection?"),
- a **consent dialog** is open (preload save, data export),
- a **detection-review action** the researcher must resolve is pending.

M5 threshold: zero concealed errors or needed controls, proven by driving a
thinking state **and** an error state in the walkthrough and Reading the frames.

---

## 6. Part E — Console preload persistence (M6)

Consent-gated, versioned-JSON `localStorage` of a researcher-chosen console
layout, plus an in-memory step log. Port the contract; rename the key.

### Persisted key (exactly ONE)

```
orcast_console_preload_v1
```

### Payload schema

```typescript
interface ConsolePreloadV1 {
  v: 1;
  saved_at: string;        // ISO, injected on save
  consent: true;           // a write is REFUSED unless this is true
  panes: string[];         // registry pane keys to restore
  orientation: "auto" | "row" | "column";
  intent?: string;         // coarse purpose, for dedupe
  title?: string;
}
```

### M6 ledger (the gate)

- Exactly one persisted key is introduced.
- `save()` writes **only** when `consent === true`; no write occurs on import.
- **No** behavioral / identity / timing / telemetry fields are persisted — only
  the layout essentials + `saved_at` + `consent`.
- The **step log** (open/close/dedupe/preload_apply, timestamp, source, panes) is
  **in-memory only**, never persisted, no free-text/user-content fields.
- SSR/`typeof window` guard + `try/catch` on every storage call.

### M7 trust-tier rule (carries directly)

A preload is a **different trust tier** than an agent-emitted directive. The
restore path must call the console open API **directly** and MUST NOT pass
through the agent-directive allowlist parser (which strips researcher panes).
Per-pane server gates remain the access authority.

Reference file: `pax_v0/lib/consolePreload.ts`.

---

## 7. Part F — Honesty locks (ORCAST domain)

ORCAST already renders honesty/transparency captions on the `web/` surfaces
(gate-status, provenance, and out-of-region disclaimers — the legacy bundle's
`js/forecast_transparency.js` / `css/transparency_ui.css` are the non-target
analog). The liquid-glass restyle MUST preserve those captions: present, legible
at AA contrast, unchanged in meaning, on every surface they appear on.

Locked caption families (whale-research analogs of the pax modeled/CV/induction set):

| Lock | Caption intent | Where it must remain |
|---|---|---|
| H1 modeled-not-observed | PINN forecast is a **modeled probability**, not an observed sighting | probability-cloud overlay + forecast pane |
| H2 detection-confidence | Hydrophone/CV detection is a **confidence score**, not confirmed ground truth | detection/hydrophone panes |
| H3 prediction-not-certainty | "87% accuracy" / probability zones are **predictions**, not guarantees | forecast HUD + console |
| H4 agent-simulated | Multi-agent transcript reasoning is **machine-generated**, not expert testimony | chat shell |

Threshold (M2): no caption dropped, dimmed below AA, or reworded to weaken the
disclaimer. Any new console copy passes a prose gate (Part I, M8).

---

## 8. Part G — Researcher-gate integrity (M7)

ORCAST has public and researcher capabilities. The restyle must not change who
reaches what.

- Public reach: the public surface may open only public panes (sightings map,
  public forecast clouds). It MUST NOT be able to summon a researcher pane
  (raw hydrophone audio review, detection-labeling, dtag/dive review, model
  internals) — even if asked via the chat.
- Server gate is the authority: a researcher pane request without a valid
  researcher session / agent bearer returns the denial unchanged. Style changes
  never touch the gate.
- The preload restore path and the chat directive path both honor the gate (Part
  E trust-tier rule).

Reference seam: `pax_v0/lib/researchAuth.ts` + the directive allowlist in
`pax_v0/lib/routingOrchestrator.ts` (do-not-touch seams in the pax build).

---

## 9. Part H — Friend → ORCAST console mapping

| pax (Friend) | ORCAST (research) |
|---|---|
| Comfort map viewer (3D WebGL) | Google Maps + probability-cloud canvas |
| Friend chat (`ChatLayer` + `FriendPane`) | Gemma 5-agent research chat + transcript |
| `top_down_sigma` public pane | public sightings / forecast pane |
| Researcher panes (cameras, CV labeling, collection monitor) | hydrophone-audio review, detection-labeling, dtag/dive review, model internals |
| Edge panels: Route / Analytics / Maps | edge panels: Sightings / Hydrophones / Environmental |
| Console views: inspect / comparison / hub_cutaway | console views: sighting / detection / forecast / dive |
| Honesty: modeled / CV-estimate / induction | honesty: H1–H4 above |

Focus claim sites (where ORCAST calls `claim(...)`):
- map click / cloud hover → `claim({kind:"map"})` (or `yield`)
- open chat → `claim({kind:"chat"})`
- summon edge panel → `claim({kind:"panel", edge})`
- open analysis console for a sighting/detection → `claim({kind:"console", view})`

---

## 10. Part I — Qualification rubric (ORCAST M1–M10)

Hard thresholds. No measure passes by assertion; each pass cites the file or
Read-examined frame it was checked against. No-reassurance-bias applies — an
unverified pass is a fail.

| M | Measure | Threshold / method (ORCAST) |
|---|---|---|
| M1 | Text contrast on glass | WCAG AA (4.5:1 normal, 3:1 large/glyph) vs the **worst-case composited map/cloud frame** behind the glass. Zero failures. |
| M2 | Honesty-caption legibility & truth | H1–H4 present, AA-legible, meaning unchanged on every surface. Enumerate current captions, confirm each still renders. |
| M3 | Map/canvas perf no-regression | Median frame time post ≤ 1.10× pre on the same host/viewport over a fixed idle→pan→zoom. Map HUD chips use `blur=0`. Record host quiet-state. |
| M4 | Focus-model determinism | One active target; every transition reversible to map; zero dead-ends. Prove with the ported state-table unit test + walkthrough. |
| M5 | Self-hide never conceals | Drive thinking + error + pending-confirm; surfaces re-reveal / keep error + needed control. Zero concealed. |
| M6 | No covert persistence | One documented key, consent-gated, no telemetry; step log in-memory only. Inspect every storage write. |
| M7 | Researcher-gate integrity | Researcher pane denied without session/bearer; public reach unchanged; preload + chat honor the gate. |
| M8 | Build & prose gates | Type/lint clean, unit suite green, prose gate clean for new copy. Attach logs. |
| M9 | Runtime walkthrough | Cypress/Playwright completes: load → map centered → open/close edge panel → trigger thinking → observe self-hide + re-reveal → save preload → reload → preload applied. No unhandled error. |
| M10 | Visual verification | Every visual claim backed by a **Read-examined** rendered frame, not code inspection. |

Tie-breakers (not gates): demo-camera friendliness (calm motion, no strobe on
self-hide), reuse of ORCAST's existing transparency layer over net-new
mechanisms, fewer convergence-file edits.

---

## 11. Part J — Wave charter scaffold

Run under ORCAST's own orchestrator (O0) with parallel subagent orchestrators per
wave. Gated waves require explicit O0 go.

| Wave | Work | Gate |
|---|---|---|
| W0 | Research: read ORCAST seams (map component, chat/agent UI, transparency layer, auth), record any drift vs this manifest; adversarial member owns honesty-caption legibility, canvas perf, researcher-gate, self-hide-conceals | report to O0 |
| W1 | Candidate design space (token plan, focus-model binding options, persistence options) scored against M1–M10 | — |
| W2 | Select design; architecture note | — |
| W3 | **Design acceptance** on prototype evidence (must clear M1,M2,M4,M5,M6,M7; credible plan for M3,M8,M9,M10) | **GATED** |
| W4 | Implementation: tokens, GlassSurface, focus model + binding, self-hide, edge panels, preload | — |
| W5 | Testing: static gates (M8), focus unit test (M4), walkthrough (M9), perf A/B (M3), Read-verified frames (M10), researcher-gate (M7) | — |
| W6 | Adversarial review; exits at zero open P0/P1 | — |
| W7 | **Final acceptance**: M1–M10 all hold on the running app with Read-examined evidence; gated to O0 for commit/push/promotion | **GATED** |

---

## 12. Part K — Reference-implementation file map

Everything ORCAST needs to replicate, with the pax source to copy/adapt from
(`pax_v0` @ `793b86e`):

Target is orcast `web/` (Next.js 14 / React 18 / TS 5) — paths below are under `web/`.

| Concern | pax reference | ORCAST `web/` target |
|---|---|---|
| Design tokens | `app/globals.css` `:root` (Part A) | `web/app/globals.css` `:root` |
| GlassSurface | `components/ui/GlassSurface.tsx` | `web/app/components/ui/GlassSurface.tsx` (copy as-is) |
| Focus model (pure) | `lib/focus/focusModel.ts` | `web/lib/focus/focusModel.ts` — port verbatim |
| Focus model test | `lib/focus/focusModel.test.ts` | `web/lib/focus/focusModel.test.ts` — the M4 proof |
| Focus binding | `components/focus/FocusProvider.tsx` | `web/app/components/focus/FocusProvider.tsx` |
| Chat self-hide | `components/chat/ChatLayer.tsx`, `FriendPane.tsx` | `web/app/components/ExploreGuidePanel.tsx` (agent chat shell) |
| Dock self-hide | `components/console/ConsoleController.tsx` | `web/app/components/ActiveSurfaceHost.tsx` (surface controller) |
| Edge panels | `components/comfort/CollapsibleBorderPanel.tsx` | sightings/hydrophones/environmental panels under `web/app/components/` |
| Console shell + save preload UI | `components/console/SplitConsole.tsx` | analysis console shell under `web/app/components/console/` |
| Preload persistence | `lib/consolePreload.ts` | `web/lib/consolePreload.ts` |
| Walkthrough (M9) | `e2e/lgc-comfort-walkthrough.spec.ts` | `web/e2e/orcast-research-walkthrough.spec.ts` (Playwright; `web/playwright.config.ts` exists) |
| Rubric | LGC `METHODOLOGY_RUBRIC.md` | Part I above |

Do-not-touch seams (preserve the analog in ORCAST): the researcher auth gate and
the agent-directive allowlist parser. Style never edits these.

---

## 13. Part L — Acceptance, escalation, honesty

- **Acceptance** is the rubric in Part I. W3 and W7 are gated; W7 ships only with
  Read-examined runtime evidence for all of M1–M10.
- **Escalation**: any seam drift (a referenced ORCAST surface missing/renamed),
  any honesty-caption that cannot render at AA over glass, or any researcher-gate
  ambiguity stops the wave and returns to O0 — do not infer or fabricate a
  missing surface.
- **Honesty**: this manifest describes a restyle + a focus/persistence layer. It
  does **not** change ORCAST's data, models, accuracy claims, or who can see
  researcher data. Any caption rewrite that would weaken a disclaimer is a M2
  failure, not a copy edit.

---

### Provenance

Reference implementation: pax LGC waveset, lane
`pax/.cca/catalogue/O0/20260628_liquid-glass-console/`, product code `pax_v0`
@ `793b86e`. Tokens and focus-model logic are quoted verbatim from that build;
the focus model and design tokens are framework-free and port without React.

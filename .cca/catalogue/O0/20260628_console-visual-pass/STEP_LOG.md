# STEP_LOG (newest last)

## 2026-06-28 — S01 hydration + charter authored

- O0 grounded the lane in the live code at `main 97b6397` and re-verified the three defects:
  (1) `web/app/globals.css` has no `.chip` rule and no base `button` / `textarea` / `input` /
  `label` styles (grep for `.chip {` returns zero), so `<button className="chip">` at
  `AdaptiveExplore.tsx:330` and the bare controls render as native unstyled OS controls; the styled
  `.ask-label` / `.ask-textarea` classes exist at `globals.css:308-318` but the home does not use
  them. (2) The home composer is a raw `<label>Ask about the Salish Sea <textarea rows={2}>` at
  `AdaptiveExplore.tsx:335-343`, no width, cramped. (3) The hydrophone beacon is a 6-sided cone
  `coneGeometry args={[1.6, 5, 6]}` in `#ffcf33` at `SalishScene.tsx:354-357`, dominating the frame.
- Confirmed the hot convergence surface: `globals.css` (LGC-W4 tokens + `.glass-surface`; TWIN
  W-LABELS `.scene-label`; WFX-INTEGRATE), `AdaptiveExplore.tsx` (CXR-1 copy redaction, dispatched,
  commit gated to O0), `SalishScene.tsx` (TWIN W2.6 / W-CAM / W-PERFUX-BUILD / W-LABELS,
  WFX-INTEGRATE, ORCA-OINT). CVP carries an explicit collision lock and serializes through O0.
- Locked decisions recorded in the charter: web/ only; baseline-correctness + design-system layer
  (component classes, composer layout, panel hierarchy, Get-access form, mobile breakpoints); NO LGC
  glass/ink token families, ghost-text, self-hide, or preload; style-only (no anonymous-path copy
  change, CXR owns copy); net-new buoy marker under `web/lib/scene/markers/` with the SalishScene
  editor wiring it, no camera/framing/re-bake; no new dependencies; no commit/push/deploy without
  operator request.
- Authored: WAVESET_CHARTER, wave_shape.yml, ORCHESTRATOR_DISPATCH_PROMPT, README, DECISION_RECORD,
  W1_DISPATCH, CVP_PREFLIGHT, and the runnable preflight `tools/waves/gates/cvp-preflight.sh`
  (writes `gate_captures/cvp_preflight.json`). Appended CVP-W1..CVP-W4 + the `cvp-preflight` gate to
  `docs/devpost/waves.registry.yaml`.
- Status: CHARTERED, pending operator GO on the DECISION_RECORD items and the W3 serialize order,
  then W1 launch. W2 build, W3 integrate, and W4 accept are O0-gated.

## 2026-06-28 — S02 operator GO, W1 dispatched

- Operator confirmed DECISION_RECORD items 1-3 ("go"): separate baseline lane, full console pass,
  serialize through O0 with CVP baseline before LGC identity. The exact W3 per-file serialize order
  stays O0-gated and is re-confirmed at the W3 gate.
- Dispatched W1 discovery (read-only) to a background sub-orchestrator running the five disjoint
  agents from `W1_DISPATCH.md` (A1 controls, A2 layout, A3 scene-marker + TWIN boundary, A4
  globals.css additive boundary vs LGC, A5 adversarial + collision + defect re-verify). Each writes
  only its `findings/CVP-<TOPIC>.md`; no edits to `web/`; no dev server; no commit. The
  sub-orchestrator writes `findings/SYNTHESIS_cvp.md` (the W2 build split) and pauses, returning to
  O0. W2/W3/W4 remain O0-gated.

## 2026-06-28 — S03 W1 complete, O0 rulings, W2 dispatched

- W1 returned all six findings docs + `SYNTHESIS_cvp.md`. Three defects re-verified PRESENT (note D3
  beacon is `SalishScene.tsx:355`, a +1 line drift vs the dispatch's `:354`; corrected). No code
  changed. Six escalations returned to O0. Rulings:
- E5 (scope correction), ACCEPTED. The "missing Get-access form" premise was inaccurate: the
  `InterestForm` is already rendered for anonymous users at `AdaptiveExplore.tsx:397` and existed at
  the pin, it is just unstyled. CVP scope narrows from "create" to "style the existing form". W3
  gains a fourth serialized edit file `web/app/components/InterestForm.tsx` (no other lane holds it).
  This is strictly less work, kept in scope.
- D-1 (control naming), RULED per charter: define `.chip` plus base `button` / `textarea` / `input` /
  `label` element selectors in net-new `web/app/styles/cvp-controls.css`. The charter locked-decision
  names exactly these, so the baseline-cascade approach stands. This minimizes the diff to the
  CXR-held `AdaptiveExplore.tsx` (chips already reference `.chip`; the composer fix reuses the
  existing `.ask-label` / `.ask-textarea`), avoiding the 15 className swaps the `.cvp-*` alternative
  would force into a file CXR-1 is actively editing.
- D-2 (spacing tokens), RULED: minting `--cvp-space-*` spacing tokens is allowed. The boundary forbids
  only the LGC `--glass-*` / `--text-ink` families; an additive `--cvp-*` namespace does not collide.
- E1 (stale pin string), NOTED: `repo_state_verified_against: main 97b6397` is the correct grounding
  pin (state before the pass). The `gate_captures/cvp_preflight.json` capture is regenerated against
  the then-current HEAD at the W3 preflight RUN, not churned now.
- E2/E3 (beacon guardrail) folded into the W3 gate: require a Read-examined `SalishScene.tsx` diff
  proving only beacon geometry / scale / material changed, with no camera / datum / water edit.
  PF-3.beacon is expected to flip from PRESENT to absent after the cone swap by design.
- E4 (chip blast radius, 15 sites across 7 components) folded into the W4 gate: capture covers those
  components, not only `/`.
- E6 (concurrency), NO ACTION: an external committer advanced HEAD during the read-only wave; verified
  no `web/` or `src/` touched and CVP ran no git command.
- Dispatched W2 build (net-new files only, no edits to the hot convergence files, no commit) to a
  background sub-orchestrator running B1 controls CSS, B2 layout + Get-access form styling, B3 buoy
  marker module, each owning disjoint net-new files plus a `WIRING-*.md`, validating with
  `cd web && npx tsc --noEmit`. Pauses and returns to O0. W3 integrate and W4 accept remain O0-gated.

## 2026-06-28 — S04 W2 complete, W3 serialize order confirmed, W3 dispatched

- W2 returned three net-new files (`web/app/styles/cvp-controls.css`, `cvp-layout.css`,
  `web/lib/scene/markers/buoyMarker.tsx` + `index.ts`) and three WIRING docs with the exact per-file
  W3 edit list. `cd web && npx tsc --noEmit` clean (exit 0), linter clean, the four hot files
  unmodified, no commit. E7 (concurrency): WFX water-sandbox + ORCA mesh edits landed in parallel,
  none a CVP hot file. No action.
- W3 serialize gate CONFIRMED from git state at HEAD `eeb1ab4`: the four hot files
  (`globals.css`, `AdaptiveExplore.tsx`, `SalishScene.tsx`, `InterestForm.tsx`) are clean (no
  uncommitted edits), and the upstream holders in the W1 serialize order have LANDED on main, namely
  CXR-1 (`7116caf`) ahead of CVP-W3 on `AdaptiveExplore.tsx`, and TWIN-W2.6 (`665c808`) then
  TWIN-W-PERFUX-BUILD (`d3ab16a`) ahead of CVP-W3 on `SalishScene.tsx`. The downstream lanes
  (LGC-W4, TWIN-W-LABELS / W-CAM-REG, WFX-INTEGRATE, ORCA-OINT) have not started and rebase on top of
  CVP. Serialize precondition satisfied; O0 authorizes W3.
- Dispatched W3 integration (single serialized editor on the four hot files, NO commit). Runs the
  preflight first, applies the WIRING edit list, validates `tsc --noEmit`, and returns a
  Read-examined `SalishScene.tsx` diff proving only beacon geometry / scale / material changed (E2/E3
  ruling). Commit stays the operator's explicit call. W4 accept remains O0-gated.

## 2026-06-28 — S06 W3 complete, W4 accept dispatched

- W3 returned the four hot files edited per the REQUIRED list (uncommitted, 4x M), `tsc --noEmit`
  clean, ReadLints 0, and the Read-examined beacon-only diff (cone+stem -> `BuoyMarker`, hover scale
  1.4 -> 1.15, handlers relocated to a wrapping group, `Html` label + camera untouched). Preflight
  overall FAIL is non-blocking: `next lint` no-config env (pre-existing, not a named hard check) plus
  the by-design `PF-3.beacon` flip; the static hard checks (tsc/yaml/secrets) and the LGC boundary
  checks are green.
- Dispatched W4 acceptance: render the live working tree (with the uncommitted W3 edits) and capture
  the anonymous home at desktop 1280x900 and a mobile viewport, save frames to `gate_screenshots/`,
  Read-examine each frame, and return an honest verdict on the controls, composer, Get-access form,
  and buoy beacon, covering the chip blast-radius components (E4). No edits, no commit. Returns to O0.

## 2026-06-28 — S07 operator directive: no local dev, use a dedicated aimez AWS host

- Operator directive: sub-orchestrators must NOT run dev servers / builds / Playwright captures on
  the local machine. All such compute runs on a dedicated aimez AWS host. Recorded as a hard rail in
  DECISION_RECORD.
- W4 was mid-capture on a local `next dev`; INTERRUPTED and halted. The W4 agent confirmed all local
  servers shut down (ports 3099/3210 free), wrote 6 PNGs under `gate_screenshots/` (desktop frames
  CSS-verified/reliable, the two mobile frames suspect, captured before the CSS-applied wait), no
  `findings/CVP-ACCEPT.md`, no STEP_LOG W4 entry, no product-code edit, no commit. W4 is NOT accepted;
  it will be re-run on the host.
- Hosting context grounded from `.sst/hosting_consolidation_v1.json` (DD-10): production is Vercel
  (frontend + edge proxy) + AWS App Runner (backend); the shared `aimez-services` EC2 behind
  `orcast-api.aimez.ai` is retired as primary backend and kept dormant as a one-env-var rollback. The
  CVP W3 edits are uncommitted local working-tree changes to the Next `web/` app, deployed nowhere.
- BLOCKED on operator answers (asked): (1) which host + access, (2) how the uncommitted edits reach
  the host given the no-commit-without-approval rule. W4 re-dispatch waits on these.

## 2026-06-28 — S03 W1 complete (read-only), paused at the exit gate

- Ran the five W1 agents in parallel as read-only subagents against actual HEAD `a914ad1` (the tree
  had advanced past the dispatch pin `97b6397`, as the charter anticipated). All five findings docs
  written under `findings/`: `CVP-CONTROLS.md`, `CVP-LAYOUT.md`, `CVP-MARKER.md`,
  `CVP-GLOBALS-BOUNDARY.md`, `CVP-ADVERSARIAL.md`. Each cites real `file:line`.
- Three defects re-verified PRESENT at the pin: D1 `.chip {` absent in `globals.css` (grep zero) and
  no base `button/textarea/input/label`, `.chip` used at `AdaptiveExplore.tsx:313,330`; D2 raw composer
  at `AdaptiveExplore.tsx:335-343`; D3 cone `coneGeometry args={[1.6,5,6]}` at `SalishScene.tsx:355`
  (a `+1` line drift versus the dispatch sketch `:354`), color `#ffcf33` from `:339`.
- Boundary stated by selector and by string: A4 allow-list (`.chip`/base controls/form fields, all
  `cvp-` candidate selectors) and deny-list (`--glass-*`, `--text-ink`, `.glass-surface`, `.scene-label`,
  ghost-text/self-hide/preload), all absent at HEAD so CVP redefines nothing; style-only confirmed (no
  anonymous-path copy change). Collision map names every lane on each hot file with a per-file serialize
  order, cross-referenced to `docs/devpost/waves.registry.yaml`.
- Wrote `findings/SYNTHESIS_cvp.md`: the W2 build split (B1 `cvp-controls.css`, B2 `cvp-layout.css`,
  B3 `web/lib/scene/markers/buoyMarker.tsx`, each with a `WIRING-*.md`), the wiring seams, and the W3
  serialize order.
- Escalations returned to O0: E1 stale pin in four artifacts + regenerate the preflight capture; E2/E3
  no positive camera/datum/water guardrail in the preflight, require a Read-examined `SalishScene` diff
  at W3; E4 `.chip` blast radius is 15 sites across 7 components (tie to the chip-naming decision); E5
  the Get-access form already exists as the unstyled `InterestForm` (rendered at `AdaptiveExplore.tsx:397`),
  so W2 styles it rather than authoring a new form and W3 gains a fourth edit file
  `web/app/components/InterestForm.tsx` (no other lane holds it); E6 a concurrent external committer
  committed the findings docs (`fde919e`, `eeb1ab4`) interleaved with ORCA biologging commits, advancing
  HEAD `a914ad1` -> `eeb1ab4`, touching no `web/` or `src/` (CVP ran no git). Open W2 decisions for O0:
  D-1 chip/base-control naming and scoping, D-2 whether to mint `--cvp-space-*` tokens.
- No product code changed by this lane. PAUSED at the W1 exit gate. W2/W3/W4 remain O0-gated.

## 2026-06-28 — S04 W2 build complete (net-new files only), paused before W3

- Ran the three W2 build agents in parallel as internal subagents against actual HEAD `eeb1ab4`,
  each owning disjoint NET-NEW files plus a `WIRING-*.md`. All seam line numbers re-verified at this
  HEAD before dispatch (composer `<label>`:335 / `<textarea>`:337 / chips :313,330 / Ask button :345;
  beacon cone :355-356 / white stem :358-361 / handlers+scale on the `<mesh>` :342-353 / outer
  `<group>` :341 / `Html` label :362-366; InterestForm inputs :98,99 / CTA :101 / `a.chip` :52,57,62 /
  radios :85 / `.row` option :84). Net-new files created, none pre-existing:
  - B1 controls paint: `web/app/styles/cvp-controls.css` + `WIRING-controls.md`. Styles `.chip`
    (default/:hover/:focus-visible/:disabled + `[data-active="true"]`/`[aria-pressed="true"]` selected
    + `a.chip` anchor variant), primary base `button`, and text fields scoped to
    `textarea, input[type="text"|"email"|"search"]` (radios deliberately excluded so they stay native),
    plus a minimal bare `label` (color only, no flex, so it cannot fight `.ask-label` or the radio
    `.row` labels). Per the D-1 ruling: `.chip` + bare element selectors, NOT a `.cvp-*` namespace.
    Reuses only existing `:root` tokens; no `--glass-*`/`--text-ink`, no `.ask-*` redefine, no copy.
  - B2 layout + form: `web/app/styles/cvp-layout.css` + `WIRING-layout.md`. Mints additive
    `--cvp-space-xs..xl` tokens (D-2 allowed); `.explore-console > .card { margin-bottom: 0 }` so the
    existing 1rem console flex gap is the only inter-panel rhythm; optional `.cvp-stack`/`.cvp-stack--sm`
    helpers; layout for the EXISTING InterestForm markup classes (`.interest-card`, `.interest-options`,
    `.interest-links`) plus one new `.interest-option` row class; 768px override scoped under
    `.explore-console` (980px already collapses the grid). The composer fix reuses the EXISTING
    `.ask-label`/`.ask-textarea` (no new composer class), per D-1. No LGC token, no `.ask-*` redefine,
    no copy.
  - B3 buoy marker: `web/lib/scene/markers/buoyMarker.tsx` + `index.ts` barrel + `WIRING-marker.md`.
    Pure r3f `BuoyMarker({ color, hovered })` returning a `<group>` of three `meshStandardMaterial`
    primitives — body cylinder r0.5 x h0.8 @ y0.4, thin mast cylinder r0.06 x h1.0 @ y1.3, topmark
    sphere r0.22 @ y1.95, total height ~2.17 units (within the 1.8-2.5 target, footprint under a third
    of the old cone radius 1.6). Low body emissive (0.18 rest / 0.4 hover), brighter topmark light
    (0.65 / 1.0); hover raises emissive, never geometry. Color contract `#ffcf33`/`#888` preserved via
    the `color` prop. No new dependency, no `position`/handlers/`Html` label, no camera/datum/water.
- Validation: `cd web && npx tsc --noEmit` -> exit 0 (CLEAN), re-run and confirmed by the
  sub-orchestrator (not only the agents). The `.tsx` is type-checked program-wide despite no importer,
  so this is a real signal. Linter clean on all four new code files. CSS is not type-checked and a true
  buoy render needs a browser/dev server, which W2 forbids; the buoy visual read is deferred to the W4
  accept capture (Playwright). Boundary re-verified by grep: net-new CSS contains no `--glass-*`,
  `--text-ink`, `.ask-*` redefine, `.scene-label`, or `.fx-`.
- No existing product file changed by CVP: `git status` shows the four CVP hot files
  (`web/app/globals.css`, `web/app/components/AdaptiveExplore.tsx`, `web/app/components/scene/SalishScene.tsx`,
  `web/app/components/InterestForm.tsx`) UNMODIFIED. No commit, push, or deploy.
- E7 (concurrency, sub-orchestrator) — flagged to O0. During the W2 window other lanes edited the
  working tree in parallel (mtimes 22:46-22:50): WFX modified `web/app/(sandbox)/water/WaterSandboxScene.tsx`
  (a "WATER-FX verification rig" with a Preetham sky dome and exposure levers, content-confirmed not
  CVP) and ORCA touched `web/public/orca/orca.glb`, `.gitignore`, and added `web/lib/scene/orca/loadOrcaMesh.ts`
  + `web/public/orca/motion/`. None of these is a CVP file and none is a CVP hot convergence file; the
  CVP build agents touched only their six net-new artifacts. Same pattern as E6: the W3 preflight must
  run against the then-current HEAD and account for uncommitted concurrent work in the tree.
- PAUSED at the W2 exit gate, returning to O0. W3 integrate and W4 accept remain O0-gated; not started.

## 2026-06-28 — S05 W3 integration complete (single serialized editor), paused before W4

- Ran W3 as the SOLE editor of the four hot files at HEAD `eeb1ab4` (O0-confirmed serialize: CXR-1 and
  TWIN-W2.6 / W-PERFUX-BUILD landed upstream; all four hot files clean pre-edit). No commit, push, or
  deploy. W4 not started (O0-gated).
- STEP 1 pre-edit preflight (`bash tools/waves/gates/cvp-preflight.sh`): PF-3 all three defects PRESENT
  (D1 no `.chip` rule, D2 raw composer, D3 cone `coneGeometry args={[1.6, 5, 6]}`); the named static hard
  checks green (PF-1.tsc PASS, PF-1.yaml x2 PASS, PF-2.secrets PASS). Overall verdict FAIL came solely
  from PF-1.lint, which is a pre-existing environment condition: `next lint` has no ESLint config and
  prompts interactively, so the harness's non-interactive run exits non-zero. Lint is not one of the
  dispatch's named hard checks and not in the preflight doc's hard-FAIL list (tsc / invalid YAML / leaked
  secret / missing defect / boundary violation). Unrelated to the known defects and to the (untouched)
  hot files, so proceeded per the dispatch.
- STEP 2 applied the REQUIRED edit list only (OPTIONAL cleanups skipped to keep the diff minimal and
  collision-safe). All cited markup matched with no drift:
  - `web/app/globals.css`: added `@import "./styles/cvp-controls.css";` then
    `@import "./styles/cvp-layout.css";` as the first two lines, above `:root`.
  - `web/app/components/AdaptiveExplore.tsx`: `<label>` -> `<label className="ask-label">` (`:335`);
    added `className="ask-textarea"` to the `<textarea>` (`:337`). No copy change (CXR owns copy).
  - `web/app/components/InterestForm.tsx`: audience option `<label>` `className="row"` ->
    `className="interest-option"` (`:84`); inline `style` left in place (OPTIONAL removal skipped).
  - `web/app/components/scene/SalishScene.tsx`: added `import { BuoyMarker } from "@/lib/scene/markers";`
    after the `@/lib/scene/water2` import; replaced the cone geometry+material and the white stem mesh
    with `<BuoyMarker color={color} hovered={hovered} />`; relocated `onClick`/`onPointerOver`/
    `onPointerOut` and `scale` off the cone `<mesh>` onto a wrapping `<group>` inside the outer
    `<group position={position}>`, hover scale `1.4` -> `1.15`. The `Html` hover label left UNTOUCHED.
- STEP 3 validate: `cd web && npx tsc --noEmit` clean, exit 0. ReadLints on the four touched files: 0
  diagnostics.
- STEP 4 beacon diff proof (E2/E3): read `git diff web/app/components/scene/SalishScene.tsx` and confirmed
  ONLY beacon geometry/scale/material + the local interaction wrapper changed (cone+stem meshes -> wrapping
  `<group>` + `<BuoyMarker>`, scale 1.4 -> 1.15, plus the marker import). NO camera, datum, water, tile-load,
  or re-bake edit; outer placement group and `Html` label unchanged.
- Post-edit preflight written to `gate_captures/cvp_preflight.json` (pass=9 fail=2 skip=5). Deltas vs
  pre-edit: PF-3.beacon PASS -> FAIL ("D3 gone", the designed E2/E3 flip as the cone is resolved);
  PF-4.worktree PASS -> SKIP (the four hot files now dirty under the O0-confirmed serialize); PF-5.tokens
  and PF-5.lgc now actively evaluated (CVP_CHANGED=1) and both PASS (no LGC boundary violation). PF-1.tsc /
  PF-2.secrets / PF-1.yaml remain green. PF-3.chip and PF-3.composer still read "present" only because the
  harness greps for the literal `.chip {` rule in `globals.css` and the composer copy string in place; D1 is
  resolved via the imported `cvp-controls.css` partial and D2 via the `ask-label`/`ask-textarea` classNames
  (no copy change), neither observable by a literal in-place grep. The overall FAIL is by design (beacon
  flip + the pre-existing lint env), not a boundary violation.
- No commit, push, or deploy. The four hot file edits are left uncommitted in the working tree. PAUSED at
  the W3 exit gate, returning to O0. W4 accept remains O0-gated; not started.

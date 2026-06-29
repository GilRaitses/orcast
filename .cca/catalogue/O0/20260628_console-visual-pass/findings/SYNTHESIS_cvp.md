# SYNTHESIS_cvp — W1 discovery synthesis + W2 build split (sub-orchestrator)

Lane: console-visual-pass (CVP). Author: CVP sub-orchestrator (W1 wrap-up). Read-only
wave; the only files written are the six findings docs under this `findings/` directory.
Pin reconciliation: dispatch pin was `main 97b6397`; W1 ran against actual HEAD
`a914ad1` and HEAD has since advanced again to `eeb1ab4` by a concurrent external
committer (see escalation E6). All three defects re-verified PRESENT at `a914ad1`, and
the intervening commits touched zero of the three hot files.

## 1. W1 inputs (the five findings docs)

| Doc | Owner | Core result |
| --- | --- | --- |
| `findings/CVP-CONTROLS.md` | A1 | Control inventory (9 sites). `.chip` and base `button/textarea/input/label` absent in globals.css. `.ask-*` present but unused on home. Proposed `cvp-`prefixed class set, default/hover/focus/disabled, reusing only `:root` tokens. |
| `findings/CVP-LAYOUT.md` | A2 | Composer cramping at `AdaptiveExplore.tsx:335-343`. Get-access form ALREADY EXISTS (`InterestForm`, rendered at `:397`) but is unstyled. Proposed full-width composer, named spacing scale, reuse of 980px/768px breakpoints. |
| `findings/CVP-MARKER.md` | A3 | Cone beacon `HydrophoneBeacon` at `SalishScene.tsx:328-369`; `coneGeometry args={[1.6,5,6]}` at `:355`. `web/lib/scene/markers/` confirmed net-new. Buoy contract + exact wiring seam + TWIN boundary. |
| `findings/CVP-GLOBALS-BOUNDARY.md` | A4 | `:root` token map (`globals.css:1-13`). `--glass-*`, `--text-ink`, `.glass-surface`, `.scene-label` all ABSENT at HEAD. Allow-list / deny-list by selector. Ghost-text `.chat-ghost*` present and assigned to LGC. |
| `findings/CVP-ADVERSARIAL.md` | A5 | Three defects re-verified PRESENT with literal greps. Per-file collision map cross-referenced to the registry. Serialize order. Boundary-violation hunt. Escalations E1-E3 + chip blast-radius awareness. |

W1 exit gate status: all five findings docs exist and cite real `file:line`; the three
defects are re-verified present at the pin; the additive boundary vs LGC and the
style-only boundary vs CXR are stated by selector and by string (A4 + A1); the collision
map names every lane holding each hot file and proposes a serialize order (A5). No code
changed by this lane.

## 2. Defect re-verification (carried from A5, confirmed by the sub-orchestrator)

| Defect | Grep / cite | Verdict at HEAD a914ad1 |
| --- | --- | --- |
| D1 controls | `rg -n "\.chip\s*\{" web/app/globals.css` -> zero hits; `rg -n "^\s*(button\|textarea\|input\|label)\s*\{" web/app/globals.css` -> zero hits; `.chip` used at `AdaptiveExplore.tsx:313,330` | PRESENT |
| D2 composer | bare `<label>Ask about the Salish Sea <textarea rows={2}>` at `AdaptiveExplore.tsx:335-343`, no `.ask-textarea` | PRESENT |
| D3 beacon | `<coneGeometry args={[1.6, 5, 6]} />` at `SalishScene.tsx:355`; color `#ffcf33` from `const color = online ? "#ffcf33" : "#888"` at `:339` | PRESENT |

Note the +1 line drift versus the dispatch sketch: the cone is at `SalishScene.tsx:355`,
not `:354` (A3 and A5 agree). The composer span `335-343` and `.ask-*` block `308-318`
match the dispatch.

## 3. W2 build split (which agent owns which net-new file)

W2 is parallel, net-new files only, plus one `WIRING-*.md` per agent that tells the W3
single editor the exact integration edit. No convergence file is touched in W2.

### B1 — baseline controls + forms CSS
- Owns (net-new): `web/app/styles/cvp-controls.css` + `WIRING-controls.md`.
- Content (from A1 + A4 allow-list): control paint only. The chip rule, base control
  appearance, text-field paint, focus and disabled states, and the Get-access field
  paint. Per A1 the candidate selectors are `.cvp-button` (+ optional `.cvp-button--ghost`),
  `.cvp-chip`, `.cvp-input`, `.cvp-textarea`, `.cvp-field-label`, each with
  default/hover/focus/disabled. Reuse only `:root` tokens (`--surface`, `--surface-2`,
  `--border`, `--text`, `--text-muted`, `--accent`, `--radius`).
- Boundary: additive only. No `--glass-*` / `--text-ink`, no ghost-text/self-hide/preload,
  no `.ask-*` redefinition, no copy.
- Open decision for O0: see D-1 (chip naming) in section 6.

### B2 — layout + hierarchy + Get-access form
- Owns (net-new): `web/app/styles/cvp-layout.css` + `WIRING-layout.md`.
- Content (from A2): composer container width and label-above-textarea stacking
  (`.cvp-composer` wrapper, or apply the existing `.ask-label`/`.ask-textarea`); panel
  rhythm via a single additive rule `.explore-console > .card { margin-bottom: 0 }` so the
  existing `1rem` console flex gap is the only inter-panel spacing; a named intra-card
  spacing scale (`.cvp-stack` family) to replace inline `style` rhythm; mobile reuse of
  the established 980px and 768px breakpoints with no third breakpoint; the Get-access
  form LAYOUT applied to the existing `InterestForm` via the classNames already in its
  markup (`.interest-card`, `.interest-options`, `.interest-links`) plus single-column
  field arrangement.
- Boundary: layout/structure only. Field PAINT belongs to B1; B2 supplies arrangement.
  No copy (placeholder comments only; CXR owns strings). No LGC token.

### B3 — buoy marker module
- Owns (net-new): `web/lib/scene/markers/buoyMarker.tsx` (plus an optional
  `web/lib/scene/markers/index.ts` barrel) + `WIRING-marker.md`.
- Content (from A3): a pure react-three-fiber module exporting `BuoyMarker({ color, hovered })`
  returning a `<group>` of core `three` primitives (short buoy body, thin mast, small
  topmark light), target total height ~1.8-2.5 units and body radius ~0.5 (footprint under
  a third of the current cone, height under half), `meshStandardMaterial` only, online/
  offline color contract `#ffcf33`/`#888` preserved through the `color` prop. No new deps,
  no scene/camera/datum reference, no `Html` label (TWIN owns labels).
- W2 gate per charter: the module type-checks in isolation and the author Reads a sandbox
  or unit render before claiming it renders as a buoy.

### Disjointness of the W2 split (no two agents own the same file)
- `cvp-controls.css` (B1) and `cvp-layout.css` (B2) are separate net-new files. The split
  by concern is: B1 = control/field PAINT, B2 = composer/panel/form LAYOUT. The two seams
  for the composer field are complementary, not overlapping: B1 paints the `<textarea>`
  and label; B2 sizes/stacks the composer wrapper.
- `buoyMarker.tsx` (B3) is a separate subtree under `web/lib/scene/markers/`.

## 4. Wiring seams (what the W3 single editor applies)

These are recorded now for O0 planning; W3 is O0-gated and not started.

1. globals.css (additive include). Add the two partials at the top of
   `web/app/globals.css`, for example `@import "./styles/cvp-controls.css";` and
   `@import "./styles/cvp-layout.css";`, or import them from `web/app/layout.tsx`. This is
   purely additive and redefines none of the deny-list selectors (A4). Plus the single
   additive rule `.explore-console > .card { margin-bottom: 0 }` if B2 places it here.
2. `AdaptiveExplore.tsx` composer (`:335-343`). Apply the field classes to the bare label
   and textarea (B1 `.cvp-field-label` / `.cvp-textarea`, or the existing `.ask-label` /
   `.ask-textarea`) and the composer wrapper class (B2 `.cvp-composer`). If the chip-naming
   decision (D-1) lands on namespaced classes, also swap `className="chip"` ->
   `className="cvp-chip"` at `:313,330`. All of this is style-only className application; it
   changes no copy string. This file is held by CXR-1 (dispatched) -> serialize CXR-1 first.
3. `InterestForm.tsx` (the Get-access form). Apply `.cvp-input` to the inputs (`:98,99`),
   `.cvp-button` to the CTA (`:101-103`), `.cvp-chip` to the result anchors (`:52,57,62` if
   namespaced), and the B2 `.interest-*` layout classes. See escalation E5: this is a
   FOURTH product file beyond the three named hot convergence files, and the registry shows
   no other lane holding it, so the edit is collision-free but it expands the W3 edit set.
4. `SalishScene.tsx` beacon (`:341-366`). Replace `:355-356` (cone geometry + material) and
   `:358-361` (white stem) with `<BuoyMarker color={color} hovered={hovered} />`; relocate
   `onClick` / `onPointerOver` / `onPointerOut` and `scale` from the `<mesh>` at `:342-353`
   onto the outer `<group>` at `:341` so the multi-mesh buoy stays clickable; add the import
   of `buoyMarker`. Preserve position/color/hover/onSelect. Leave the `Html` hover label at
   `:362-366` untouched (TWIN owns labels). This file is held by TWIN and others -> serialize.

## 5. Recommended W3 serialize order (per hot file, cross-referenced to `docs/devpost/waves.registry.yaml`)

Locked policy: CVP baseline before LGC identity, serialized through O0, `git pull --rebase`
first, preflight green on hard checks. In-flight (dispatched) lanes are the real
serialization risk; chartered/gated lanes are not yet editing.

| Hot file | Holding lanes (registry line) | Status | Recommended order |
| --- | --- | --- | --- |
| `web/app/globals.css` | LGC-W4 (1247-1250), TWIN-W-LABELS (1460-1464), WFX-INTEGRATE (1488-1491) | all chartered/gated, none in-flight | CVP-W3 -> LGC-W4 -> TWIN-W-LABELS -> WFX-INTEGRATE |
| `web/app/components/AdaptiveExplore.tsx` | CXR-1 (1313-1319) | dispatched (in-flight) | CXR-1 -> CVP-W3 (CVP rebases after the copy redaction lands) |
| `web/app/components/InterestForm.tsx` | none in registry | clean | CVP-W3 free (new to the edit set; see E5) |
| `web/app/components/scene/SalishScene.tsx` | TWIN-W2.6 (1276-1283), TWIN-W-PERFUX-BUILD (1303-1305), TWIN-W-CAM-REG (1449-1451), TWIN-W-LABELS (1460-1464), WFX-INTEGRATE (1488-1491), ORCA-OINT (1593-1595) | W2.6 + PERFUX-BUILD dispatched (in-flight); rest chartered/gated | TWIN-W2.6 -> TWIN-W-PERFUX-BUILD -> CVP-W3 (beacon) -> TWIN-W-CAM-REG -> TWIN-W-LABELS -> WFX-INTEGRATE -> ORCA-OINT |

The two dispatched TWIN waves on `SalishScene.tsx` and the dispatched CXR-1 on
`AdaptiveExplore.tsx` are the binding constraints. CVP-W3 must rebase after each lands and
re-run the preflight against the then-current HEAD.

## 6. Open W2 decisions for O0 (do not pre-decide; flagged per the escalation catch)

- D-1 chip and base-control naming. The charter and `wave_shape.yml` name CVP's additions
  as `.chip` plus base `button/textarea/input/label`. A1 instead proposes `cvp-`namespaced
  classes (`.cvp-chip` and so on) to avoid a global `textarea`/`input` base rule cascading
  onto `/ask` (the `.ask-*` surface) and other pages. The trade-off: styling the existing
  `.chip` and bare elements directly means near-zero component edits in W3 but a wider
  global cascade (A5 notes `.chip` is used at 15 sites across 7 components); namespacing is
  cascade-safe but requires className swaps at those 15 sites, several inside the
  CXR-held `AdaptiveExplore.tsx`. A middle option is to style `.chip` directly but scope the
  base control rules under the console container rather than bare element selectors. O0
  decides the naming and scoping before W2.
- D-2 spacing tokens. A2 asks whether W2 may mint `--cvp-space-*` custom properties for the
  named spacing scale or must use literals. A4's boundary allows new namespaced selectors
  and properties as long as they are not the LGC families, but to keep PF-5 unambiguous the
  recommendation is either literals or a clearly `--cvp-`prefixed set. O0 confirms.

## 7. Escalations returned to O0

- E1 (A5) stale pin string. `97b6397` is stale in four artifacts: the registry (line 1602),
  `W1_DISPATCH.md` (line 12), `gate_captures/cvp_preflight.json` (the `head` field), and
  `tools/waves/gates/cvp-preflight.sh` (line 21). Reconcile the pin and regenerate the
  preflight capture against the current HEAD before W3.
- E2 (A5) no positive scene guardrail. PF-3.beacon flips to FAIL by design once the cone is
  swapped, and nothing asserts the camera, `useTilesLayer`, `errorTarget`, `maxDepth`, or
  water plane are unchanged. Recommend a Read-examined `SalishScene.tsx` diff at W3 that
  proves only geometry/scale/material changed.
- E3 (A5) no water-surface guardrail. Fold the seabed/water-plane check into the same W3
  diff review.
- E4 (A5 + sub-orchestrator) chip blast radius. A baseline `.chip` (rather than a namespaced
  class) restyles 15 sites across 7 components, so the W4 accept capture should cover chip
  surfaces beyond `/`, not just the home. Tied to decision D-1.
- E5 (A2 + sub-orchestrator) Get-access form premise and a fourth edit file. The charter and
  dispatch describe a MISSING Get-access form; in reality `InterestForm` is rendered
  unconditionally for anonymous users at `AdaptiveExplore.tsx:397` and existed at the pin.
  The real defect is that it is UNSTYLED. W2 scope is corrected to STYLE the existing form,
  not author a new one. Consequence: W3 edits `web/app/components/InterestForm.tsx`, a fourth
  product file beyond the three named hot convergence files. The registry shows no other lane
  holding it, so the edit is collision-free, but the edit set and the W3/W4 surface grow by
  one file. O0 should confirm the scope correction and that `InterestForm.tsx` joins the W3
  edit set.
- E6 (sub-orchestrator) concurrency during the read-only wave. While W1 ran, an external
  committer (author `Gil Raitses`) committed the CVP findings docs in `fde919e` and
  `eeb1ab4`, interleaved with ORCA biologging commits, advancing HEAD `a914ad1` -> `eeb1ab4`.
  Verified those commits touched no `web/` or `src/` file, so the CVP read-only-on-product-
  code rail held and CVP itself ran no git command. Flagged so O0 knows the lane home is now
  committed and the working pin has moved again; the W3 preflight should target the
  then-current HEAD.

## 8. Recommended next step

W1 is complete and at its exit gate. W2 build, W3 integrate, and W4 accept remain O0-gated.
Recommend O0 resolve D-1 and D-2 and acknowledge E1-E6, then dispatch W2 (B1/B2/B3 net-new
files plus WIRING docs). No code changed in W1.

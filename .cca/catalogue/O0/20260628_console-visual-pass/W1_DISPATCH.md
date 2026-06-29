# W1 dispatch: console visual pass discovery (read-only)

Status: pending operator GO. Discipline: one file one owner; READ-ONLY (each agent writes ONLY its
own `findings/CVP-<TOPIC>.md`); no edits to `web/`; no dev server; no `next dev` / `next build`; no
commit / deploy / promotion. Return a findings-doc path + the cited evidence only.

Shared context (every agent reads first):
- Charter: `WAVESET_CHARTER.md` (authority + locked decisions). Machine shape: `wave_shape.yml`.
  Preflight the integrate wave runs: `CVP_PREFLIGHT.md`.
- Console is `/` -> `web/app/components/AdaptiveExplore.tsx` -> `SceneHost` ->
  `web/app/components/scene/SalishScene.tsx` (react-three-fiber + three + 3d-tiles-renderer).
- The three defects at the pin `main 97b6397`:
  1. `web/app/globals.css` has NO `.chip` rule and NO base `button` / `textarea` / `input` / `label`
     styles. The styled `.ask-label` / `.ask-textarea` classes exist at `globals.css:308-318` but the
     home does not use them. Chip is used at `AdaptiveExplore.tsx:330`.
  2. Raw composer `<label>Ask about the Salish Sea <textarea rows={2}>` at
     `AdaptiveExplore.tsx:335-343`, no width, cramped.
  3. Cone beacon `coneGeometry args={[1.6, 5, 6]}` in `#ffcf33` at `SalishScene.tsx:354-357`.
- Hot convergence files shared with other lanes (serialize through O0): `globals.css` (LGC-W4 tokens
  + `.glass-surface`; TWIN W-LABELS `.scene-label`; WFX-INTEGRATE), `AdaptiveExplore.tsx` (CXR-1 copy
  redaction), `SalishScene.tsx` (TWIN W2.6 / W-CAM / W-PERFUX-BUILD / W-LABELS, WFX-INTEGRATE,
  ORCA-OINT). Holds are listed in `docs/devpost/waves.registry.yaml`.
- Locked boundaries: CVP is the baseline layer (adds component classes, layout, Get-access form,
  mobile breakpoints), NOT LGC identity (no `--glass-*` / `--text-ink` tokens, no ghost-text,
  self-hide, or preload), and is style-only (no anonymous-path copy change; CXR owns copy). The
  beacon fix is a net-new module under `web/lib/scene/markers/`; no camera / framing / re-bake.

## Agent A1 — Controls audit (owns findings/CVP-CONTROLS.md)
YOUR TASK: Inventory every native unstyled control surfaced on the anonymous home console. For each,
record the exact component site (file + line), the class or bare tag, and what it renders as today.
Confirm by grep that `.chip` and base `button` / `textarea` / `input` / `label` rules are absent from
`web/app/globals.css`, and that the existing `.ask-label` / `.ask-textarea` (`globals.css:308-318`)
are present but unused on the home. Define the baseline component-class set CVP must add (names,
states: default / hover / focus / disabled) WITHOUT renaming or colliding with the existing `.ask-*`
classes and WITHOUT introducing LGC token families.
DELIVERABLE: `findings/CVP-CONTROLS.md` (control inventory table + the proposed baseline class set +
the no-collision argument vs `.ask-*`).
VALIDATION: every site cited with file:line; the absence greps shown.
COLLISION-AVOIDANCE: own ONLY your findings doc. Read-only; no edits to `web/`. Do not propose LGC
token-family additions.
RETURN: findings path + the control inventory + the proposed class set.

## Agent A2 — Layout / hierarchy audit (owns findings/CVP-LAYOUT.md)
YOUR TASK: Audit the composer cramping (`AdaptiveExplore.tsx:335-343`), the panel hierarchy and
spacing rhythm on the home, and the missing Get-access form. Define the layout the build wave
produces: composer width and stacking, label placement, panel spacing scale, the Get-access form
markup and field layout, and mobile breakpoints. Style only; no copy changes.
DELIVERABLE: `findings/CVP-LAYOUT.md` (current-state cites + the proposed layout + breakpoints + the
Get-access form spec).
VALIDATION: every current-state claim cited with file:line; the proposed layout references only CVP
baseline classes (no LGC tokens) and changes no copy strings.
COLLISION-AVOIDANCE: own ONLY your findings doc. Read-only. Do not change copy (CXR owns it).
RETURN: findings path + the proposed layout + the Get-access form spec.

## Agent A3 — Scene-marker audit + TWIN boundary (owns findings/CVP-MARKER.md)
YOUR TASK: Audit the hydrophone beacon at `SalishScene.tsx:354-357` (geometry `coneGeometry
args={[1.6, 5, 6]}`, `#ffcf33` material, scale, hover) and the surrounding marker group. Define the
buoy target read (geometry / scale / material that reads as a buoy, not a frame-dominating cone) and
the exact wiring seam the SalishScene single editor will use to mount a net-new buoy marker module
from `web/lib/scene/markers/`. State the hard TWIN boundary explicitly: CVP changes only the beacon
geometry / scale / material; NO camera, framing, or re-bake change (those stay 3D-TWIN W2.6 / W-CAM /
W-PERFUX-BUILD / W-LABELS).
DELIVERABLE: `findings/CVP-MARKER.md` (current beacon cite + the buoy contract + the SalishScene
wiring seam + the TWIN boundary statement).
VALIDATION: the beacon site cited with file:line; the wiring seam references the real mount point;
the TWIN boundary names the lanes it must not touch.
COLLISION-AVOIDANCE: own ONLY your findings doc. Read-only; do not edit `SalishScene.tsx`.
RETURN: findings path + the buoy contract + the wiring seam.

## Agent A4 — globals.css additive boundary vs LGC (owns findings/CVP-GLOBALS-BOUNDARY.md)
YOUR TASK: Map the existing `globals.css` token families and the `.glass-surface` / `.scene-label`
ownership. Define exactly which additions are CVP baseline (component classes, composer layout, form
styles, breakpoints) versus which are LGC identity (`--glass-*` / `--text-ink` token families,
ghost-text, self-hide, preload). Prove the additive boundary by selector: CVP adds new selectors that
do not redefine or rename LGC's families and do not touch the TWIN `.scene-label` or WFX surfaces.
DELIVERABLE: `findings/CVP-GLOBALS-BOUNDARY.md` (token-family map + the CVP-baseline-vs-LGC-identity
split, by selector + the additive-boundary proof).
VALIDATION: every owned selector cited; the boundary stated as a selector allow-list / deny-list.
COLLISION-AVOIDANCE: own ONLY your findings doc. Read-only.
RETURN: findings path + the selector-level additive boundary.

## Agent A5 — Adversarial + collision + defect re-verify (owns findings/CVP-ADVERSARIAL.md)
YOUR TASK: Re-verify the three defects STILL exist at the pin by grep (`.chip {` undefined in
`globals.css`; raw composer at `AdaptiveExplore.tsx:335-343`; cone beacon `coneGeometry` at
`SalishScene.tsx:354-357`), so the lane never builds against stale state. Map the FULL collision
surface: for each of the three hot files, name every lane holding it (LGC / CXR / 3D-TWIN / WFX /
ORCA), the specific waves, and the serialize order CVP must request from O0. Hunt boundary violations
and bad assumptions: any place a baseline addition would accidentally introduce an LGC token family,
change copy, or alter camera / framing.
DELIVERABLE: `findings/CVP-ADVERSARIAL.md` (the three defect re-verification greps + the per-file
collision map + the boundary-violation hunt + the recommended serialize order).
VALIDATION: each defect grep shown with its result; the collision map cross-referenced to
`docs/devpost/waves.registry.yaml`.
COLLISION-AVOIDANCE: own ONLY your findings doc. Read-only.
RETURN: findings path + the defect re-verification + the collision map + the serialize order.

## W1 exit gate

All five findings docs exist and cite real paths. The three defects are re-verified present at the
pin. The additive boundary vs LGC and the style-only boundary vs CXR are stated by selector and by
string. The collision map names every lane holding each hot file and proposes a serialize order. No
code changed. The sub-orchestrator then writes `findings/SYNTHESIS_cvp.md` (the W2 build split) and
returns to O0. W2 build, W3 integrate, and W4 accept are O0-gated.

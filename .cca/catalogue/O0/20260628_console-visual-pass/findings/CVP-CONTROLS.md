# CVP-CONTROLS — Controls audit (W1 Agent A1, read-only)

Lane: console-visual-pass (CVP). Agent: A1 Controls audit. Scope: anonymous home
console only. This is a read-only discovery doc. No product code was edited.

## Pin reconciliation

- Dispatch pin: `main 97b6397`.
- Actual HEAD at audit time: `a914ad1bdb482cc5a13ba514eba808ba7082b3a6` (`git rev-parse HEAD`).
- The tree advanced past the pin. The charter anticipated this. All three CVP
  defects (unstyled chips, unstyled native button/textarea/label on the home
  card, and the orphaned `.ask-*` rules) are still present at `a914ad1`. Every
  cite below is a real `file:line` read at the current tree.

## Anonymous home render path

`/` renders `web/app/components/AdaptiveExplore.tsx`
(`AdaptiveExplore` -> `AdaptiveExploreInner`). The home composer card lives in
`AdaptiveExplore.tsx:303-355`. Child components on the anonymous home path:

- `SceneHost` (`web/app/components/scene/SceneHost.tsx`), rendered at
  `AdaptiveExplore.tsx:294`. Surfaces no native form controls. It mounts the r3f
  `SalishScene` canvas or the `MapHero` fallback. Click targets are canvas/3D, not
  native `<button>/<input>` elements. Out of CVP control scope.
- `ActiveSurfaceHost`, rendered at `AdaptiveExplore.tsx:357-365`, only after a
  turn produces a `plan`. Not present on first anonymous paint, so not part of the
  initial control surface.
- `InterestForm` (`web/app/components/InterestForm.tsx`), rendered unconditionally
  at `AdaptiveExplore.tsx:397`. Present on first anonymous paint and surfaces
  native controls (radios, text/email inputs, send button, and `.chip` anchors in
  the post-submit result state).
- `AuthStatus` and `ExploreGuidePanel` were named in the charter as candidates.
  Neither is imported or rendered by `AdaptiveExplore.tsx` (no import, no JSX use
  on the home render path), so neither contributes controls to the anonymous home
  console here.

## Control inventory

Site cites are at HEAD `a914ad1`. "Renders as today" reflects that globals.css has
no `.chip` rule and no base `button`/`textarea`/`input`/`label` rule (see greps
below), so every control listed falls back to the browser native OS appearance,
except where an inline `style` prop adds local paint.

| Site (file:line) | Class / tag | Renders as today | CVP target |
| --- | --- | --- | --- |
| `AdaptiveExplore.tsx:310-324` | `<button className="chip">` (branch options) | Native OS button. `.chip` has zero CSS. Active state only via inline `style` borderColor/color at :316-320 plus `data-active`/`aria-pressed`. | `.cvp-chip` with default/hover/focus/disabled and a `[data-active]`/`[aria-pressed="true"]` selected state |
| `AdaptiveExplore.tsx:330` | `<button className="chip">` (starter prompts) | Native OS button, no styling. | `.cvp-chip` (same class, no selected state needed here) |
| `AdaptiveExplore.tsx:335-343` | bare `<label>` wrapping bare `<textarea>` (`textarea` at :337) | Native label text plus native OS textarea. No padding, border token, or focus ring beyond browser default. | `.cvp-field-label` on the label, `.cvp-textarea` on the textarea |
| `AdaptiveExplore.tsx:345-352` | bare `<button>` (Ask / Thinking…) | Native OS button. Disabled via `disabled` attr only, no styled disabled state. | `.cvp-button` (primary) with default/hover/focus/disabled |
| `InterestForm.tsx:84-95` | bare `<label>` wrapping `<input type="radio">` (input at :85) | Native label plus native radio. | `.cvp-field-label` on label is optional here; radio left native or `.cvp-radio-row` for layout only |
| `InterestForm.tsx:98` | bare `<input type="text">` | Native OS text input. | `.cvp-input` |
| `InterestForm.tsx:99` | bare `<input type="email">` | Native OS email input. | `.cvp-input` |
| `InterestForm.tsx:101-103` | bare `<button>` (CTA) | Native OS button, disabled via attr only. | `.cvp-button` |
| `InterestForm.tsx:52,57,62` | `<a className="chip">` (result links) | Native anchor, `.chip` has zero CSS. Post-submit only. | `.cvp-chip` (anchor variant; same visual, `display:inline-flex`) |

Note: `AdaptiveExplore.tsx:354` and `InterestForm.tsx:105` use `<p className="error">`;
`.error` is a defined rule and is out of CVP control-styling scope.

## Absence / presence greps (literal)

`.chip {` rule is absent from globals.css. Zero matches.

```
$ rg -n "\.chip\s*\{" web/app/globals.css
(no output; rg exit code 1)
```

Any `chip` token anywhere in globals.css. Zero matches.

```
$ rg -n "chip" web/app/globals.css
(no output; rg exit code 1)
```

Base element selectors `button{`, `textarea{`, `input{`, `label{` are absent.
Zero matches.

```
$ rg -n "^\s*button\s*\{|^\s*textarea\s*\{|^\s*input\s*\{|^\s*label\s*\{" web/app/globals.css
(no output; rg exit code 1)
```

The only `button`-bearing selector in globals.css is a state utility, not a base
button rule:

```
$ rg -n "button" web/app/globals.css
584:.gated-button { opacity: 0.7; cursor: not-allowed; }
```

The only `textarea`/`input` selector in globals.css is the `.ask-*` block:

```
$ rg -n "textarea|[^-]input|select" web/app/globals.css
309:.ask-textarea, .ask-input {
```

LGC token families are not present at HEAD (so CVP must not introduce them):

```
$ rg -n "\-\-glass|\-\-text-ink" web/app/globals.css
(no output; rg exit code 1)
```

Conclusion from greps: the home controls have no class-level styling and no base
element styling, so they render as native OS widgets today. `.ask-label`,
`.ask-textarea`, and `.ask-input` exist but are not referenced anywhere on the
home render path (the home uses bare `<label>` and bare `<textarea>` at
`AdaptiveExplore.tsx:335,337`, not the `.ask-*` classes).

## The `.ask-*` block (globals.css:308-318)

```308:318:web/app/globals.css
.ask-label { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.9rem; font-weight: 600; }
.ask-textarea, .ask-input {
  width: 100%;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 0.65rem 0.75rem;
  font: inherit;
  font-weight: 400;
}
```

These three classes are defined and styled for the `/ask` sighting-check layout
(`.ask-layout`, `.ask-map-card`, `.ask-chat-card` at globals.css:296-307). They
are present but unused on the anonymous home console.

## Safe tokens to reuse vs families to avoid

Read from the `:root` block at globals.css:1-13. These variables already exist and
are SAFE for CVP to reuse:

| Token | Value | CVP use |
| --- | --- | --- |
| `--surface` | `#121821` | card-level fill if needed |
| `--surface-2` | `#1a2230` | input/textarea/chip fill |
| `--border` | `#233040` | 1px borders on every control |
| `--text` | `#e6edf3` | control foreground text |
| `--text-muted` | `#8b97a7` | placeholder/secondary text |
| `--accent` | `#4fb8d8` | focus ring, hover border, primary button fill, selected chip |
| `--radius` | `10px` | corner radius on all controls |
| `--fail` | `#e0625f` | only if a control needs an error border; `.error` already owns messages |

Families to AVOID (LGC owns these; not present at HEAD and CVP must not add them):
`--glass-*` and `--text-ink`. CVP must also not touch ghost-text, self-hide, or
preload behavior (LGC owns those) and must not change any copy strings (CXR owns
copy). CVP is style only.

## Proposed CVP baseline class set with states

New classes are namespaced `cvp-` so they are disjoint from `.ask-*` and from
existing utility classes. States reuse only the `:root` tokens above.

- `.cvp-button` (primary action; maps to the Ask button and the InterestForm CTA)
  - default: `background var(--accent)`, `color var(--bg)`, `border 1px solid transparent`, `border-radius var(--radius)`, padding, `font: inherit`, `cursor pointer`
  - hover: slightly brighter accent or `filter: brightness(1.08)`
  - focus / focus-visible: `outline none` plus `box-shadow 0 0 0 3px rgba(79,184,216,0.16)` (matches the existing `.chat-composer:focus-within` ring at globals.css:331-333)
  - disabled: `opacity 0.5`, `cursor not-allowed` (paired with the existing `disabled` attr)
- `.cvp-button--ghost` (optional secondary; transparent fill, `border 1px solid var(--border)`, `color var(--text)`) with the same hover/focus/disabled states. Use only if a non-primary button appears; not required for the current inventory.
- `.cvp-chip` (maps to `className="chip"` buttons at AdaptiveExplore.tsx:313,330 and the result anchors at InterestForm.tsx:52,57,62)
  - default: `display inline-flex`, `align-items center`, `background var(--surface-2)`, `color var(--text)`, `border 1px solid var(--border)`, `border-radius 999px`, small padding, `font: inherit`, `cursor pointer`, `text-decoration none` for the anchor variant
  - hover: `border-color var(--accent)`, `color var(--text)`
  - focus / focus-visible: accent box-shadow ring as above
  - selected (`[data-active="true"]`, `[aria-pressed="true"]`): `border-color var(--accent)`, `color var(--accent)`. This formalizes the inline `style` at AdaptiveExplore.tsx:316-320 so the inline override can later be removed by the implementer; CVP defines the rule, it does not edit the component.
  - disabled: `opacity 0.5`, `cursor not-allowed`
- `.cvp-input` (maps to InterestForm.tsx:98,99)
  - default: `width 100%`, `background var(--surface-2)`, `border 1px solid var(--border)`, `border-radius var(--radius)`, `color var(--text)`, padding, `font: inherit`
  - placeholder: `color var(--text-muted)` via `::placeholder`
  - hover: `border-color` toward `--accent` (subtle)
  - focus / focus-visible: `border-color var(--accent)` plus the accent box-shadow ring
  - disabled: `opacity 0.5`, `cursor not-allowed`
- `.cvp-textarea` (maps to AdaptiveExplore.tsx:337)
  - same token set as `.cvp-input` plus `resize vertical`, `min-height` for the 2-row composer; identical hover/focus/disabled/placeholder states
- `.cvp-field-label` (maps to bare `<label>` at AdaptiveExplore.tsx:335 and optionally InterestForm.tsx:84)
  - default: `display flex`, `flex-direction column`, `gap 0.35rem`, `font-size 0.9rem`, `font-weight 600`, `color var(--text)`
  - no interactive states needed; it is a text label wrapper

## No-collision argument vs `.ask-*` (by selector)

The new set is disjoint from the orphaned `.ask-*` block by selector, so CVP adds
rules without renaming or redefining the existing ones:

- Existing selectors: `.ask-label`, and `.ask-textarea, .ask-input`
  (globals.css:308-318). CVP does not write any selector that begins with `.ask-`,
  does not add `.ask-textarea`, `.ask-input`, or `.ask-label` to its rules, and
  does not add a base `label`, `textarea`, or `input` element selector that would
  cascade onto `/ask`.
- New selectors all carry the `cvp-` prefix: `.cvp-button`, `.cvp-button--ghost`,
  `.cvp-chip`, `.cvp-input`, `.cvp-textarea`, `.cvp-field-label`. There is no
  selector-name overlap with `.ask-label`/`.ask-textarea`/`.ask-input`, so neither
  rule set can override the other and specificity is equal-and-separate (single
  class selectors in both sets).
- `.cvp-chip` does not reuse the bare `chip` name. The implementer would later swap
  `className="chip"` to `className="cvp-chip"` in the component (an edit outside
  this read-only audit). Until then `.chip` remains unstyled, which is the current
  defect, and CVP defining `.cvp-chip` cannot regress `/ask` because `/ask` uses no
  chip.
- CVP reuses only `:root` tokens (`--surface`, `--surface-2`, `--border`,
  `--text`, `--text-muted`, `--accent`, `--radius`). These are the same tokens the
  `.ask-*` block already consumes, so the two sets stay visually consistent without
  sharing a selector.

## Read-only attestation

The only file written by this agent is
`.cca/catalogue/O0/20260628_console-visual-pass/findings/CVP-CONTROLS.md`. No files
under `web/`, `src/`, or elsewhere were edited. No dev server, build, commit, push,
or deploy was run.

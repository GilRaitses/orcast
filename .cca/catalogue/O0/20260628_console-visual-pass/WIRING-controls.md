# WIRING-controls — W3 integrator edit list for cvp-controls.css

Lane console-visual-pass (CVP), Wave 2 build agent B1. This file is the wiring
spec for the net-new paint file `web/app/styles/cvp-controls.css`. B1 produced
net-new files only and did not integrate. Every edit below is for the W3
integrator to apply; none of these edits were made by B1.

Per the binding O0 ruling D-1 (lane STEP_LOG S03) the file styles the existing
`.chip` class and the bare `button` / `textarea` / `input` / `label` elements
directly. It uses no `.cvp-*` class namespace, so the markup already matches and
className edits are NONE for every control.

## 1. Required edit — import the file (one line, one file)

`web/app/styles/cvp-controls.css` is not imported anywhere. The integrator adds
exactly one `@import` to `web/app/globals.css`.

Insertion guidance. The `@import` must sit at the very top of `globals.css`,
before the `:root` block at line 1, because CSS requires every `@import` to
precede all other rules except `@charset`. There is no `@charset` in the file,
so the import becomes the new line 1 and the current `:root {` shifts to line 2.

Exact line to add as the new first line of `web/app/globals.css`:

```css
@import "./styles/cvp-controls.css";
```

Ordering note. Importing first means `globals.css` rules cascade after the CVP
paint. That is intended: existing class rules such as `.btn`, `.chat-send`,
`.chat-link`, and `.ask-textarea` keep winning over the bare `button` /
`textarea` element paint by class specificity, and the CVP `.chip` rules
out-specify the bare `button` paint regardless of order.

## 2. Per-control paint map — className edits

Paint now applies through existing markup. No className change is required for
any control.

| Control | File:line (existing markup) | Selector that paints it | className change |
| --- | --- | --- | --- |
| Branch-option chips | `AdaptiveExplore.tsx:313` | `.chip` (+ `[data-active="true"]` / `[aria-pressed="true"]` selected) | NONE |
| Starter-prompt chips | `AdaptiveExplore.tsx:330` | `.chip` | NONE |
| Composer textarea | `AdaptiveExplore.tsx:337` | `textarea` | NONE |
| Home Ask button | `AdaptiveExplore.tsx:345` | base `button` (primary) | NONE |
| Result link chips (anchors) | `InterestForm.tsx:52,57,62` | `a.chip` | NONE |
| Audience radios | `InterestForm.tsx:85` | none — left native by design | NONE |
| Name text input | `InterestForm.tsx:98` | `input[type="text"]` | NONE |
| Email input | `InterestForm.tsx:99` | `input[type="email"]` | NONE |
| InterestForm CTA button | `InterestForm.tsx:101` | base `button` (primary) | NONE |

Radio note. The text-field rules are scoped to
`textarea, input[type="text"], input[type="email"], input[type="search"]`, so
the `type="radio"` inputs at `InterestForm.tsx:85-91` receive no width:100% and
no box paint. They stay native, as required.

Chip-vs-button note. The branch and starter chips are `<button className="chip">`.
The `.chip` rules carry higher specificity than the bare `button` rule, so chip
buttons read as pills, not primary buttons. No edit needed to keep them distinct.

## 3. Optional edit — NOT required by B1

OPTIONAL (integrator's choice). The inline active-chip style override at
`AdaptiveExplore.tsx:316-320`:

```tsx
style={
  branch === opt.id
    ? { borderColor: "var(--accent, #5aa9e6)", color: "var(--accent, #5aa9e6)" }
    : undefined
}
```

is now redundant because `.chip[data-active="true"]` and
`.chip[aria-pressed="true"]` formalize the selected state in CSS. The integrator
MAY delete this inline `style` prop. B1 does NOT require this edit; the paint is
correct whether or not it is removed (the inline style and the CSS selector set
the same border-color and color). `AdaptiveExplore.tsx` is CXR-held, so leaving
it untouched is the zero-risk default.

## 4. Boundary

- Additive only. No LGC token families: the file adds and references no
  `--glass-*` and no `--text-ink`. It reuses only existing `:root` tokens
  (`--bg`, `--surface`, `--surface-2`, `--border`, `--text`, `--text-muted`,
  `--accent`, `--radius`, `--fail`). The focus ring matches the existing
  pattern `box-shadow: 0 0 0 3px rgba(79, 184, 216, 0.16)`.
- No `.ask-*` redefinition. The file defines no `.ask-label`, `.ask-textarea`,
  `.ask-input`, or any `.ask-*` selector. The bare `label` rule is color-only
  with no `display`/`flex-direction`, so it cannot fight `.ask-label` or the
  `.row` radio-row labels.
- No `.scene-label`, no WFX / `.fx-` selectors, no ghost-text (`.chat-ghost`),
  self-hide, or preload rules.
- No copy or string content changed. Style only.

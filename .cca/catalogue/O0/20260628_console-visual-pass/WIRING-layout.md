# WIRING-layout — W3 integrator edit list for cvp-layout.css

Lane: CVP (console-visual-pass), Wave 2. Author: build agent B2 (layout). This
doc describes the W3 single-integrator edits that wire `cvp-layout.css` into the
product. B2 produced net-new files only and did NOT integrate. Every edit below
is style-only: no copy string changes, no LGC token, additive selectors only.

Pin note: line numbers cite the working tree audited in W1/W2 (HEAD `a914ad1`,
files byte-identical to dispatch pin per CVP-LAYOUT.md). Re-confirm line numbers
at integration time before editing.

---

## 1. globals.css import (REQUIRED)

Add the import for this partial. CSS `@import` must precede all other statements
(except `@charset`), so it goes at the very TOP of `web/app/globals.css`, before
the `:root` block at `globals.css:1`. Insert it immediately AFTER B1's
`cvp-controls.css` import so controls paint loads before layout:

```css
@import "./styles/cvp-controls.css"; /* B1 — added by the integrator */
@import "./styles/cvp-layout.css";   /* B2 — this partial */
```

If B1's import is not present yet, add the `cvp-layout.css` line as the first
statement in the file (still above `:root`). Order: controls then layout.

---

## 2. AdaptiveExplore.tsx — composer fix (REQUIRED)

Binding ruling D-1: reuse the EXISTING `.ask-label` / `.ask-textarea` classes
(globals.css:308-318). Do NOT invent a `.cvp-composer` class. The fix is purely
two `className` additions; it changes NO copy string.

At `AdaptiveExplore.tsx:335`, add `className="ask-label"` to the bare `<label>`:

```tsx
<label className="ask-label">
```

At `AdaptiveExplore.tsx:337`, add `className="ask-textarea"` to the bare
`<textarea>` (keep all existing props — `rows`, `value`, `onChange`,
`placeholder` — unchanged):

```tsx
<textarea
  className="ask-textarea"
  rows={2}
  value={message}
  onChange={(e) => setMessage(e.target.value)}
  placeholder="Ask about a place, a hydrophone, or planning a visit…"
/>
```

This alone removes the composer cramping (label stacks above a full-width
field). No new token, no copy change.

### 2b. AdaptiveExplore.tsx composer card stack (OPTIONAL)

Optional nicety to move the inline `marginBottom` / `marginTop` literals in the
composer card body onto one container gap. At `AdaptiveExplore.tsx:303`, add
`cvp-stack` to the composer card div:

```tsx
<div className="card cvp-stack">
```

If applied, the following inline styles in that card become redundant and MAY be
removed by the integrator (OPTIONAL — leaving them is harmless):
- `AdaptiveExplore.tsx:304` `style={{ marginBottom: "0.6rem" }}` on `div.orienting-question`
- `AdaptiveExplore.tsx:328` `marginBottom: "0.6rem"` (keep `flexWrap`/`gap`) on the starter `div.row`
- `AdaptiveExplore.tsx:344` `style={{ marginTop: "0.6rem" }}` on the send `div.row`

The two chip rows at `:308` and `:328` keep their own `gap: "0.4rem"`; if you
prefer to move that onto a class, swap each to `className="row cvp-stack--sm"`
is NOT recommended (those are horizontal flex rows, not vertical stacks) — leave
the inline `gap` on the chip rows.

---

## 3. InterestForm.tsx — form layout (className additions/swaps)

`.interest-card`, `.interest-options`, `.interest-links` already exist in the
markup, so they need NO edit — only the new CSS rules in `cvp-layout.css` apply
to them. The one new class is `.interest-option`.

### REQUIRED

- `InterestForm.tsx:84` — swap the audience option `label` class from `row` to
  `interest-option` (this is the class that replaces the inline alignment style):

```tsx
<label key={a.id} className="interest-option">
```

### OPTIONAL inline-style removals (now redundant; integrator MAY remove)

Once the CSS rules apply, these inline `style={{...}}` literals are redundant.
Removing them is OPTIONAL; each is safe to delete because the equivalent value
now lives in `cvp-layout.css`. Do NOT change any text/copy.

- `InterestForm.tsx:50` — `div.interest-links.row`: remove
  `style={{ flexWrap: "wrap", gap: "0.4rem", marginTop: "0.5rem" }}` (the
  flex-wrap + gap now come from `.interest-links`; the `marginTop` is absorbed by
  the `.interest-card` gap). OPTIONAL.
- `InterestForm.tsx:81` — `p.muted` blurb: remove `style={{ marginTop: "0.2rem" }}`
  (the `.interest-card` flex gap now owns blurb spacing). OPTIONAL.
- `InterestForm.tsx:82` — `div.interest-options`: remove
  `style={{ display: "flex", flexDirection: "column", gap: "0.4rem", margin: "0.5rem 0" }}`
  (now in `.interest-options`; outer margin is absorbed by `.interest-card` gap).
  OPTIONAL.
- `InterestForm.tsx:84` — `label`: remove
  `style={{ gap: "0.45rem", alignItems: "flex-start" }}` (now in
  `.interest-option`). Pairs with the REQUIRED class swap above. OPTIONAL once
  the class is applied.
- `InterestForm.tsx:90` — `input[type=radio]`: remove
  `style={{ marginTop: "0.25rem" }}` only if the radio still aligns acceptably
  with `align-items: flex-start` on `.interest-option`. OPTIONAL; safest to keep.
- `InterestForm.tsx:98` — name `input[type=text]`: remove
  `style={{ marginBottom: "0.4rem" }}` (the `.interest-card` gap now owns
  field-to-field spacing). OPTIONAL. If you want the inputs to get the shared
  surface/border, ALSO add `className="ask-input"` here (OPTIONAL, see below).
- `InterestForm.tsx:100` — submit `div.row`: remove
  `style={{ marginTop: "0.6rem" }}` (absorbed by the `.interest-card` gap).
  OPTIONAL.

### OPTIONAL field surface (reuse existing classes, not defined by this partial)

To give the two bare text inputs the shared surface/border, the integrator MAY
add `className="ask-input"` to the inputs at `InterestForm.tsx:98` and `:99`, and
wrap each in an `.ask-label` if a visible field label is wanted. This reuses
existing `globals.css:308-318` classes (NOT defined in cvp-layout.css) and is
control-surface scope shared with B1; treat as OPTIONAL and coordinate with the
controls partial. No copy change.

---

## 4. Boundary statement

All edits above are style-only. No copy/string is added, removed, or changed
(the form copy is CXR-owned). No LGC token is introduced (`--glass-*`,
`--text-ink`, `.glass-surface`, ghost-text, self-hide, preload are untouched).
`cvp-layout.css` adds only the `--cvp-space-*` token family and additive layout
selectors; it redefines no existing selector and does not touch `.ask-*` or
global `.card` (the only `.card` reference is the scoped `.explore-console > .card`
descendant rule and a media-scoped padding override).

---

## 5. W3 edit list (verbatim summary)

REQUIRED:
1. globals.css (top, above `:root`, after the cvp-controls.css import):
   `@import "./styles/cvp-layout.css";`
2. AdaptiveExplore.tsx:335 — `<label>` → `<label className="ask-label">`
3. AdaptiveExplore.tsx:337 — `<textarea>` → add `className="ask-textarea"`
4. InterestForm.tsx:84 — `className="row"` → `className="interest-option"`

OPTIONAL:
5. AdaptiveExplore.tsx:303 — `className="card"` → `className="card cvp-stack"`,
   then remove inline margins at :304, :328 (marginBottom only), :344.
6. InterestForm.tsx — remove now-redundant inline styles at :50, :81, :82, :84,
   :90, :98, :100; optionally add `className="ask-input"` at :98 and :99.

# CVP-LAYOUT — layout / hierarchy audit (W1 Agent A2, read-only)

Lane: CVP (console visual pass). Agent: A2 (layout / hierarchy). Mode: READ-ONLY discovery.
Owns exactly one file: this doc. No `web/` edit, no dev server, no build, no commit.

Pin reconciliation: dispatch named `main 97b6397`; actual HEAD at audit time is
`a914ad1` (`git rev-parse HEAD` = `a914ad1bdb482cc5a13ba514eba808ba7082b3a6`). The two
home files audited here are byte-identical across that range
(`git log 97b6397..a914ad1 -- web/app/components/AdaptiveExplore.tsx web/app/components/InterestForm.tsx`
returns no commits), so every cite below is valid at both the pin and current HEAD.

Anonymous path: `/` -> `web/app/components/AdaptiveExplore.tsx` -> `SceneHost` ->
`web/app/components/scene/SalishScene.tsx`. Console UI lives in `AdaptiveExplore.tsx`;
the Get-access card lives in `web/app/components/InterestForm.tsx`, mounted from
`AdaptiveExplore.tsx:397`.

---

## 1. Current state (every claim cites file:line)

### 1.1 The cramped composer

The home composer is a bare `<label>` wrapping a `<textarea rows={2}>`, with no
`className` and no `width`, so the textarea renders inline next to the label text and
falls back to the browser default `cols` width. Source `AdaptiveExplore.tsx:335-343`:

```335:343:web/app/components/AdaptiveExplore.tsx
            <label>
              Ask about the Salish Sea
              <textarea
                rows={2}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about a place, a hydrophone, or planning a visit…"
              />
            </label>
```

Two reasons it sits cramped:

- No `className` on the `<label>` or `<textarea>`, so neither receives the existing
  `.ask-label` (flex column) or `.ask-textarea` (`width: 100%`) rules at
  `globals.css:308-318`. The label and field are laid out as default inline-block flow.
- No base `label` / `textarea` rule exists in `globals.css` (confirmed by A1's controls
  audit and by the charter grounding at `WAVESET_CHARTER.md:23-28`), so the field has no
  width, padding, surface, or border, and the OS default applies.

### 1.2 Inline `style={{...}}` on the home layout (ad-hoc spacing today)

Every spacing / layout decision on the anonymous home is an inline literal, not a class.
Inventory in `AdaptiveExplore.tsx`:

| file:line | element | inline style |
|-----------|---------|--------------|
| `AdaptiveExplore.tsx:304` | `div.orienting-question` | `marginBottom: "0.6rem"` |
| `AdaptiveExplore.tsx:305` | `span.muted` (section label) | `display: "block", marginBottom: "0.35rem", fontSize: "0.85rem"` |
| `AdaptiveExplore.tsx:308` | `div.row` (branch chips) | `flexWrap: "wrap", gap: "0.4rem"` |
| `AdaptiveExplore.tsx:316-320` | `button.chip` (active branch) | conditional `borderColor`/`color` set to `var(--accent, #5aa9e6)` |
| `AdaptiveExplore.tsx:328` | `div.row` (starter prompts) | `flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.6rem"` |
| `AdaptiveExplore.tsx:344` | `div.row` (send button) | `marginTop: "0.6rem"` |
| `AdaptiveExplore.tsx:379` | `strong` (assistant label) | `display: "block"` |
| `AdaptiveExplore.tsx:385` | `div` (streaming reply) | `whiteSpace: "pre-wrap"` |

The Get-access card (`InterestForm.tsx`) is the same pattern, all inline:

| file:line | element | inline style |
|-----------|---------|--------------|
| `InterestForm.tsx:50` | `div.interest-links.row` | `flexWrap: "wrap", gap: "0.4rem", marginTop: "0.5rem"` |
| `InterestForm.tsx:81` | `p.muted` (blurb) | `marginTop: "0.2rem"` |
| `InterestForm.tsx:82` | `div.interest-options` | `display: "flex", flexDirection: "column", gap: "0.4rem", margin: "0.5rem 0"` |
| `InterestForm.tsx:84` | `label.row` (audience option) | `gap: "0.45rem", alignItems: "flex-start"` |
| `InterestForm.tsx:90` | `input[type=radio]` | `marginTop: "0.25rem"` |
| `InterestForm.tsx:98` | `input[type=text]` (name) | `marginBottom: "0.4rem"` |
| `InterestForm.tsx:99` | `input[type=email]` | (no inline style, bare input) |
| `InterestForm.tsx:100` | `div.row` (submit) | `marginTop: "0.6rem"` |

The recurring literal rhythm across both files is `0.2 / 0.25 / 0.35 / 0.4 / 0.45 /
0.5 / 0.6 rem`, all hand-set per element. There is no shared spacing scale.

### 1.3 Container / panel structure and the spacing it uses

The home tree (`AdaptiveExplore.tsx:276-400`):

- `main.explore-shell` `:277`
- `header.explore-header` `:278` (`hero-title`, `hero-subtitle`, optional `.explore-anon-note` at `:285`)
- `div.explore-grid` `:292`
  - `div.explore-scene` `:293` (the 3D scene)
  - `aside.explore-console` `:302`
    - `div.card` `:303` — composer card (orienting chips, starter chips, the bare composer `:335`, send button `:344`)
    - `ActiveSurfaceHost` `:357` (plan panels, only after a turn)
    - `div.card.explore-replies` `:368` — transcript (only when `turns.length > 0`)
    - `InterestForm` `:397` -> renders `div.card.interest-card` (`InterestForm.tsx:79`)

The CSS that governs this hierarchy (all in `globals.css`):

- `.explore-shell { max-width: 1400px; margin: 0 auto; padding: 1.5rem 1.5rem 3rem; }` `:468`
- `.explore-header { margin-bottom: 1.25rem; }` `:469`
- `.explore-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(320px, 1fr); gap: 1.25rem; align-items: start; }` `:477-482`
- `.explore-scene { height: 560px; ... }` `:486-493`
- `.explore-console { display: flex; flex-direction: column; gap: 1rem; }` `:494`
- `.explore-replies { display: flex; flex-direction: column; gap: 0.75rem; max-height: 320px; overflow-y: auto; }` `:495`
- `.card { ... padding: 1.25rem; margin-bottom: 1.25rem; }` `:71-77`
- `.row { display: flex; gap: 1rem; flex-wrap: wrap; }` `:113`

So inter-panel rhythm is set in two competing places: the console column gives a `1rem`
flex gap (`:494`) while each `.card` also carries `margin-bottom: 1.25rem` (`:77`). Inside
a card, the inline `marginBottom`/`marginTop` literals from 1.2 stack on top. The default
`.row { gap: 1rem }` is overridden to `0.4rem` inline at every chip row, so the base `.row`
gap never actually applies on the home composer.

### 1.4 The Get-access form is present but unstyled (dispatch reconciliation)

The dispatch states there is NO Get-access form on the anonymous home. Current tree
contradicts this: `InterestForm` is imported at `AdaptiveExplore.tsx:8` and rendered
unconditionally (no `signedIn` guard) at `AdaptiveExplore.tsx:397`, and it renders a
"Get access" card at `InterestForm.tsx:78-107`. It was present at the pin too
(`git show 97b6397:.../AdaptiveExplore.tsx` shows the import and the `:397` render).

The accurate defect is not a missing component, it is a missing form layer: the form has
no dedicated CSS. `rg -n "interest|get-access" web/app/globals.css` returns zero, so the
classNames already in the markup (`.interest-card`, `.interest-options`, `.interest-links`
at `InterestForm.tsx:48,79,82,50`) are inert, and the two `<input>` fields at
`InterestForm.tsx:98-99` are bare (no `.ask-input` class, and no base `input` rule exists).
The fields therefore render as native OS inputs with no width, surface, or border. The
build-wave task is to style the existing form, not to author a new one.

---

## 2. Existing token + breakpoint inventory

### 2.1 `:root` tokens (`globals.css:1-13`)

Color and one radius. There is no spacing, sizing, or shadow token.

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

Non-LGC tokens available to reuse: `--bg`, `--surface`, `--surface-2`, `--border`,
`--text`, `--text-muted`, `--accent`, `--pass`, `--fail`, `--warn`, `--radius`. None are
LGC families (no `--glass-*`, no `--text-ink`). There is NO spacing token, so any spacing
in the proposal is either a literal rem on a CVP class or a CVP-introduced `--cvp-space-*`
token. I flag the spacing-token choice for A4 / O0 in section 5; this doc reuses the
existing rem rhythm rather than inventing a token family.

### 2.2 Existing form / field classes to reuse (`globals.css:308-318`)

The styled field classes already exist and are the correct reuse target for both the
composer and the form fields:

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

`.ask-label` is a flex column (label stacks above its field). `.ask-textarea` and
`.ask-input` are `width: 100%` with surface, border, radius, padding. The home composer
and the form inputs simply do not use them today.

### 2.3 Other layout-relevant rules

`.card` `:71-77`, `.row` `:113`, `.grid2` `:114-117`, `.chip` is referenced in markup but
has no rule (A1 owns the `.chip` baseline; do not redefine here), `.explore-*` shell
`:467-495`, `.ask-layout` grid `:296-304`, `.chat-composer` family `:319-405` (this is the
LGC-adjacent ghost-text composer; CVP must NOT adopt `.chat-ghost` / ghost-text, per the
charter `WAVESET_CHARTER.md:58-60`).

### 2.4 Existing breakpoints (`rg -n "@media" web/app/globals.css`)

| line | query | what stacks / changes |
|------|-------|-----------------------|
| `globals.css:47` | `max-width: 768px` | `.auth-status` padding tightens, `.auth-email` hidden |
| `globals.css:64` | `max-width: 768px` | `.nav` gap/padding tighten, `.nav-subtitle` hidden |
| `globals.css:115` | `max-width: 768px` | `.grid2` collapses to one column |
| `globals.css:122` | `max-width: 768px` | `.hero-title` / `.hero-subtitle` shrink |
| `globals.css:302` | `max-width: 960px` | `.ask-layout` collapses to one column |
| `globals.css:483` | `max-width: 980px` | `.explore-grid` collapses to one column (scene stacks above console) |

So the home grid already collapses at 980px. The two established breakpoints are 980px
(home grid) and 768px (compact nav / hero / grid2). The proposal reuses these two and adds
no third.

---

## 3. Proposed CVP layout (style only, baseline classes, no LGC token)

### 3.1 Composer — full width, label stacked above the textarea

Target read: the label sits on its own line above a full-width textarea inside the
composer `.card`, matching the existing `.ask-layout` chat composer behaviour.

Reuse the classes that already exist:

- Apply `.ask-label` to the `<label>` at `AdaptiveExplore.tsx:335` (flex column already
  stacks label text above the field).
- Apply `.ask-textarea` to the `<textarea>` at `AdaptiveExplore.tsx:337` (gives
  `width: 100%`, surface, border, radius, padding from `globals.css:309-318`).

This alone removes the cramping with zero new tokens and no copy change. If the build wave
wants the composer block to own its own vertical rhythm independent of the inline
`marginTop` on the send row (`AdaptiveExplore.tsx:344`), introduce ONE CVP baseline
wrapper class:

- `.cvp-composer` — `display: flex; flex-direction: column; gap: 0.6rem;` applied to a
  wrapper around the label + send row, so the `0.6rem` literal moves out of inline style
  and into one class. Field control styling (the textarea itself, base `button`) stays
  A1's baseline set; this class is layout only.

Naming note: A1 owns base `button` / `textarea` / `input` / `label` and `.chip`. A2
introduces only layout containers. The synthesis step (`SYNTHESIS_cvp.md`) resolves
whether the composer wrapper is named `.cvp-composer` (A2) or folded into A1's set.

### 3.2 Panel hierarchy and the spacing scale

Defect: rhythm is set twice (the console flex `gap: 1rem` at `globals.css:494` plus
`.card { margin-bottom: 1.25rem }` at `globals.css:77`) and then patched per element with
inline `marginBottom`/`marginTop`. Proposal: a single owner for inter-panel rhythm and one
named scale for intra-card rhythm.

Inter-panel rhythm (between the composer card, plan panels, transcript, Get-access card):
keep the flex gap on `.explore-console` as the single source and stop relying on
`.card` margin inside the console. CVP adds a scoped reset:

- `.explore-console > .card { margin-bottom: 0; }` so the `1rem` console gap
  (`globals.css:494`) is the only inter-panel spacing. This is additive (a new descendant
  selector), reuses the existing `--surface`/`--border`/`--radius` card surface, and does
  not touch `.card` globally.

Intra-card rhythm (inside a card: section label, chip rows, composer, submit): name the
de-facto scale already in the markup and apply it through classes instead of inline
literals. The scale, drawn from the literals counted in 1.2:

| step | value | role |
|------|-------|------|
| `xs` | `0.35rem` | label-to-field, tight inline gaps |
| `sm` | `0.4rem` | chip-row gap, option gap |
| `md` | `0.6rem` | between sub-blocks inside a card (orienting -> starters -> composer -> send) |
| `lg` | `1rem` | inter-panel (the existing `.explore-console` gap) |
| `xl` | `1.25rem` | card padding / shell rhythm (existing `.card` + `.explore-header`) |

These five steps already exist as literals; CVP codifies them as the documented scale and
applies them via the layout classes below (`.cvp-stack`, `.cvp-stack--sm`). The build wave
expresses them as literal rem on those classes (matching today's values). Whether to also
mint `--cvp-space-xs..xl` tokens is a baseline-token question for A4 / O0 and is NOT
required for the layout to land.

Optional one container class to replace the repeated inline `marginBottom` between
sub-blocks:

- `.cvp-stack` — `display: flex; flex-direction: column; gap: 0.6rem;` (the `md` step) for
  the composer card body, replacing the inline `marginBottom: 0.6rem` at
  `AdaptiveExplore.tsx:304,328` and `marginTop: 0.6rem` at `:344`.
- `.cvp-stack--sm` — same with `gap: 0.4rem` for chip rows, replacing the inline
  `gap: 0.4rem` at `:308,328`.

### 3.3 Get-access form spec (structure only, no final copy)

Restyle the EXISTING `InterestForm` (`InterestForm.tsx:78-107`). The build wave adds CSS
for classNames already in the markup plus reuses `.ask-label` / `.ask-input`; it does not
author new copy and does not change the component's field set. Field layout, top to bottom,
single column, full width inside the `.card.interest-card`:

1. Heading row. Existing `<strong>` at `InterestForm.tsx:80` (copy owned by CXR; abstract
   placeholder only, render as the card title block). Optional new class `.interest-title`
   for type scale; or reuse `.console-panel-title`.
2. Blurb line. Existing `p.muted` at `:81`. Reuse `.muted`; drop the inline
   `marginTop: 0.2rem` into the `xs` step on the card stack.
3. Audience option group. Existing `div.interest-options` at `:82` -> add CSS rule
   `.interest-options { display: flex; flex-direction: column; gap: 0.4rem; }` (the `sm`
   step), replacing the inline style. Each option is a `label.interest-option` (rename the
   inline `.row` usage at `:84` to a dedicated class) laid out as
   `display: flex; align-items: flex-start; gap: 0.45rem;` so the radio aligns to the top
   of a two-line label. Radio is the native control styled by A1's base `input` rule; drop
   the inline `marginTop: 0.25rem` into the option class.
4. Text fields. The name `<input type="text">` (`:98`) and email `<input type="email">`
   (`:99`) each wrapped in (or preceded by) an `.ask-label` and given `.ask-input`
   (`globals.css:309-318`) for full-width surface/border. Field-to-field gap is the `sm`
   step via the card stack, replacing the inline `marginBottom: 0.4rem` at `:98`.
5. Submit control. Existing `div.row` at `:100` holding the button. Reuse `.row`; the
   button itself is A1's base `button` baseline. Drop the inline `marginTop: 0.6rem` into
   the `md` step.
6. Error line. Existing `p.error` at `:105` (unchanged; copy owned upstream).
7. Result state. The success branch (`InterestForm.tsx:45-69`) reuses the same
   `.interest-links.row` chip layout; add CSS for `.interest-links { display: flex;
   flex-wrap: wrap; gap: 0.4rem; }` replacing the inline style at `:50`.

Markup shape (structure only, copy is placeholder and CXR-owned):

```html
<div class="card interest-card">
  <strong class="interest-title"><!-- CXR: card title --></strong>
  <p class="muted"><!-- CXR: blurb --></p>
  <div class="interest-options">
    <label class="interest-option">
      <input type="radio" name="audience" />
      <span><strong><!-- CXR: option label --></strong> <span class="muted"><!-- CXR: option blurb --></span></span>
    </label>
    <!-- repeat per audience option -->
  </div>
  <label class="ask-label"><!-- CXR: name label -->
    <input class="ask-input" type="text" />
  </label>
  <label class="ask-label"><!-- CXR: email label -->
    <input class="ask-input" type="email" />
  </label>
  <div class="row">
    <button type="button"><!-- CXR: submit label --></button>
  </div>
  <p class="error"><!-- runtime error --></p>
</div>
```

All inner text is a placeholder comment. No string in the markup above is a final user
copy value; CXR owns every label, blurb, and CTA.

### 3.4 Mobile breakpoints

Reuse the two established breakpoints; add no third.

- `max-width: 980px` (existing `globals.css:483`): `.explore-grid` already collapses to one
  column, so the scene stacks above the console and the composer + form become full-width
  single column with no extra rule needed. Confirm the composer textarea and `.ask-input`
  fields are already `width: 100%`, so they fill the collapsed column.
- `max-width: 768px` (existing, used by nav / hero / grid2): tighten the shell padding and
  card padding for phones. Add a CVP block:
  - `.explore-shell { padding: 1rem 1rem 2rem; }` (down from the `1.5rem 1.5rem 3rem` at
    `globals.css:468`).
  - `.card { padding: 1rem; }` scoped under the console if A4's boundary prefers not to
    touch global `.card`, otherwise as a media-scoped override.
  - The Get-access audience options and the chip rows already wrap (`flex-wrap: wrap`), so
    they reflow without a new rule.

No layout needs a sub-768px breakpoint; the single-column stack from 980px down already
holds at phone widths.

---

## 4. Boundary statement (style-only + no-LGC-token, by string and by class)

Copy boundary (by string): the proposal changes NO anonymous-path copy string. Every text
node stays as-is. The composer label text "Ask about the Salish Sea"
(`AdaptiveExplore.tsx:336`), the placeholder
"Ask about a place, a hydrophone, or planning a visit…" (`:341`), the section label
"What brings you here?" (`:306`), all `STARTER_PROMPTS` (`:23-27`), all `BRANCH_OPTIONS`
labels (`:32-37`), the Get-access "Get access" title (`InterestForm.tsx:80`), its blurb
(`:81`), the `AUDIENCES` labels/blurbs (`:6-10`), the input placeholders (`:98-99`), and
the CTA strings (`:71-76,102`) are untouched. Where the form markup shows a placeholder
comment, it is a structural placeholder only; CXR owns the final string.

LGC-token boundary: the proposal adds NO LGC token family. No `--glass-*`, no `--text-ink`,
no `.glass-surface`. No ghost-text (`.chat-ghost` at `globals.css:347-361` is NOT adopted),
no self-hiding dock, no consent preload. Every color reference reuses an existing non-LGC
token from `:root` (`--surface-2`, `--border`, `--text`, `--text-muted`, `--accent`,
`--radius`). Spacing reuses the existing rem rhythm; any optional `--cvp-space-*` token is
flagged to A4 / O0 and is not an LGC family.

### Classes the proposal INTRODUCES (CVP baseline, A2-owned layout)

- `.cvp-composer` — composer wrapper, vertical stack (optional; may fold into A1).
- `.cvp-stack`, `.cvp-stack--sm` — intra-card vertical rhythm (`md` / `sm` steps).
- `.interest-option` — single audience option row (replaces inline `.row` usage at
  `InterestForm.tsx:84`).
- `.interest-title` — Get-access heading type (optional; may reuse `.console-panel-title`).
- CSS RULES for classNames already in the markup but currently unstyled:
  `.interest-card`, `.interest-options`, `.interest-links`. These names exist in the JSX
  (`InterestForm.tsx:48,79,82,50`); the proposal gives them rules, it does not invent names.
- Scoped additive selectors: `.explore-console > .card { margin-bottom: 0; }` and the two
  media-query overrides under `max-width: 768px`.

### Classes / tokens the proposal REUSES (no redefine)

- `.ask-label`, `.ask-textarea`, `.ask-input` (`globals.css:308-318`) for the composer and
  form fields.
- `.card`, `.row`, `.muted`, `.explore-shell`, `.explore-grid`, `.explore-console`,
  `.explore-replies` (`globals.css:71-77,113,112,468-495`).
- `.chip` and base `button` / `textarea` / `input` / `label` — A1 owns these; A2 references
  them and does not define or rename them.
- Tokens `--surface-2`, `--border`, `--text`, `--text-muted`, `--accent`, `--radius`.

### Hand-offs / open questions for synthesis + O0

- A1 owns base control classes and `.chip`. Confirm in `SYNTHESIS_cvp.md` whether the
  composer wrapper is A2's `.cvp-composer` or part of A1's control set, to avoid a
  duplicate selector when the W3 single editor wires both partials.
- Spacing tokens: this doc reuses the existing rem rhythm and names a 5-step scale but does
  NOT mint `--cvp-space-*`. A4 owns the globals additive boundary; O0 decides whether CVP
  introduces a spacing-token family or keeps literals on the layout classes.
- Dispatch said the Get-access form is missing; it is present and unstyled
  (`AdaptiveExplore.tsx:397`, `InterestForm.tsx:78-107`). Flagged to O0 so the W2 build
  task is scoped as "style the existing InterestForm", not "author a new form".

# orcast Prose Gate Rules (canon)

Authoritative ruleset for prose across orcast user-facing and audience-facing
surfaces. Compiled from the prose-gate sources:
- `pax/.cursor/rules/grant-prose-punctuation.mdc` (punctuation canon)
- orcast SD-016 prose register in `.cca/CLAIM_BOUNDARIES.md`
- SDR SD-006 (single-author voice), SD-013 (forbidden claims)
- user rule "No Smug Narrative Devices"

This file is the grep source of truth for the `copy-gate` battery target. The
paired Cursor agent rule is `.cursor/rules/prose-gate.mdc`.

---

## Hard-ban (gate FAILS) in user-facing prose, headers, titles, and inline

1. Em dash and en dash as ornament: `—`, `–`, and `--`. Replace with a period or
   a comma, or restructure. Never replace with a colon or parentheses.
2. Semicolons. Split into short sentences or join with "and".
3. Colons in headers, titles, and inline, and decorative `Label: body` colons in
   prose. Use a period and a new sentence, or restructure. Allowed only where
   strictly required by machine format (see exceptions).
4. Parentheses in running prose, headings, subheads, or table cell copy. Rephrase
   with "such as", "including", or "for example", or use separate sentences.
5. Arrows `→`, `=>`, `-->`. Say "leads to", "then", or "so that".
6. Team voice "we", "our", "us" (SD-006). Write first-person singular or direct.
7. Smug narrative devices and double-dash, per the "No Smug Narrative Devices"
   rule (filler, synthetic contrast, reflective hedging, false authority).
8. Meta-framing: "In this section we", "We propose", "This paper contributes",
   "Our approach" (SD-016). Open with the claim.
9. Passive voice for results; hedging "might", "could", "seems"; bullet lists
   inside body prose blocks (SD-016).
10. Forbidden claims (SD-013): "predicts whale locations", "identifies orca
    species from images", "high forecast accuracy", and the rest of the
    CLAIM_BOUNDARIES forbidden set.

## Flag (REPORT, reviewed case-by-case, not auto-removed)

- `, and` Oxford comma. Keep where a list genuinely needs it; otherwise remove.

## Allowed exceptions ("strictly required")

- Markdown / LaTeX / code syntax that the format requires: `#` and `##` headings,
  `| table |` pipes, JSX/TSX, code blocks, LaTeX commands. These are not prose.
- Colons required by machine format: clock times like `14:00`, URLs like
  `https:`, code, and `key: value` in JSON or config that is not rendered as prose.
- Hyphens inside established compounds, for example "cross-domain".
- File paths and machine identifiers in operator-only text that users never see.
- Scientific-paper citation and abbreviation style inside whitepaper `.tex`
  (author-year citations, technical abbreviations, math), per the pax W5 report.

## Scope

Class A, runtime UI copy: `web/app/**` pages and components (JSX text,
`placeholder`/`title`/`aria-label`/default props, empty-states, toasts, notes,
sample and seed text), `web/lib/**` copy (glossary, gateDisplay, constants),
`web/app/api/*/route.ts` client messages, and backend user-facing strings
(interest message, sighting-assist and exploration-guide template replies, gate
labels, default response messages).

Class B, authored communication surfaces: whitepapers
(`docs/whitepaper*/LX/Sections/*.tex` and `MD/`), demo scripts and storyboards,
voiceover narration source, the presentation deck
(`docs/devpost/submission/audit-deck/LX/Sections/*.tex`), devpost copy, and
`.cca/outreach_drafts/*`.

Out of scope: code comments and docstrings, and LLM system-prompt instruction
text.

## Frozen surfaces (detect and propose only, operator-gated)

`docs/devpost/DEVPOST_DRAFT.md` (frozen), the locked demo recording and `a-gate`
(SD-025), and seeded journal entries. Detect violations and propose rewrites, but
do not edit or rebuild these without an explicit operator go.

# CX Copy/Prose Inventory (detection baseline)

Date: 2026-06-27. Source: `tools/waves/gates/copy-gate.sh` + per-area grep.
Ruleset: `.cca/PROSE_GATE_RULES.md`. Hard-ban enforced by the gate today: em dash.
Context-dependent patterns are reported for case-by-case remediation.

## Hard-ban: em dash (—) = 681 total

| Surface | Class | em-dash | Notes |
|---|---|---|---|
| web/app | A | 24 | JSX text, hero titles, placeholders, `?? "—"` empty-value dashes |
| web/lib | A | 5 | glossary, gateDisplay, copy constants |
| src/aws_backend (user-facing strings) | A | ~3 | interest message, sighting-assist/exploration template replies |
| docs/whitepaper | B | 110 | `.tex` sections + research MD (scientific-style exceptions apply) |
| docs/whitepaper2 | B | 17 | `.tex` sections |
| docs/devpost | B | 428 | deck (audit-deck/*.tex), storyboards, devpost copy, figures MD |
| .cca/outreach_drafts | B | 52 | linkedin/github/aimez drafts |
| docs/field-campaign | B | 45 | SUMMIT_DEMO_SCRIPT.md |

Frozen surface: `docs/devpost/DEVPOST_DRAFT.md` holds 7 em-dashes -> detect + propose only (operator-gated).

## Report (context-dependent; reviewed in CX-2)

| Pattern | Count | Disposition |
|---|---|---|
| en dash (–) | 96 | many are legit numeric ranges (pp. 159-166); ban only clause-splice use |
| unicode arrow (→) | 131 | replace in prose; code/diagram syntax exempt |
| semicolons (;) | 2083 | mostly legit (code, CSS, markdown, JSON); ban only in prose sentences/headers |
| Oxford comma (, and) | 503 | flag; keep where a list needs it, else remove |
| voice we / our | 247 / 39 | SD-006; rewrite to first-person singular on user-facing/audience surfaces |
| hedging (might/could/seems) | 20 | SD-016; state what data shows |
| meta-framing | 38 | SD-016; open with the claim |

## Method note
The gate hard-fails em dash only (unambiguous ornament). en dash, arrows,
semicolons, colons, and parentheses are reported because automated hard-fail
would false-positive on numeric ranges, JS `=>`, code, markdown/LaTeX syntax,
and machine colons. CX-2 dispositions these per the strictly-required exceptions;
once the prose layer is cleaned, semicolon/colon/paren-in-prose can be promoted
to hard-fail with a curated allowlist.

## Next (CX-2)
Per-hit before/after proposals: em/en dash -> period or comma or restructure
(never colon or parens); semicolon -> split; arrow/paren/colon rephrase;
`, and` keep/remove; voice/hedging/meta rewrite. Class B hits carry rebuild tags
(whitepaper/deck PDF, voiceover + demo re-stitch); frozen hits are operator-gated.

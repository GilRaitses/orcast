# W0 — Whitepaper charter

Date: 2026-06-24
Wave set: **W** (Whitepaper)
Predecessor: Wave Set **A** complete (A5 `a-gate` PASS)
Capstone: **H1** manual Devpost submit (depends on **W6** PDF build PASS)

## Title

*Evidence-bounded encounter forecasting: an honest-model architecture for effort-biased wildlife observation data*

## Purpose

Produce a citable preprint (arXiv cs.LG / q-bio.QM candidate) establishing the orcast architecture and grounding benchmark as scientific prior art. The paper bridges the science axis (encounter forecasting methodology) and the systems axis (provenance grounding, agent orchestration) into a single unified argument about why evidence-bounding requires both statistical gates and structured citation.

## Section blocking

| # | Section | Families | Core claim |
|---|---------|----------|------------|
| Abstract | 150 words | — | H1 hypothesis, four gaps, pilot scope |
| 1 | The four gaps | SF-1, SF-6 | Effort bias and epistemic opacity are documented failure modes |
| 2 | Gate-bounded honesty model | SF-3, SF-4, SF-5 | Null gating + CV skill can bound confidence without hiding the forecast |
| 3 | Acoustic grounding: PSTH + Level 0 QC | SF-2 | False-positive rates require quarantine before model ingestion |
| 4 | Provenance grounding as a system | SF-7, SF-9, SF-12 | Structured step-log citations reduce unsupported claims vs LLM baselines |
| 5 | Orchestrated managed agents with verified tools | SF-8 | Plan-then-execute with manifest dispatch reduces tool hallucination |
| 6 | Governance: quarantine, authority, audit | SF-10 | HITL promotion authority is a necessary condition for citizen-science data |
| 7 | Geospatial grounding limits | SF-11 | Maps grounding leaves 85% of scientific claims uncited (live benchmark) |
| 8 | Limits and falsification | SF-5, SF-6 | H1 falsification table; extension path |

## Caveat table (known open gaps)

| ID | Gap | Section | Treatment |
|----|-----|---------|-----------|
| C-1 | No cetacean-specific effort-correction measurement | 1 | State as open measurement gap; cite analogs (1907.05902, 2110.12951) |
| C-2 | Phase-shuffled null ecology papers absent from arXiv CS | 2 | Cite neuroscience precedents (2010.04875, 1506.02361); note ecology-journal gap |

## Prose gate rules (exit bar for W3)

| Gate | Rule |
|------|------|
| PG-1 | No sentence asserting a quantitative or ecological finding without a bracketed citation or explicit "open measurement gap" caveat |
| PG-2 | Every systems claim about orcast behavior must cite a supporting arXiv ID from the research files or an orcast artifact path |
| PG-3 | SF-1 and SF-4 Partial verdicts must be stated as gaps with the exact reason — not glossed |
| PG-4 | Section 8 must include the falsification table from WHITEPAPER_HYPOTHESIS.md verbatim or extended |
| PG-5 | The 85% uncited-evidence figure must appear in section 7 with the run date, model, and measurement method |
| PG-6 | No parentheses, decorative colons, or em-dashes in section headings |

## Reference resolution rule (W2)

For every arXiv ID in the 12 SF research files:
1. Query CrossRef then Semantic Scholar for a published DOI.
2. If DOI found and journaltitle present: `@article` with `journaltitle + doi + eprint`. Style drops `url`/`eprint` when `doi` is present.
3. If no DOI: `@online` with `eprint/eprinttype=arxiv`.
4. Key: `arxiv` + numeric ID with dots removed.

## Build pipeline (W1)

```
docs/whitepaper/LX/Raitses_orcast_2026.tex  ← root
docs/whitepaper/LX/Sections/               ← tex section inputs
docs/whitepaper/LX/Figures/               ← mermaid .mmd + compiled .pdf
docs/whitepaper/Build/                    ← latexmk output
docs/whitepaper/MD/                       ← prose markdown drafts
docs/whitepaper/Refs/                     ← per-claim reference files
```

Style: 10pt twocolumn, compact margins (0.34–0.36in), lmodern, biblatex/biber numeric.
Build: `latexmk -pdf -outdir=../Build LX/Raitses_orcast_2026.tex`

## Execution order

1. W0 — this charter + registry entries
2. W1 — folder scaffold + LaTeX root + Makefile
3. W2 — reference_audit.py + references.bib + reference_audit.txt
4. W3 — prose MD/ → gate → LX/Sections/ (longest wave)
5. W4 — Equations.tex + Glossary_Content.tex
6. W5 — mermaid figures + Appendix_Diagrams.tex + visual verify
7. W6 — make pdf + visual verify full PDF
8. W7 — next-phase charter (IC8, W-Eval, W-RAG, P1)

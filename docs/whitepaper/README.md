# Whitepaper research workflow

This folder contains the Emergent Mind search-family grid and resulting research summaries for the orcast whitepaper.

## How this works (mirrors the May 2026 workflow)

Each row of [`SEARCH_FAMILY_GRID.md`](SEARCH_FAMILY_GRID.md) is one EM search family. A family corresponds to a falsifiable claim in the whitepaper and a set of arXiv / research topics to verify it against.

**For each family:**

1. Copy the Representative EM Queries column into Emergent Mind (https://www.emergentmind.com). Run 3–5 queries per family.
2. For each relevant paper Emergent Mind surfaces, capture:
   - Paper title + arXiv ID
   - EM summary (1–3 sentences)
   - Whether it supports, contrasts, or is background to the whitepaper claim
   - Whether the orcast artifact cross-link in the grid is consistent with the paper's finding
3. Write a family summary (4–6 sentences) to `research/<family-id>.md` — this is the citable research block for that whitepaper section.

**Naming convention:** `research/SF-01-effort-bias.md`, `research/SF-07-llm-grounding.md`, etc.

**One verification rule per family:** the Verification Target column states exactly what a citation must demonstrate. If no paper found in EM satisfies the target, the whitepaper claim is not supported and must be weakened or removed.

## Folder structure

```
docs/whitepaper/
  README.md               (this file)
  SEARCH_FAMILY_GRID.md   (section blocking + all 12 families)
  research/
    SF-01-effort-bias.md
    SF-02-acoustic-qc.md
    ...                   (one file per family, created as you run searches)
```

## After all families are run

Return to the grid, mark each family Supported / Partial / Not found, and use the summaries to write or validate each whitepaper section. SF-11 (geospatial grounding limits) is already pre-verified by the live benchmark in [`PROVENANCE_GRAPH_CONTRACT.md`](../devpost/casting/PROVENANCE_GRAPH_CONTRACT.md) — no EM run needed.

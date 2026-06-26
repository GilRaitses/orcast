# FA0 — Defect register

Wave Set FA: Figure audit, remediation, and adversarial review  
Date: 2026-06-24

## Severity key

| Severity | Meaning |
|----------|---------|
| P0 | Breaks legibility for judges — blocks submission use |
| P1 | Incorrect or misleading content |
| P2 | Style drift from reference (decisiondb-fig2.png) |

## Defect table

| ID | Sev | Figure | Description | tex_location | Status |
|----|-----|--------|-------------|-------------|--------|
| P0-01 | P0 | fig-01 | Figure ~27cm wide; text unreadable at A4 print width | matrix at (0,0)…at (24,-8.5) absolute coordinates | verified |
| P0-02 | P0 | fig-02 | Title collides with Adapters header (same y region) | `\node[font=\normalsize\bfseries]` placement | verified |
| P0-03 | P0 | fig-03 | FreezeSnapshot/WriteReport nodes invisible (off bounding box) | `at (6.0,-4.5)` and `at (12.0,-4.5)` below visible area | verified |
| P0-04 | P0 | fig-04 | Vercel Next.js web header overwritten by title | title node overlaps first actor | verified |
| P0-05 | P0 | fig-07 | Width >40cm; IC4 node off-page; equations at ~5pt | horizontal pipeline with 9 nodes × 5cm each | verified |
| P1-01 | P1 | fig-01 | sightings table header text floats above lilac cell | matrix row 1 col-span not spanning both columns | verified |
| P1-02 | P1 | fig-01 | S3 artifact dashed border invisible (solid overwrites) | `draw=ORstroke` on matrix + `\draw[dashed]` overlay | verified |
| P1-03 | P1 | fig-02 | covariates→kernel arrow labeled "scheduled keyed calls" | `node[near start, flowlabel, below]{scheduled keyed calls}` | verified |
| P1-04 | P1 | fig-03 | FitAndGate says "L1–L3 gates" without noting L0 already done | node label text | verified |
| P1-05 | P1 | fig-04 | Automation agent header invisible; node body starts mid-box | `\node[BOX] (agent)` + `\node[SUBBOX] (ag1)` chaining | verified |
| P1-06 | P1 | fig-05 | "L1–L3 gate" text renders with strikethrough artifact | `kernel fit, L1-L3 gate verdicts` field text | verified |
| P1-07 | P1 | fig-06 | D (Data) node missing derived_from edge from X2 | X2 → D1 edge: `(X2.west) -| (D1.east)` unreachable | verified |
| P1-08 | P1 | fig-06 | "no signal" badge reads as content claim, not UI example | VN node at `(8.5,-9.5)` with no "example" annotation | verified |
| P1-09 | P1 | fig-07 | IC4 (PIT) text hidden; "pass" edge label obscured | node width 3.6cm; IC nodes overlap | verified |
| P2-01 | P2 | all | (log FK) badge clips against cell border in some rows | `inner xsep=3pt` on column 2 | verified |
| P2-02 | P2 | fig-01 | Column 2 (PK)/(FK) badges inconsistently right-aligned | `anchor=east` missing in some column 2 style definitions | verified |
| P2-03 | P2 | fig-02 | Edge labels "writes sightings", "writes timeseries" overlap | multiple labels at same midway position | verified |
| P2-04 | P2 | fig-04 | Legend box overlaps AppRunner node | legend `anchor=south west` at wrong coordinates | verified |
| P2-05 | P2 | fig-05 | "maps to" double arrows overlap edge path lines | columns at x=0 and x=8.5 too close | verified |
| P2-06 | P2 | fig-06 | Large vertical whitespace between metric root and claims | y=-4.5 for claims; should be y=-2.5 | verified |

## Status history

All defects opened 2026-06-24 during FA0 visual inspection of first-pass TikZ builds.

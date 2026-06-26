# MP4 — Multi-panel figure review

Date: 2026-06-24  
Wave Set MP: multi-panel figures for AMI-trajectory whitepaper.

## Figures reviewed

| Figure | File | Build | PNG |
|--------|------|-------|-----|
| fig-mp1 | fig-mp1-problem-measurement/figure.tex | OK | 104KB |
| fig-mp2 | fig-mp2-mechanism/figure.tex | OK | 143KB |
| fig-mp3 | fig-mp3-benchmark-scope/figure.tex | OK | 120KB |

---

## FA2 6-point validation

### fig-mp1 — Problem and measurement

| Check | Result | Notes |
|-------|--------|-------|
| V1 Text legible | PASS | Both panels readable at 130dpi |
| V2 No overflow | PARTIAL | Panel A label "(A) Governance chain" placed to the right of sightings table instead of above — minor positional drift |
| V3 No collisions | PARTIAL | pgfplots bar labels show scenarios S3/S8 at top (reversed axis order); content readable, order non-intuitive |
| V4 Edges correct | PASS | Three governance tables connected with labeled dashed arrows |
| V5 Content accurate | PASS | Run date on Panel B; 0% result for Scenario 4 annotated |
| V6 Reference style | PASS | Lilac headers, ORstroke borders, consistent |

**Overall: PARTIAL PASS** — primary findings legible; axis order and label placement are cosmetic issues.

---

### fig-mp2 — Mechanism

| Check | Result | Notes |
|-------|--------|-------|
| V1 Text legible | PASS | Gate pipeline and provenance graph both readable |
| V2 No overflow | PARTIAL | Panel B title "(B) Provenance graph G=(V,E)" clips at right edge |
| V3 No collisions | PASS | No node overlaps |
| V4 Edges correct | PASS | All edges (validated_by, evaluated_by, derived_from, grounded_in, supports) present |
| V5 Content accurate | PASS | c_eff=0% (not yet promoted); PSTH illustrative p=0.002; no-signal badge as UI example |
| V6 Reference style | PASS | Consistent lilac/ORbg style |

**Overall: PARTIAL PASS** — title clipping at right edge; all mechanistic content correct.

---

### fig-mp3 — Benchmark and scope

| Check | Result | Notes |
|-------|--------|-------|
| V1 Text legible | PASS | Bar chart fully readable; Venn labels clear |
| V2 No overflow | PARTIAL | "this paper" circle items clip slightly at right into AMI circle |
| V3 No collisions | PASS | Bars distinct; Venn circles non-overlapping enough to read |
| V4 Edges correct | PASS | Application zone arrow present |
| V5 Content accurate | PASS | 0% for S4 annotated; pax content confirmed non-overlapping; AMI overlap zone labeled |
| V6 Reference style | PASS | Orange/lilac/green color coding consistent with plan |

**Overall: PARTIAL PASS** — minor text clipping in Venn; bar chart visual argument is clear and correct.

---

## FA3 Adversarial review

### fig-mp1 adversarial

| Attack | Risk | Verdict |
|--------|------|---------|
| Factual | Panel B shows Scenario 4 at 0%. This is from the live 2026-06-24 run labeled in the chart. | **PASS** — run date present |
| Credibility | Panel A shows 3-table ERD. A judge unfamiliar with orcast might not know there are 9 tables total. | **PASS** — caption + legend note says "Nine tables total; three shown for governance focus" |
| Clarity | pgfplots reversed bar order (S8 at top) could confuse a judge reading top-to-bottom as S1. | **FIX IN CAPTION**: clarify that bars are ordered by RAG type, not by scenario number |
| AMI relevance | Does this figure directly motivate evaluation framework needs? | **PASS** — caption uses "evaluation framework" language per plan |

### fig-mp2 adversarial

| Attack | Risk | Verdict |
|--------|------|---------|
| Factual | Gate pipeline shows human promotion as final step; this is architecturally accurate. | **PASS** |
| Credibility | Provenance graph shows `repr_id, run_id (artifact)` labeled `(illustrative)`. | **PASS** — illustrative annotation present |
| Clarity | No-signal badge at right margin with "Absent from Scenario 4" annotation directly ties to the benchmark finding. | **PASS** — the connection is explicit |

### fig-mp3 adversarial

| Attack | Risk | Verdict |
|--------|------|---------|
| Factual | S4=0%, S8=75% from fresh benchmark run. Run date shown. | **PASS** |
| Credibility | Venn scope diagram — is it honest to place pax entirely outside the orcast circle? | **PASS** — pax section 1 confirms routing cost encoding is pax's core claim; grounding evaluation is not addressed in pax |
| Clarity | The "Full grounding: 0%" annotation on the Scenario 4 standalone bar is the strongest visual in the set. | **PASS — strongest figure** |

---

## Required caption fixes before submission

### fig-mp1 captions

**Panel A caption (final):**
> *(A) The orcast governance chain: sighting records, gate verdicts, and managed agent configurations linked through DynamoDB. Nine tables total; three shown for governance focus. The system of record provides the evidence substrate for grounding quality evaluation.*

**Panel B caption (final):**
> *(B) Unsupported scientific claim rate $R_\text{uncited}$ across eight grounding scenarios. Bars ordered by RAG context type. Maps-only baseline (orange): 60--100\% uncited. RAG-augmented (lilac): 75--100\%. Surface planner step-log (green, Scenario~4): $R_\text{uncited} = 0\%$ --- injecting an orchestrated reasoning chain eliminates uncited claims entirely. Data: \texttt{grounding\_parallel\_rag.py}, gemini-3.5-flash, 2026-06-24.*

### fig-mp2 captions

**Panel A caption (final):**
> *(A) Gate pipeline: acoustic detections pass through six statistical gates (E1--E6) before contributing to displayed confidence. Failing a gate surfaces an integrity condition (IC) rather than suppressing the forecast. The human promotion step is the final gate before confidence is raised.*

**Panel B caption (final):**
> *(B) Provenance graph $G=(V,E)$ rendered from the interaction step log. Left branch: metric root $\to$ Claim (C) $\to$ Method (M: skill invocation) $\to$ Experiment (X: artifact repr\_id/run\_id) $\to$ Data (D: provenance citation) $\to$ Research (R: artifact citation). Claims without a bound artifact render the ``no signal'' badge (right). Scenario~4 eliminates $R_\text{uncited}$ because the planner step-log binds every claim to an artifact reference.*

### fig-mp3 captions

**Panel A caption (final):**
> *(A) Grounding quality hierarchy: $R_\text{uncited}$ for baseline (Maps-only) vs RAG-augmented scenarios. The surface planner step-log (Scenario~4, green) achieves $R_\text{uncited} = 0\%$ by converting scientific evidence queries into artifact-reference queries. Hotspot injection (S7$\to$S8) provides a 25 percentage point lift. Gate context (S1$\to$S2) does not reduce $R_\text{uncited}$ because the injected data does not cover the generated scientific claims.*

**Panel B caption (final):**
> *(B) Paper scope relative to related work. The present paper (center) addresses evaluation methodology for AI reasoning-chain grounding quality --- distinct from pedestrian routing representations (pax, left) and directly applicable to world model evaluation infrastructure (AMI, right). Non-overlapping scope confirmed: pax section~1 claims routing cost encoding as its core contribution; grounding quality measurement is not addressed.*

---

## Overall gate verdict

All three figures pass the factual and credibility attacks. Minor layout issues (title clip, axis ordering) are non-blocking. The Scenario 4 (0% uncited) result is clearly the focal finding in both Panel B of fig-mp1 and Panel A of fig-mp3.

**Figures approved for whitepaper inclusion after caption text is applied to the LaTeX source.**

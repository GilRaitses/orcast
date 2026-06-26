# P2X Defect Register

**Status: RESOLVED 2026-06-26.** All FIX rows landed; P2X-3 adversarial review returned 2 P1 regressions (E5/E6 deviance-skill mislabel; aimez 8-scenario 0% overclaim) which were fixed and re-verified; second-pass residual check CLEAN. WP1+WP2 PDFs rebuilt (10/7/5/4), figures re-exported and visually verified. See resolution notes at end.

Date: 2026-06-26. Source: P2X-0 discovery (3 readonly lanes). Status: P2X-1 classification applied.
Lanes: A=WP prose/number (.tex), B=web/site copy, C=figures, D=deploy hygiene. ESC=escalated to P1.

## ESCALATED (P1 — contract violation / overclaim)

| id | file:line | issue | fix | lane |
|----|-----------|-------|-----|------|
| W6c | docs/whitepaper/LX/Figures/fig-3-provenance-graph.mmd | `grounded_in` drawn X1→R1; contract = **C→R** | repoint to C1→R1, re-export PNG | C/ESC |
| W6d | docs/whitepaper/LX/Appendix_Diagrams.tex:30 | caption "all typed edges match the contract" is false given W6c | true after W6c fix; verify wording | A/ESC |

## FIX — Lane A (WP prose/number)

| id | file:line | fix |
|----|-----------|-----|
| C1 | LX/Sections/01_abstract.tex:2 | "85% on same query" → "Maps-only baseline: 89% uncited on the evidence query, 85% averaged" |
| C4 | LX/Sections/04_acoustic_grounding.tex:13 | add reported FP rate 0.673 (Level-0 QC, 2022-06-22) |
| C4 | LX/Sections/09_limits_falsification.tex:5 | add CV deviance skill −0.018, 3/5 folds to the 0% line |
| W1 | LX/Sections/08_geospatial_limits.tex:39 | "in preparation" → factual companion-report wording (no peer-review claim) |
| W4a | LX/Appendix_Diagrams.tex:40 (fig-4 caption) | add "6 of 6 annotations bound" |
| W4b | LX/Appendix_Diagrams.tex:40 (fig-4 caption) | add "9 scientific sentences, 8 uncited (89%)" |
| W4c | LX/Sections/08_geospatial_limits.tex (S7/S8) | add explicit 25 pp (100%→75%) body line supporting fig caption |
| W5a | LX/Equations.tex:72 | `R_{\text{uncited}}` → `R_{\mathrm{uncited}}` |
| W5b | LX/Glossary_Content.tex:42-43 | unify name to $R_{\mathrm{uncited}}$ + percent style |
| W5c | whitepaper2/LX/Sections/05_rag_lift_hierarchy.tex:27 | "75\% uncited rate" → `$\Runcited=75\%$` |
| W2c | LX/Sections/03_gate_bounded_honesty.tex:25 | "L2 and L3" → E5/E6 (pipeline scheme) |
| W2d | LX/Sections/05_governance.tex:11, 09:5 | disambiguate L1–L3 as kernel-program levels on first use |
| W4d | LX/Sections/05_governance.tex | add nine-table system-of-record fact (supports fig-mp1 caption) |

## FIX — Lane B (web/site copy + outreach)

| id | file:line | fix |
|----|-----------|-----|
| C3 | web/app/page.tsx:285 | "world model systems" → "human-in-the-loop agentic systems" |
| C3 | .cca/outreach_drafts/aimez_ai_post_v1.md:40,59 | same title fix |
| C3 | .cca/outreach_drafts/github_release_note_v1.md:10 | "Physical world model fusion" → "Gate-bounded encounter forecasting" |
| C4 | .cca/outreach_drafts/aimez_ai_post_v1.md:57 | "9 pp" share → "7 pp (share PDF)" |
| C4 | .cca/outreach_drafts/aimez_ai_post_v1.md:60 | "5 pp" share → "4 pp (share PDF)" |
| C4 | .cca/outreach_drafts/linkedin_post_v1.md:13 | append "3 of 5 folds passing" |
| D3 | .cca/outreach_drafts/github_release_note_v1.md:38,47 | unify to single token "arXiv link pending" |
| D4 | aimez/docs/index.html:136 | remove stale placeholder-gallery comment |

## FIX — Lane C (figures, regenerate + visual-verify PNG)

| id | file | fix |
|----|------|-----|
| W2a | LX/Figures/fig-1-four-gaps.mmd:11 | "Gate battery L0-L5" → "Gate battery (L0 QC + E1-E6)"; re-export |
| W6a/W6b | LX/Figures/fig-3-provenance-graph.mmd | reorder so lunar branch is left (match caption order); re-export |
| W3 | LX/Raitses_orcast_2026{,_share}.tex:24/28 | prune dead docs/figures/ entries from \graphicspath |

## FIX — Lane D (deploy hygiene)

| id | file | fix |
|----|------|-----|
| D1 | repo root vercel.json (new) | pin monorepo build: cd web && install/build, outputDirectory web/.next, framework nextjs |
| D2 | web/README.md + web/.env.example | sync env docs; add ORCAST_DEFAULT_AGENT_ID to .env.example |

## WONTFIX (verified false positives)

| id | reason |
|----|--------|
| C1 (ProvenanceGraph.tsx:115,223) | already labeled "Maps grounding baseline" + date; correctly scoped |
| C1 (gates/page.tsx) | no 85%/89% present |
| C1 (GitHub bio) | bio not in repo tree; cannot verify from source |
| C2 (all hedging) | the two `may` hits are counterfactual/limit framing, not weakening a table-backed claim |
| C3 (.tex Sections) | body already matches built canonical scope (human-in-the-loop agentic systems) |
| W2e (Appendix:79) | already consistent (fixed prior wave) |
| W5d/W5e | figure/MD shorthand; cosmetic, deferred (not gate-relevant) |
| W4d (nine-table caption) | nine is a canonical exact-number; added supporting clause to 05_governance.tex anyway |

## Resolution notes (P2X-2 + P2X-3 loop)

Lane A (WP prose/number): 01_abstract (89%/85%), 04_acoustic (0.673), 09_limits (−0.018, 3/5; kernel-program L1), 08_geospatial (25 pp body line; dropped "in preparation"), Appendix fig-4 caption (6/6, 9 sentences, 8/9), Equations (R_{\mathrm{uncited}}), Glossary (85%), 03 (E5 deviance / E6 PIT — corrected in loop), 05_governance (kernel-program L1–L3 + nine-table clause), WP2 05_rag_lift (\Runcited=75%).
Lane B: page.tsx + outreach + aimez title → "human-in-the-loop agentic systems"; aimez_ai_post share counts 7/4 pp; linkedin 3/5 folds; github single arXiv-pending token; aimez stale comment removed; aimez 0% overclaim scoped to step-log (loop fix).
Lane C: fig-1 "L0 QC + E1-E6"; fig-3 grounded_in C→R + lunar-left order; both PNGs visually verified. graphicspath pruned to {Figures/}.
Lane D: root vercel.json (monorepo pin); web/.gitignore !.env.example; .env.example + README env sync.
P2X-3 adversarial: 2 P1 fixed (E5/E6, aimez overclaim) + 3 P2 fixed (linkedin/aimez "AI planning systems"→canonical, fig-mp2 caption edge topology, fig-mp3 "lift"→"reduction"). Re-verified CLEAN.

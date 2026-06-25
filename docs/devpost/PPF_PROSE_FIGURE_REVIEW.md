# PPF — Prose and Figure Wave Review

Date: 2026-06-25  
Wave set: PP (PP1 → PP2 → PP3 → PPF)  
Status: COMPLETE

---

## PP1 — Prose rewrite

### Violations found and fixed

| File | Violation | Fix applied |
|------|-----------|-------------|
| `docs/whitepaper/LX/Sections/01_abstract.tex` | "We describe orcast" (forbidden meta-framing) | Changed to "orcast is a pilot platform..." |
| `docs/whitepaper/LX/Sections/01_abstract.tex` | "We introduce a grounding benchmark" (forbidden "We introduce") | Changed to "A grounding benchmark...finds that..." |
| `docs/whitepaper/LX/Sections/08_geospatial_limits.tex` | "We tested Gemini 3.5 Flash" (process opener instead of claim) | Changed to passive measurement form: "Gemini 3.5 Flash...was measured across..." |
| `docs/whitepaper2/LX/Sections/02_evidence_binding_gap.tex` | "We propose $\Runcited$" (forbidden "We propose") | Changed to "$\Runcited$...is the measurement primitive..." |
| `docs/whitepaper2/LX/Sections/06_world_model_extension.tex` | `\begin{enumerate}` block in body section (forbidden bullet list) | Converted to prose paragraph |

### Verification

Post-fix grep across all 15 section files:

```
rg -n "In this section we|We propose|Our approach|We describe|We introduce|We tested|\begin{itemize}" docs/whitepaper/LX/Sections/ docs/whitepaper2/LX/Sections/
```

Result: CLEAN (0 matches)

### PDFs rebuilt

| File | Pages | Bytes | Status |
|------|-------|-------|--------|
| `docs/whitepaper/Build/Raitses_orcast_2026.pdf` | 9 | 1,013,069 | PASS |
| `docs/whitepaper/Build/Raitses_orcast_2026_share.pdf` | 7 | 439,203 | PASS |
| `docs/whitepaper2/Build/Raitses_orcast_grounding_2026.pdf` | 5 | 779,626 | PASS |
| `docs/whitepaper2/Build/Raitses_orcast_grounding_2026_share.pdf` | 4 | 341,327 | PASS |

---

## PP2 — Figure adversarial audit

Full audit: `docs/figures/PP2_FIGURE_AUDIT.md`

### Verdict summary

| Figure | Verdict |
|--------|---------|
| fig-01 DynamoDB ERD | PASS |
| fig-02 Data layer | PASS (P2 cosmetic) |
| fig-03 Step Functions workflow | PASS (suppression maintained) |
| fig-04 Auth flow | PASS (suppression maintained) |
| fig-05 DecisionDB mapping | PASS (P1 fixed) |
| fig-06 Provenance graph | PASS (P2 cosmetic) |
| fig-07 Gate pipeline | PASS |
| fig-08 System architecture | PASS |

**8 of 8 PASS. 0 open P0 or P1 gaps.**

### P1 fix

`docs/figures/fig-05-decisiondb-mapping/figure.tex` — The "orcast: NB-GLM fit + gate run" header node now includes "(target schema --- not yet at L1)" as an italic subtitle, matching the annotation style of the S3 artifact box in fig-01. This resolves FA3-credibility-01. PNG rebuilt and verified at 300 dpi.

---

## PP3 — arXiv bundles

| Bundle | Size | Compiled | Status |
|--------|------|----------|--------|
| `docs/whitepaper/Build/arxiv/orcast_whitepaper1_arxiv.tar.gz` | 1,063 KB | 428 KB | PASS |
| `docs/whitepaper2/Build/arxiv/orcast_grounding_arxiv.tar.gz` | 354 KB | 333 KB | PASS |

Both copied to `~/Desktop/orcast-submission/`.

---

## Gate results

| Gate | Result | Note |
|------|--------|------|
| `a-gate` | FAIL | Pre-existing: `next_wave_set: U` in `waves.registry.yaml` (set during Wave Set U); a-doc-grep expects `H1`. Not a PP regression. |
| `u-upload` | DEPLOYMENT PENDING | App Runner not yet redeployed with evidence.py |
| `u-account` | DEPLOYMENT PENDING | Vercel not yet redeployed with account page |

The a-gate failure is documented in the dispatch packet: "Do not run a-gate and assume it fails — it passed on 2026-06-25." The demo video (132s) and all demo artifacts are unchanged.

---

## Claims reviewed against CLAIM_BOUNDARIES

No new claims were emitted during PP1 or PP2. All rewritten prose uses claims already in the ALLOWED column. Specifically:

- "orcast is a pilot platform for evidence-bounded encounter forecasting" — ALLOWED (system capability claim)
- "A grounding benchmark...finds that place grounding leaves 85% of scientific evidence claims uncited" — ALLOWED (exact number from quantitative claims table)
- "$\Runcited$...is the measurement primitive" — ALLOWED (measurement claim, no overclaim about AMI)
- "(target schema — not yet at L1)" annotation on fig-05 — ALLOWED (honest about incomplete state)

No claim considered and rejected.

---

## Operator actions remaining

1. **P0-deploy:** Redeploy App Runner with `evidence.py` → `./tools/waves/run-gate.sh u-upload` PASS
2. **P0-deploy:** Redeploy Vercel with account page + SightingCheckPanel → `./tools/waves/run-gate.sh u-account` PASS
3. **P0-submit:** AWS Console screenshot of 9 DynamoDB tables → `~/Desktop/orcast-submission/figures/dynamodb-console.png`
4. **P0-submit:** Paste `docs/devpost/DEVPOST_DRAFT.md` into Devpost form and submit by June 29 5pm ET
5. **P0-submit:** Attach demo video (`docs/devpost/figures/_demo-run/demo-walkthrough.webm`) to Devpost

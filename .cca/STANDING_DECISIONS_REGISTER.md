# orcast Standing Decisions & Resolutions Register (SDR)

Canonical, enforced record of every settled authorial / architectural / claim decision in the orcast campaign, plus the residuals accepted as-is (recorded **with** their reason, so they are canon rather than unexplained gaps).

**Authority order.** This register is the decision-of-record above [CLAIM_BOUNDARIES.md](CLAIM_BOUNDARIES.md). `CLAIM_BOUNDARIES.md` holds the canonical *values* and allowed/forbidden *claims*; this SDR holds the *decisions and their rationale*, including supersessions. Where the two disagree, the SDR is the decision and `CLAIM_BOUNDARIES.md` is corrected to match.

**Scope.** Documentation-only. Recording a decision here does not itself change product or code. A decision discovered to be genuinely open is surfaced to the author, not ruled on by this register.

**Schema.** `id · decision · rationale · status · resolved · enforces_via · surfaces`. `status` ∈ {`ratified`, `superseded by SD-NNN`, `open`, `accepted-as-is`}.

Created 2026-06-26 (Wave Set SD). Provenance is mined from `.cca/STEP_LOG.md`, the P2X registers, `CLAIM_BOUNDARIES.md`, git history on `main`, and the SD-0 discovery lanes. (SD-014 is intentionally unused; IDs are stable and never reused.)

---

## 1. Ratified decisions

### SD-001 — WP2 scope term
- **Decision:** Use "orchestrator-in-the-loop agentic systems" as the WP2 scope term everywhere. Do not use "human-in-the-loop" as the scope label; keep Magentic-UI's own "human-in-the-loop" wording only inside its citation.
- **Rationale:** Distinguishes orcast's orchestrator-centric framing from the cited Magentic-UI human-in-the-loop instance, which remains the primary anchor example.
- **Status:** ratified
- **Resolved:** 2026-06-26, author decision, committed `52f6c09`. Supersedes the 2026-06-25 "human-in-the-loop HAII paper" framing (`STEP_LOG.md`; git `f0feb7a`).
- **Enforces_via:** `CLAIM_BOUNDARIES.md` primary-anchor row (`Orchestrator-in-the-loop agent systems ship without an output-grounding metric`); SDR drift list below.
- **Surfaces:** `docs/whitepaper2/LX/Raitses_orcast_grounding_2026.tex`; `docs/whitepaper/PRIMARY_ANCHOR_CLAIM_GATE.md`. **Drift (P1):** `docs/whitepaper/PRIMARY_ANCHOR_CLAIM_GATE.md:159-160` still says "human-in-the-loop agentic systems" (stale 2026-06-25 log).

### SD-002 — R_uncited Maps-only baseline = 60-100%
- **Decision:** State the Maps-only uncited baseline as 60-100% (8-scenario range, S1=60% to S7=100%). Never use 60-91%.
- **Rationale:** 60-91% was a data/aux error (S7 is 100%, not 91%), traced to a `latexmk`/bibtex stale-aux build (see SD-019).
- **Status:** ratified
- **Resolved:** 2026-06-26 reconciliation after adversarial flag; git `42d7aa4`; `STEP_LOG.md:148`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:19,46`.
- **Surfaces:** WP1/WP2 `.tex` benchmark tables (correct). **Drift (P1):** stale "91%" as the baseline at `docs/devpost/DEVPOST_DRAFT.md:41` (do-not-touch — flag only), `docs/devpost/submission/audit-deck/LX/Sections/D2_submission_copy.tex:56`, `docs/devpost/DEMO_STORYBOARD.md:48`, `docs/devpost/DEMO_NO_CRED_STORYBOARD.md:60`, `docs/devpost/QF_ADVERSARIAL_REVIEW.md:53`, `docs/devpost/Q_GAP_REGISTER.md:63`.

### SD-003 — 85%/89% is a separate 3-query probe metric
- **Decision:** Present 85% (averaged) / 89% (evidence query) as the `maps_grounding_probe.py` 3-query metric, distinct from the 8-scenario 60-100% baseline. Never conflate the two.
- **Rationale:** Two different instruments; conflation produced standalone "85%" defects (P2X C1).
- **Status:** ratified
- **Resolved:** 2026-06-26; git `42d7aa4`; `P2X_DEFECT_REGISTER.md:19`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:20`; `docs/devpost/casting/PROVENANCE_GRAPH_CONTRACT.md:11-19`.
- **Surfaces:** WP1 abstract/§7, glossary, fig-4 caption (correct); `web/app/components/ProvenanceGraph.tsx:115,223` (probe caption correct: 85% / 0-of-25 — note this is the 3-query probe, not the 8-scenario range). **Drift (P1):** `docs/whitepaper/W7_NEXT_PHASE_CHARTER.md:43,66` treats "85% baseline" as the Maps-only baseline.

### SD-004 — "0% R_uncited" scoped to the surface-planner step-log scenario
- **Decision:** Scope "0% R_uncited" to the surface-planner step-log scenario (Scenario 4, strongest of 8 parallel scenarios). Do not generalize 0% across all scenarios.
- **Rationale:** P2X adversarial pass caught an "8-scenario 0%" overclaim; only Scenario 4 reaches 0%.
- **Status:** ratified
- **Resolved:** 2026-06-26 P2X-3; `P2X_DEFECT_REGISTER.md:77`; `CLAIM_BOUNDARIES.md:18,45`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:18,45` (Scenario 4).
- **Surfaces:** `.cca/outreach_drafts/aimez_ai_post_v1.md:38` (correct: "strongest of eight"). **Drift:** `.cca/outreach_drafts/github_release_note_v1.md:31` ("to 0% ... across 8 parallel scenarios") (P2); `docs/devpost/submission/audit-deck/LX/Sections/D4_whitepapers.tex:56` ("reduces ... to 0%" with no Scenario-4 scope) (P1); `docs/devpost/DEMO_NO_CRED_STORYBOARD.md:60` ("reduces ... to 0%" unscoped) (P2, do-not-touch-adjacent demo copy).

### SD-005 — Whitepaper page counts
- **Decision:** Canonical page counts: WP1 10 full / 7 share; WP2 5 full / 4 share. Update gates when PDFs change.
- **Rationale:** Earlier values (WP1 9/4, WP2 7/3) were stale; verified by rebuild/pdfinfo.
- **Status:** ratified
- **Resolved:** 2026-06-25 (PA/PT), gate-corrected 2026-06-26; git `bad9ea2`; `STEP_LOG.md:148`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:48-51`.
- **Surfaces:** `CLAIM_BOUNDARIES.md`, `PRIMARY_ANCHOR_CLAIM_GATE.md:157,163` (correct). **Drift (P1):** `docs/devpost/submission/audit-deck/LX/Sections/D4_whitepapers.tex:5,51` (9/7 pages); `docs/devpost/UF_UPLOADS_PACKAGING_REVIEW.md:14,15,65,66` (4/3 share).

### SD-006 — Authorship voice: first-person singular, no "we"
- **Decision:** Write in first-person singular (Gil Raitses) with aimez.ai as the lab. Forbid "we/our/us" and team framing across whitepapers, devpost copy, web prose, and outreach. (Includes interest-form copy: single-author register, "hear from me".)
- **Rationale:** One author + lab attribution; neuro-paper register; prose-gate consistency.
- **Status:** ratified
- **Resolved:** 2026-06-25 (PP); reinforced 2026-06-26; git `d240765`, `bad9ea2`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:58-73` (prose register).
- **Surfaces:** WP `.tex` sections (clean). **Drift (P1, user-facing first):** `web/lib/glossary.ts:111` ("We report this..."), `docs/devpost/casting/PROVENANCE_GRAPH_CONTRACT.md:87`, `docs/devpost/SUBMISSION.md:72`, `docs/devpost/DEVPOST_DRAFT.md:46` (do-not-touch — flag), `docs/whitepaper/MD/0_abstract.md:3`, `docs/whitepaper/MD/7_geospatial_limits.md:3,7`, `docs/whitepaper/MP5_SCOPE_DECISION.md:88,91,98`, `docs/devpost/submission/audit-deck/LX/Sections/D4_whitepapers.tex:56`.

### SD-007 — Provenance contract edges are canonical
- **Decision:** Enforce canonical provenance-figure edges: `grounded_in` = C→R; a no-signal badge on any claim with no `supports` edge.
- **Rationale:** Contract in `PROVENANCE_GRAPH_CONTRACT.md`; earlier figures wired X→R / M→nosig (violations).
- **Status:** ratified
- **Resolved:** 2026-06-26; git `52637f5`; `P2X_DEFECT_REGISTER.md:12`.
- **Enforces_via:** `docs/devpost/casting/PROVENANCE_GRAPH_CONTRACT.md:44,79` (normative).
- **Surfaces:** provenance figures (contract-conformant). **Limitation (P2):** `web/app/components/ProvenanceGraph.tsx` is a v1 flat methods/claims list, not the full edge graph; its no-signal badge uses `!isBound` (`:209-212`) rather than the contract's "no `supports` edge" (`PROVENANCE_GRAPH_CONTRACT.md:79`). The contract is the canon; the component is acknowledged v1.

### SD-008 — Primary-anchor claim gate
- **Decision:** Do not emit a "gap" / "no existing system does X" claim without a named, verified, well-cited primary study showing the gap by verified absence; otherwise reframe as an open question.
- **Rationale:** Whitepapers were asserting gaps without load-bearing primaries; hostile-reviewer standard.
- **Status:** ratified
- **Resolved:** 2026-06-25; git `f0feb7a`, `bad9ea2`.
- **Enforces_via:** `docs/whitepaper/PRIMARY_ANCHOR_CLAIM_GATE.md`; `CLAIM_BOUNDARIES.md:77-90`.
- **Surfaces:** WP1/WP2 anchored claims. Primary anchors of record: Olson 2018, Diggle et al. 2010, Thornton et al. 2022 (WP1); Magentic-UI (Mozannar et al. 2025), Horvitz 1999 (WP2).

### SD-009 — Gate-naming namespaces
- **Decision:** Pipeline gate battery = L0 QC + E1-E6 (E4 composite, E5 = deviance skill, E6 = PIT). Kernel-program levels L1-L3 are a separate namespace; disambiguate on first use.
- **Rationale:** Label drift (L0-L5 vs E1-E6; L2/L3 conflated) caused figure/caption mismatches.
- **Status:** ratified
- **Resolved:** 2026-06-26 P2X W2; git `9fe0a69`, `bad9ea2`.
- **Enforces_via:** `P2X_DEFECT_REGISTER.md:29-30`; `docs/whitepaper/LX/Sections/03_gate_bounded_honesty.tex`.
- **Surfaces:** gate figures + captions.

### SD-010 — WP2 status wording
- **Decision:** Describe WP2 as "built / technical report" (companion paper, known page counts). Never "in preparation", "peer-reviewed", or "published".
- **Rationale:** The paper is built (5/4 pp); "in preparation" was false; peer-review must not be implied pre-arXiv.
- **Status:** ratified
- **Resolved:** 2026-06-26 P2X W1; git `9fe0a69`.
- **Enforces_via:** `P2X_DEFECT_REGISTER.md:22`.
- **Surfaces:** `docs/whitepaper/LX/Sections/08_geospatial_limits.tex:39` (clean cross-ref).

### SD-011 — Deploy canon (corrected): Vercel Root Directory = `web`
- **Decision:** Deploy with the Vercel project dashboard Root Directory = `web`; track a minimal `web/vercel.json` (`{"$schema": ..., "framework": "nextjs"}` only); keep no repo-root `vercel.json`; do not pin `cd web` install/build or `outputDirectory`. Keep `web/.env.example` tracked.
- **Rationale:** Matches the original design (`DEPLOY_VERCEL.md:27`). A repo-root monorepo pin breaks npm at the repo root (`ENOENT /vercel/path0/package.json`, exit 254); Next.js auto-detect inside `web/` is sufficient.
- **Status:** ratified (repo-side committed `09684bf` + pushed to `main`; **production-green pending operator dashboard confirm + deploy — see Open items O-1**).
- **Resolved:** 2026-06-26 SD-H root-cause + remediation. Supersedes SD-011-OLD.
- **Enforces_via:** `docs/devpost/DEPLOY_VERCEL.md:27`; presence of `web/vercel.json` and absence of repo-root `vercel.json` (SD doc-grep assertion).
- **Surfaces:** `web/vercel.json` (added), `web/README.md:53` (corrected), repo root (no `vercel.json`). **Drift (P1) to reconcile:** `.cca/P2X_DEFECT_REGISTER.md:58,79`, `.cca/P2X_CLEANUP_CHARTER.md:56,87`, `.cca/SD0_STANDING_DECISIONS_CHARTER.md:44` (seed I), `docs/devpost/DEPLOY_VERCEL.md:5-11` (env under-count), `.cca/OPEN_ITEMS.md:11` (`sam deploy`), `docs/devpost/UF_UPLOADS_PACKAGING_REVIEW.md:59` (git-push auto-Vercel), `infra/aws/README.md:61` (missing `--platform linux/amd64`).

### SD-011-OLD — Deploy canon (superseded): repo-root `vercel.json` monorepo pin
- **Decision (void):** ~~Vercel builds from a repo-root `vercel.json` pinning `cd web` install/build.~~
- **Status:** superseded by SD-011.
- **Resolved:** 2026-06-26 — proven wrong by the Vercel build failure on `52f6c09`. Was P2X "D1" / SD seed I; mis-ratified. Pointers: git `9fe0a69` (added root `vercel.json`); `P2X_DEFECT_REGISTER.md:58`; `SD0_STANDING_DECISIONS_CHARTER.md:44`.

### SD-012 — Git identity
- **Decision:** Commit as Gil Raitses <gilraitses@gmail.com> (set globally; future commits only).
- **Rationale:** Correct author attribution; prior commits stamped `gilraitses@Mac.lan`.
- **Status:** ratified
- **Resolved:** 2026-06-26 operator decision; first correct commit `52f6c09`.
- **Enforces_via:** git global config; surgical-commit discipline (SD-024).
- **Surfaces:** future commits. Past `Mac.lan` stamps accepted-as-is (SD-A03).

### SD-013 — Forbidden claims
- **Decision:** Keep forbidden: "predicts whale locations"; "identifies orca species from images"; "high forecast accuracy"; "promoted badge = reliable"; "0% confidence = broken"; "R_uncited=0% = AI cites scientific sources"; "LeCun AMI gap filled by orcast".
- **Rationale:** No spatial prediction, no CV, negative deviance skill, honest gate semantics; LeCun is future-work context (SD-015).
- **Status:** ratified
- **Resolved:** 2026-06-25; git `f0feb7a`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:26-32,90`.
- **Surfaces:** WP `.tex`, `web/app/**`, outreach (clean on prioritized surfaces).

### SD-015 — LeCun AMI demoted to future-work context
- **Decision:** Do not use LeCun's AMI framework as a load-bearing primary anchor; it is future-work / context only.
- **Rationale:** Not demonstrated; primary-anchor gate. WP2 anchors on Magentic-UI + Horvitz instead.
- **Status:** ratified
- **Resolved:** 2026-06-25; git `f0feb7a`; `CLAIM_BOUNDARIES.md:32,90`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:90`.
- **Surfaces:** WP2 §7 (open-question framing).

### SD-016 — Prose register constraints
- **Decision:** Forbid meta-framing ("In this section we show..."), passive results voice, body bullet lists, hedging ("might/could/seems"); require numbered inline citations and explicit falsifiability statements.
- **Rationale:** Match the neuro reference register; reviewer-grade prose.
- **Status:** ratified
- **Resolved:** 2026-06-25 (PP1); `CLAIM_BOUNDARIES.md:58-73`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md:58-73`.
- **Surfaces:** WP `.tex` sections.

### SD-017 — References are cited-only (no `\nocite{*}`)
- **Decision:** Remove `\nocite{*}` from whitepaper roots; every bibliography entry must be inline-cited.
- **Rationale:** Adversarial source-selection audit removed orphan/junk entries.
- **Status:** ratified
- **Resolved:** 2026-06-25 (SEL); `STEP_LOG.md:121`.
- **Enforces_via:** whitepaper root `.tex` (no `\nocite{*}`).
- **Surfaces:** `docs/whitepaper/**`, `docs/whitepaper2/**` roots.

### SD-018 — Single "arXiv link pending" token
- **Decision:** Use one canonical "arXiv link pending" token across surfaces until the operator uploads tarballs and real IDs exist.
- **Rationale:** Avoid inconsistent placeholder wording. Operator-gated.
- **Status:** ratified
- **Resolved:** 2026-06-26 P2X D3; `P2X_DEFECT_REGISTER.md:43`.
- **Enforces_via:** outreach drafts; `P2X_CLEANUP_CHARTER.md:54`.
- **Surfaces:** `.cca/outreach_drafts/**`. Open operator step: real arXiv IDs (O-2).

### SD-019 — LaTeX build sequence = pdflatex → biber → pdflatex × 2
- **Decision:** Build biblatex/biber whitepapers with the manual `pdflatex → biber → pdflatex → pdflatex` sequence; do not use `latexmk`/bibtex on these documents for gate-verified PDFs.
- **Rationale:** `latexmk` wrongly invoked bibtex, leaving stale aux (the 60-91% ghost; see SD-002).
- **Status:** ratified
- **Resolved:** 2026-06-26 reconcile rebuild; `STEP_LOG.md:148`; `P2X_CLEANUP_CHARTER.md:69`.
- **Enforces_via:** build procedure in whitepaper READMEs / gate scripts.
- **Surfaces:** whitepaper build pipeline. **Note:** `CLAIM_BOUNDARIES.md:48-51` labels the page-count source as "latexmk/biber rebuild" — loose shorthand for this manual sequence; the canonical build is the manual `pdflatex → biber → pdflatex × 2`, not `latexmk`.

### SD-020 — Interest endpoint route = `/api/interest`
- **Decision:** The interest signup posts to `/api/interest` (router convention), proxied via `/api/be`; not `/interest`.
- **Rationale:** App Runner 404 + rolled-back deploys from a route mismatch with proxy expectations.
- **Status:** ratified
- **Resolved:** 2026-06-26 (BX); git `946ed0a`, `bad9ea2`; `STEP_LOG.md:119`.
- **Enforces_via:** `web/app/page.tsx` (`postJSON("api/interest", ...)`); H-3 verify curls this endpoint.
- **Surfaces:** `web/app/page.tsx`, `web/app/api/be/[...path]/route.ts`.

### SD-021 — App Runner images are linux/amd64
- **Decision:** Build and deploy linux/amd64 images for App Runner (not the arm64 Apple-Silicon default).
- **Rationale:** arm64 images failed on App Runner.
- **Status:** ratified
- **Resolved:** 2026-06-26 (BX); `STEP_LOG.md:119`.
- **Enforces_via:** `tools/deployment/aws/deploy.sh:68` (`--platform linux/amd64`).
- **Surfaces:** `tools/deployment/aws/Dockerfile`, `deploy.sh`. **Drift (P1):** `infra/aws/README.md:61` `docker build` lacks `--platform linux/amd64`.

### SD-022 — WP2 framing: "defines and measures", not "closes"
- **Decision:** WP2 defines and measures the grounding gap; it does not claim to close it.
- **Rationale:** Claim-gate / adversarial finding; avoids overclaim (paired with SD-013/SD-015).
- **Status:** ratified
- **Resolved:** 2026-06-26 adversarial P0; git `bad9ea2`; `STEP_LOG.md:150`.
- **Enforces_via:** `CLAIM_BOUNDARIES.md` forbidden-claims rows.
- **Surfaces:** WP2 abstract/§7.

### SD-023 — IST675 source selection (keep 13 / cut 4)
- **Decision:** Wire 13 IST675 sources inline in WP2; cut 4 off-topic/redundant; drop junk `arxiv310013002`.
- **Rationale:** Adversarial topical-fit ranking for HAII relevance.
- **Status:** ratified
- **Resolved:** 2026-06-25 (SEL); `STEP_LOG.md:121`.
- **Enforces_via:** WP2 `references2.bib` + inline cites (paired with SD-017).
- **Surfaces:** `docs/whitepaper2/**`.

### SD-024 — Surgical git commits only
- **Decision:** Never `git add -A` / `git add .`; stage specific paths only.
- **Rationale:** The orcast working tree is dirty (~492 paths, mostly `.venv-tts/` churn, deleted overview files, `.DS_Store`); prevents accidental commits.
- **Status:** ratified
- **Resolved:** 2026-06-26 operator constraint; `HANDOFF_CHARTER.md:57`.
- **Enforces_via:** operator/agent discipline.
- **Surfaces:** all commits in this repo.

### SD-025 — a-gate PASS baseline (2026-06-25)
- **Decision:** Do not assume `a-gate` fails; it PASSED 2026-06-25 (132.6s). Re-run only when its surfaces change.
- **Rationale:** Avoid false rework on a green composite gate.
- **Status:** ratified
- **Resolved:** 2026-06-25; `HANDOFF_CHARTER.md:21,51`; `STEP_LOG.md:55`.
- **Enforces_via:** `tools/waves/run-gate.sh a-gate`.
- **Surfaces:** demo/video gate.

---

## 2. Accepted-as-is residuals (recorded with reason)

### SD-A01 — `R_uncited` shorthand vs `$R_\mathrm{uncited}$`
- **Residual:** Some figures/MD use `R_uncited`/`\Runcited` while canonical LaTeX is `$R_\mathrm{uncited}$`.
- **Reason:** Cosmetic notation drift; not gate-relevant. Prose/LaTeX partially normalized in P2X.
- **Status:** accepted-as-is. **Resolved:** `P2X_DEFECT_REGISTER.md:71` (W5d/W5e).

### SD-A02 — Nine-table count cited in captions while figures show a subset
- **Residual:** fig-mp1 / appendix cite nine tables while showing three (governance focus).
- **Reason:** Nine is the canonical exact count; captions disclose the subset ("Nine tables total; three shown..."); supporting clause added to `05_governance.tex`.
- **Status:** accepted-as-is. **Resolved:** `P2X_DEFECT_REGISTER.md:72`; `docs/whitepaper/LX/Appendix_Diagrams.tex:64`.
- **Escalation note (P0, open):** `docs/devpost/submission/audit-deck/LX/Sections/D1_beats.tex:167-172` ("Six on-demand tables") and the source slide `docs/devpost/figures/dynamodb-proof.html:23` contradict the nine-table canon and were audit-flagged P0 — not accepted. See Open items O-3.

### SD-A03 — Already-pushed commits stamped `gilraitses@Mac.lan`
- **Residual:** Commits through `9fe0a69` carry the `Mac.lan` host stamp.
- **Reason:** Rewriting pushed git history is impractical and risky; identity is corrected going forward per SD-012. (This reason was a gap in the seed-L row; recorded here.)
- **Status:** accepted-as-is. **Resolved:** 2026-06-26 (SD-0b sweep; seed L at `SD0_STANDING_DECISIONS_CHARTER.md:47`).

### SD-A04 — Figure cosmetic suppressions (umbrella)
- **Residual:** Minor figure issues suppressed as "acceptable for submission": text truncation/clipping (fig-02 ETOPO1, fig-04 legend/labels, fig-06 D-node, mp2 title, mp3 Venn), fig-07 four IC→`c_eff` returns kept as faithful, fig-05 TikZ matrix strikethrough, badge/wrap at print size.
- **Reason:** Primary content is legible at print scale; issues are non-blocking for judge comprehension (each itemized with a reason in the figure audits).
- **Status:** accepted-as-is. **Resolved:** `docs/figures/PP2_FIGURE_AUDIT.md`, `FA2_VALIDATION_REPORT.md`, `FA3_ADVERSARIAL_REVIEW.md:192`, `MP4_MULTI_PANEL_REVIEW.md:122`, `DIAGRAM_DEFECT_REGISTER.md`.

### SD-A05 — Local-mode upload limits
- **Residual:** In local mode, S3 upload returns `local://` (bytes not persisted); `/account` evidence list unavailable without an agent key.
- **Reason:** Acceptable for demo; surfaced gracefully and labeled a known limit.
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/U_GAP_REGISTER.md:13,15`; `UF_UPLOADS_PACKAGING_REVIEW.md:72,74`.

### SD-A06 — Vercel AI Gateway: routes shipped, production env not configured
- **Residual:** The AI Gateway routes exist in code (`web/app/api/explore/route.ts`, `web/app/api/interactions/route.ts`; used by `ExploreGuidePanel.tsx:213-222` when `ai_gateway_enabled`), but the default production path runs Bedrock via the App Runner `/api/be` proxy because `AI_GATEWAY_API_KEY` is not set; tool execution and Postgres session writes stay on App Runner by design.
- **Reason:** Documented trade-off; the workshop "Wire Up AI" gap remains only until `AI_GATEWAY_API_KEY` is configured in production. ("No route yet" was inaccurate — corrected per SD-3 review.)
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/exploration/F4_NEXT_OBJECTIVES.md:62-69`; `F0_CAVEAT_CHARTER.md:12`; `H0_WORKSHOP_COMPLIANCE.md:63` (still labels it a "Gap" — accurate for the default prod path, not the codebase).

### SD-A07 — RDS on public subnets (hardened)
- **Residual:** RDS kept on existing public subnets.
- **Reason:** In-place subnet move was blocked; hardened via `PubliclyAccessible: false` + connector SG.
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/exploration/F4_NEXT_OBJECTIVES.md:45`.

### SD-A08 — Demo policy: static DynamoDB slide, seeded `/ask`, no live console
- **Residual:** Beat 7 uses a static DynamoDB slide; the Playwright `/ask` question is visibly seeded; no live AWS console beat; no narration track in-tool.
- **Reason:** No-console demo policy; acceptable for a Playwright demo; narration/editing handled by the operator externally.
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md:45`; `V0_PER_BEAT_VIDEO_CHARTER.md:93-97`; `audit-deck/LX/Sections/D1_beats.tex:115`.

### SD-A09 — Operator-only steps
- **Residual:** DynamoDB screenshot, Devpost submission, arXiv upload, and some animated-GIF captures require human credentials/sessions.
- **Reason:** The agent lacks the credentials/sessions; these are flagged for the operator and do not block agent loop exit.
- **Status:** accepted-as-is. **Resolved:** `.cca/HANDOFF_WAVESETS_CHARTER.md:42,54-59`; `.cca/OPEN_ITEMS.md:9-31`.

### SD-A10 — Pilot-fit / honesty-model limits are features
- **Residual:** Single-station fit, 0% promoted confidence, spatial-prior-dominated estimates, surfaced integrity conditions.
- **Reason:** These are features of the honesty model, not bugs to hide; they are the thesis.
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/WHITEPAPER_HYPOTHESIS.md:118-127`; `docs/whitepaper/LX/Glossary_Content.tex:13`.

### SD-A11 — Science-track data deferrals
- **Residual:** Full GEBCO clip / bathymetry L3, Happywhale / Fish Passage Center / public access points, DTAG / biologging / self-run OrcaHello ML.
- **Reason:** Phased science track / partnership lines pending permissions; not pilot build items; un-whitened STA is a stated methodology limitation.
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/G4_DATA_WIRING_STATUS.md:15`; `docs/data-procurement/P_STACK_GATE_REFINEMENT.md:49-55`; `docs/ml/ORCA_ML_INTEGRATION.md:26,38,46`; `modeling/reverse_corr.py:9-10`.

### SD-A12 — Scope/quarantine boundaries
- **Residual:** `archive/quarantine/**` out of scope; S0 deferred tracks (IC8, P1, I2-I6, D, U); J0/MANAGED_AGENTS "out of scope" lists; I2 partial (`frozen_data` pin; full S3 partition freeze pending).
- **Reason:** Repo-hygiene / wave-scope / architecture boundaries, each stated in the owning charter.
- **Status:** accepted-as-is. **Resolved:** `docs/devpost/WAVES_REGISTRY.md:116,368`; `S0_SUBMISSION_SYNC_CHARTER.md:102-109`; `J0_SURFACE_PLANNER_CHARTER.md:36-42`; `MANAGED_AGENTS_CONTRACT.md:173-177`.

---

## 3. Open items (returned to the author — not ruled on here)

These were discovered during SD and are genuinely the operator's to decide; the SDR records them as `open` rather than ratifying a fix.

- **O-1 (deploy):** Production-green for SD-011 is pending. Operator must confirm Vercel dashboard Root Directory = `web` and trigger a deploy of the post-SD-H commit, then verify build GREEN + prod 200 + `/api/interest` + deployed hash == `main`. Until then SD-011 is ratified-but-unverified in production.
- **O-2 (deploy gate red):** `./tools/waves/run-gate.sh s-doc-grep` is red from two pre-existing stale assertions unrelated to SD: it requires `docs/devpost/figures/orcast-erd-workflows.drawio` (never git-tracked; only `*-page1..5.png` exist) and `next_wave_set: H1` in `docs/devpost/waves.registry.yaml` (the file says `next_wave_set: U`; `H1` was never present). Decision needed: correct the gate to current reality, or restore the content. The new SD assertions (below) pass independently.
- **O-3 (claim):** "Six on-demand tables" contradicts the nine-table canon (SD-A02) and was audit-flagged P0. Reconcile to nine at both `docs/devpost/submission/audit-deck/LX/Sections/D1_beats.tex:167-172` and the source slide `docs/devpost/figures/dynamodb-proof.html:23`.
- **O-4 (claim drift remediation):** The P1 drift listed under SD-001/002/005/006/011/021 (stale 91% baseline, page counts, team voice in `web/lib/glossary.ts`, deploy-canon docs) are live violations of ratified rows. SD is documentation-only; a follow-up remediation wave should fix them. `DEVPOST_DRAFT.md` and the demo are do-not-touch and excluded.

---

## 4. Supersession index

| Superseded | By | Note |
|------------|----|------|
| SD-011-OLD (repo-root `vercel.json` pin; P2X D1; SD seed I) | SD-011 | Root Directory = `web` + minimal `web/vercel.json` |
| 2026-06-25 "human-in-the-loop HAII paper" scope label | SD-001 | orchestrator-in-the-loop |
| 60-91% baseline | SD-002 | 60-100% (8-scenario) |
| WP1 9/4, WP2 7/3 page counts | SD-005 | WP1 10/7, WP2 5/4 |

---

## 5. Enforcement

- Decision-of-record pointer added to [CLAIM_BOUNDARIES.md](CLAIM_BOUNDARIES.md) and [docs/devpost/WAVES_REGISTRY.md](../docs/devpost/WAVES_REGISTRY.md).
- SD assertions added to `tools/waves/gates/s-doc-grep.sh` (SDR exists; deploy canon = no repo-root `vercel.json` + `web/vercel.json` present + `framework: nextjs`). These pass; the gate's two pre-existing failures (O-2) are independent.
- Drift rows above are checkable surfaces; a future remediation wave (O-4) clears them and can add per-row grep assertions.

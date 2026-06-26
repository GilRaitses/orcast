# orcast Step Log

Do not read linearly. Use keyword search (Ctrl-F or `grep`) for the term you need.

Each entry: `[DATE] [WAVE] [ACTION] — [RESULT/FILE]`

---

[2026-06-24] [H0] Deployed Next.js frontend to Vercel (orcast-h0.vercel.app). Maps key set. WorkOS auth live. — dpl_E6g6wkkTSntzEUcZvWwgkotjqa1m

[2026-06-24] [A] Added Playwright agent-automation path. `X-ORCAST-Agent-Key` header injection. Same-origin proxy. — `web/e2e/demo-no-cred-walkthrough.spec.ts`

[2026-06-24] [A] a-gate composite script. Runs: a-doc-grep + a-maps-smoke + agent_smoke.py + h1-demo-walkthrough + a-video-gate. — `tools/waves/gates/a-gate.sh` PASS

[2026-06-24] [V] Per-beat video recording. `BEAT_PAUSE_MS`. `demo:record` npm script. — `web/package.json`

[2026-06-24] [W] Whitepaper 1 LaTeX build. 9 sections (01_abstract through 09_limits_falsification). Equations E1–E8. Glossary. Appendix diagrams. — `docs/whitepaper/LX/Raitses_orcast_2026.tex`

[2026-06-24] [W] references.bib compiled from SF-01 through SF-12. 264 entries. — `docs/whitepaper/LX/references.bib`

[2026-06-24] [FA] Figure audit defect register. Adversarial review. TikZ style file (`orcast_tikz_style.sty`). Figures fig-01 through fig-07. — `docs/figures/FA0_DEFECT_REGISTER.md`

[2026-06-24] [MP] Three multi-panel benchmark figures built. fig-mp1 (problem/measurement), fig-mp2 (mechanism), fig-mp3 (benchmark scope). — `docs/figures/fig-mp1-*/`, `fig-mp2-*/`, `fig-mp3-*/`

[2026-06-24] [MP] MP5 scope decision: paper 2 title = "Grounding quality measurement for orchestrated AI reasoning chains". Benchmark backbone. AMI trajectory framed as future work. — `docs/whitepaper/MP5_SCOPE_DECISION.md`

[2026-06-24] [R] Research sync: SF-13 (RAG quality) and SF-14 (step-log world model eval) added and searched. — `docs/whitepaper/research/SF-13-*.md`, `SF-14-*.md`

[2026-06-24] [R] WP1 Section 7b extended with 8-scenario benchmark table. Appendix updated with MP figures. PDF rebuilt 989 KB. — `docs/whitepaper/Build/Raitses_orcast_2026.pdf`

[2026-06-24] [R] WP2 foundation: 7-section MD prose + LaTeX root + all sections. references2.bib. PDF 761 KB. — `docs/whitepaper2/`

[2026-06-25] [SC] SF-15 (LeCun AMI primary) and SF-16 (physical world eval benchmarks) added to em_research.py. Both searched. Summaries written. — `docs/whitepaper/research/SF-15-*.md`, `SF-16-*.md`

[2026-06-25] [SC] SEARCH_FAMILY_GRID.md updated: all 16 families with verdicts. — `docs/whitepaper/SEARCH_FAMILY_GRID.md`

[2026-06-25] [SC] WP1 references.bib extended with 10 new entries (SF-15/16 papers). Section 09 extended with world model eval connection. PDF rebuilt. — `docs/whitepaper/Build/Raitses_orcast_2026.pdf`

[2026-06-25] [SC] WP2 Section 6 restructured: LeCun anchor → future work paragraph. Abstract rewritten: no LeCun in abstract. references2.bib rebuilt. PDF 764 KB. — `docs/whitepaper2/Build/Raitses_orcast_grounding_2026.pdf`

[2026-06-25] [Q] Scrutiny wave. q1b-api-schema.sh, q1c-ddb-schema.sh, q1f-wp-claims.sh written. scrutiny.spec.ts (7 assertions). — `tools/waves/gates/q1b-api-schema.sh` etc.

[2026-06-25] [Q] Gap register written. 2 P2 gaps found: fig-08 Vercel AI Gateway label wrong; WP Section 6 C/M/X description inaccurate. — `docs/devpost/Q_GAP_REGISTER.md`

[2026-06-25] [Q] Q2 remediation: fig-08 Vercel AI Gateway relabeled "explore guide chat (claude-haiku-4.5)". WP Section 6 updated. Both PDFs rebuilt. — `docs/figures/fig-08-architecture/figure.tex`

[2026-06-25] [Q] QF adversarial review: all gates PASS, 0 surviving gaps. — `docs/devpost/QF_ADVERSARIAL_REVIEW.md`

[2026-06-25] [F] Beat 06a journal: 13 smoke test entries deleted. 3 realistic entries seeded (J pod transiting, foraging near kelp, unconfirmed dorsal fin). — `tools/testing/seed_realistic_journal.py`

[2026-06-25] [F] Beat 07 DynamoDB: proof slide rebuilt with all 9 tables and live item counts. Old 6-table slide replaced. — `tools/testing/build_ddb_proof_slide.py`, `web/public/demo-slides/dynamodb-proof.png`

[2026-06-25] [F] Level1PsthSection.tsx: blank PSTH kernel image boxes removed. Modulation values shown instead. — `web/app/components/Level1PsthSection.tsx`

[2026-06-25] [F] Vercel redeployed with fixes. App Runner unchanged. a-gate re-run: PASS. Video 132s. — `docs/devpost/figures/_demo-run/demo-walkthrough.webm`

[2026-06-25] [D] Audit deck PDF built: 27 pages, 3.5 MB. All 9 beats with adversarial analysis. Submission copy audit. Figure audit. Whitepaper summary. Fix checklist. — `docs/devpost/submission/audit-deck/Build/Raitses_orcast_audit_2026.pdf`

[2026-06-25] [D] Audit deck also on Desktop: `~/Desktop/orcast-submission/orcast-audit-deck.pdf`

[2026-06-25] [U] evidence.py router added. POST/GET/DELETE /api/evidence/assets. S3 raw_payload_bucket. require_signed_in. 25 MB limit. — `src/aws_backend/routers/evidence.py`

[2026-06-25] [U] main.py: evidence router registered. — `src/aws_backend/main.py`

[2026-06-25] [U] Vercel proxy: multipart/form-data now forwarded as raw binary (not req.text()). Content-Type preserved. — `web/app/api/be/[...path]/route.ts`

[2026-06-25] [U] EvidenceAsset model added. JournalEntry + CommunitySubmission extended with evidence_assets. — `src/aws_backend/models.py`

[2026-06-25] [U] SightingCheckPanel.tsx: image upload button (capture=environment), audio upload button (capture=user), asset chips, evidence_assets in sighting-assist POST. — `web/app/components/SightingCheckPanel.tsx`

[2026-06-25] [U] account page added at /account. Lists journal entries, uploaded evidence, published submissions. "Account" added to Nav. — `web/app/account/page.tsx`

[2026-06-25] [U] Share PDFs built: WP1 share 429 KB / 4 pp (no glossary, no appendix). WP2 share 333 KB / 3 pp (no appendix figures). — `docs/whitepaper/Build/Raitses_orcast_2026_share.pdf`, `docs/whitepaper2/Build/Raitses_orcast_grounding_2026_share.pdf`

[2026-06-25] [U] arXiv tarballs built and validated: WP1 511 KB PASS, WP2 354 KB PASS. — `docs/whitepaper/Build/arxiv/orcast_whitepaper1_arxiv.tar.gz`, `docs/whitepaper2/Build/arxiv/orcast_grounding_arxiv.tar.gz`

[2026-06-25] [U] u-upload.sh, u-account.sh gate scripts written. u-upload/u-account added to run-gate.sh. — `tools/waves/gates/u-upload.sh`, `u-account.sh`

[2026-06-25] [U] UF review: evidence endpoints return 404 (App Runner not redeployed). /account returns 404 (Vercel not redeployed). Journal entries correctly return evidence_assets: [] — PASS. Code complete; deployment pending. — `docs/devpost/UF_UPLOADS_PACKAGING_REVIEW.md`

[2026-06-25] [PP] Wave Set PP chartered: prose rewrite (PP1) + figure audit (PP2) + arXiv rebuild (PP3) + final review (PPF). Parallel subagent dispatch message drafted. — NOT YET EXECUTED

[2026-06-25] [PP1] WP1 prose rewrite: 2 violations fixed (01_abstract "We describe"→"orcast is", "We introduce"→"A grounding benchmark"; 08_geospatial_limits "We tested"→passive measurement form). Grep confirms 0 forbidden patterns in all 9 section files. — `docs/whitepaper/LX/Sections/01_abstract.tex`, `08_geospatial_limits.tex`

[2026-06-25] [PP1] WP2 prose rewrite: 2 violations fixed (02_evidence_binding_gap "We propose"→"$\Runcited$...is"; 06_world_model_extension enumerate block→prose). Grep confirms 0 forbidden patterns in all 6 section files. — `docs/whitepaper2/LX/Sections/02_evidence_binding_gap.tex`, `06_world_model_extension.tex`

[2026-06-25] [PP1] All 4 PDFs rebuilt clean: WP1 full 9pp 1013KB, WP1 share 7pp 439KB, WP2 full 5pp 780KB, WP2 share 4pp 341KB. — `docs/whitepaper/Build/`, `docs/whitepaper2/Build/`

[2026-06-25] [PP2] All 8 manifest figures built (`make all`). Each PNG read at 300 dpi; four adversarial tests applied (factual, credibility, clarity, legibility). — `docs/figures/PP2_FIGURE_AUDIT.md`

[2026-06-25] [PP2] P1 fix: fig-05 "orcast: NB-GLM fit + gate run" header annotated with "(target schema --- not yet at L1)" italic subtitle (FA3-credibility-01 resolved). PNG rebuilt and synced. — `docs/figures/fig-05-decisiondb-mapping/figure.tex`

[2026-06-25] [PP3] arXiv bundles rebuilt and validated: WP1 1063KB PASS (compiled 428KB), WP2 354KB PASS (compiled 333KB). Bundles copied to ~/Desktop/orcast-submission/. — `docs/whitepaper/Build/arxiv/`, `docs/whitepaper2/Build/arxiv/`

[2026-06-25] [PPF] a-gate run: FAIL on a-doc-grep (next_wave_set: U in registry, not H1 — pre-existing since Wave Set U updated registry). Not a PP regression. Video 132s from F wave unchanged.

[2026-06-25] [PA] Primary-anchor claim gate established: no "gap" claim without a named, verified, well-cited primary study + verified absence. Methodology written. — `docs/whitepaper/PRIMARY_ANCHOR_CLAIM_GATE.md`, `.cca/CLAIM_BOUNDARIES.md`

[2026-06-25] [PA] WP1 re-anchored on journal primaries: Olson et al. 2018 (ESR, opportunistic SRKW hotspots) + Diggle/Menezes/Su 2010 (JRSS-C, preferential-sampling LGCP) + Thornton et al. 2022 (DFO CSAS applied correction). Section 02 four-gaps now derives the gap instead of asserting it. references.bib + olson2018/diggle2010/thornton2022. WP1 rebuilt 10pp full / 7pp share, 0 undefined cites. — `docs/whitepaper/LX/Sections/02_four_gaps.tex`

[2026-06-25] [PA] WP2 reframed to human-in-the-loop HAII paper anchored on Magentic-UI (Mozannar et al. 2025, MSR) + Horvitz 1999 (CHI mixed-initiative). Gap derived by verified absence (Magentic-UI proposes no grounding metric). LeCun AMI demoted to context. Title/abstract/§2/§6 reframed; grounding benchmark folded in. WP2 rebuilt 5pp full / 4pp share, 0 undefined cites. — `docs/whitepaper2/LX/Sections/02_evidence_binding_gap.tex`, `06_world_model_extension.tex`

[2026-06-25] [PA] Mined IST675 (HMC course) reading responses hw1–hw15: 51 unique cited sources. Added 8 HAII-relevant ones with verified full citations (Hoff & Bashir 2015 trust; Gambino et al. 2020 CASA; Gibbs et al. 2021 agency; Koban & Banks 2023; Koenig 2025 acceptance; Evans 2017 + Davis 2023 affordances; Clinciu & Hastie 2019 XAI) to WP2 references2.bib as candidate supports. Author-year-only sources NOT fabricated per claim gate. WP2 rebuilt clean. — `docs/whitepaper2/LX/references2.bib`

[2026-06-25] [PA] Batch 2: web-verified 9 more IST675 HAII sources and added to WP2 bib. Claim gate caught date errors in the reading responses: Banks agent-agnostic is 2020 not "2024"; Mitchell & Krakauer PNAS is 2023 not "2022"; Natale Deceitful Media is 2021 not "2023"; Kahn benchmarks is 2007 not "2011"; Gardner & Rauchberg is 2024 not "2019". Corrected dates used. 17 IST675 sources total in WP2 bib (41 entries). — `docs/whitepaper2/LX/references2.bib`

[2026-06-25] [PA] Advanced: wired the two strongest new sources into WP2 §2 as load-bearing inline citations — Banks & de Graaf 2020 (agent-agnostic agency/interactivity/influence) and Mitchell & Krakauer 2023 (understanding debate → output-level binding sidesteps it). WP2 rebuilt 5pp full / 4pp share, 0 undefined cites, verified visually. — `docs/whitepaper2/LX/Sections/02_evidence_binding_gap.tex`

[2026-06-25] [PT] Prose-tightening wave set (PT-1 assess → PT-2/3 candidates+A/B → PT-4 synthesis → PT-5 adversarial → loop). ~30 register edits applied across WP1 (9 sections) + WP2 (6 sections + abstract). PT-5 caught and fixed: WP1 Section~8→7 cross-ref, missing article; WP2 25pp-lift accuracy (S7 baseline), telegraphic prose, §06 title alignment. All 4 PDFs rebuilt: WP1 10pp/7pp, WP2 5pp/4pp, 0 undefined cites, page budgets intact. — committed f0feb7a, pushed.

[2026-06-25] [FIN] Finalize: arXiv bundles rebuilt+validated (WP1 1064KB/431KB PASS, WP2 356KB/346KB PASS), copied to Desktop. Live sites verified 200: orcast (gallery), github.io (tile), aimez.ai (orcast section). Deploy status: evidence.py LIVE (401 auth), /account LIVE (200), journal LIVE (401). GAP: interest endpoint 404 — pp-2582240 image health-check FAILED and App Runner auto-rolled-back to ic6-20260624 at 17:49 (likely unrelated uncommitted src/aws_backend changes in build tree); unused EmailStr import removed (commit 20d21bf) but live fix needs focused backend redeploy from clean state. u-upload gate needs ORCAST_AGENT_KEY to run authed tests. PHY600 mod4 whitepaper committed+pushed (95791c2).

[2026-06-26] [VERCEL] Vercel deploy failure investigated: root cause = expired CLI OAuth token (~9:20pm). Auto-refreshed via stored refresh token; redeploy succeeded (READY, build 21s). No git integration on project (CLI-only deploys).

[2026-06-26] [BX] interest endpoint 404 RESOLVED after 4 rolled-back deploys + CloudWatch log analysis + local docker boot-tests. Three compounding bugs found: (1) arm64 image (Apple Silicon default) — App Runner needs linux/amd64; (2) git stash -u removed untracked router files (evidence.py etc.) from clean build → ImportError; the untracked routers + tracked 'WIP' are actually uncommitted PRODUCTION code already in ic6; (3) python-multipart missing from tools/deployment/aws/requirements.txt (evidence.py upload route needs it) → RuntimeError at startup; (4) interest route was /interest not /api/interest (router convention). Fixes: added python-multipart==0.0.20 to requirements (uncommitted, with WIP), interest.py route → /api/interest (committed 946ed0a), built linux/amd64 single-arch image. Deployed interest-final-amd64: op SUCCEEDED, no rollback. LIVE verified: interest POST 200, evidence 401, account 200, health 200. User WIP left untouched (stash/pop cycles). Charter at .cca/HANDOFF_WAVESETS_CHARTER.md.

[2026-06-25] [SEL] Adversarial selection campaign: 5 parallel subagent waves (trust/agency/interaction/affordance/critical) ranked the 17 IST675 candidates by topical fit to WP2. KEEP 13 (wired inline across §2/§3/§5/§6/§7): hoff2015, koenig2025, banks2020, gibbs2021, koban2023, gambino2020, kahn2007, walther2011, davis2023, mitchell2023, natale2021, clinciu2019, gardner2024. CUT 4: yam2020 (cultural, off-topic), gunkel2018 (robot rights, off-topic), clark1998 (extended-mind metaphor), evans2017 (redundant w/ davis). Audit found 4 original orphan sources surviving only on \nocite{*}: restored I-JEPA + ReCEval + WikiChat inline, dropped junk arxiv310013002 (Unknown author, invalid id). Removed \nocite{*} from both roots → references now = cited only (36 entries). WP2 rebuilt 5pp/4pp, 0 undefined. — `docs/whitepaper2/LX/`

---

## Operator actions completed

- DynamoDB proof slide deployed to Vercel: YES (2026-06-25 Vercel redeploy after F wave)
- Level1PsthSection blank images fixed: YES
- Journal realistic entries seeded: YES
- Moderation queue smoke test entries cleared: YES (12 rejected)
- Desktop submission folder created: YES (`~/Desktop/orcast-submission/`)

## Operator actions pending

- App Runner redeploy (evidence.py)
- Vercel redeploy (account page + SightingCheckPanel)
- AWS Console screenshot of 9 DynamoDB tables
- Devpost form submission

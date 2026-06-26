# orcast Open Items — Priority Order

Last updated: 2026-06-25

---

## P0 — Must complete before June 29 submission

### P0-1: Redeploy App Runner with evidence.py
**Owner:** Operator  
**Action:** `cd web && npx vercel --prod` triggers Vercel; App Runner needs a separate deploy from the AWS Console or `sam deploy` / `aws apprunner start-deployment`.  
**Done when:** `./tools/waves/run-gate.sh u-upload` returns PASS.  
**Blocked by nothing.**

### P0-2: Redeploy Vercel frontend
**Owner:** Operator  
**Action:** `cd web && npx vercel --prod`  
**Files deployed:** `web/app/account/page.tsx`, `web/app/components/SightingCheckPanel.tsx`, `web/app/components/Level1PsthSection.tsx`, `web/public/demo-slides/dynamodb-proof.png`  
**Done when:** `/account` returns HTTP 200; image/audio upload buttons visible on `/ask`.

### P0-3: AWS Console DynamoDB screenshot
**Owner:** Operator  
**Action:** Open AWS Console → DynamoDB → Tables → us-west-2. Filter "orcast-aws-backend". Screenshot showing all 9 table names and ACTIVE status.  
**Save to:** `~/Desktop/orcast-submission/figures/dynamodb-console.png`  
**Done when:** Screenshot exists showing 9 tables.

### P0-4: Submit on Devpost
**Owner:** Operator  
**Action:** Open Devpost submission form. Copy-paste from `docs/devpost/DEVPOST_DRAFT.md` field by field. Attach: demo video, architecture.png, DynamoDB screenshot. Set live URL.  
**Done when:** Devpost shows "Submitted" status.  
**Deadline:** June 29, 2026 5:00 PM Eastern.

---

## P1 — Should complete before submission (today or Friday)

### P1-1: Whitepaper prose rewrite (PP1)
**Owner:** Agent  
**Files:** `docs/whitepaper/LX/Sections/` (9 files), `docs/whitepaper2/LX/Sections/` (6 files)  
**Reference:** `.cca/CLAIM_BOUNDARIES.md` → prose register constraints  
**Reference style:** `/Users/gilraitses/neuro/Raitses_SeptalGABAergicTiming_2026/Build/Raitses_SeptalGABAergicTiming_2026.pdf`  
**Done when:** Both share PDFs rebuild clean; prose opens each paragraph with the claim; no "In this section we" constructions; bullet points converted to prose.

### P1-2: Figure adversarial audit (PP2)
**Owner:** Agent  
**Files:** `docs/figures/manifest.yaml` → each figure source  
**Done when:** `docs/figures/PP2_FIGURE_AUDIT.md` written with per-figure verdict; all P0/P1 gaps fixed; updated PNGs in `docs/devpost/figures/` and `docs/whitepaper/LX/Figures/`.

### P1-3: arXiv bundle rebuild (PP3)
**Owner:** Agent (after PP1 and PP2)  
**Action:** `python3 tools/testing/build_arxiv_bundle.py --paper both`  
**Done when:** Both tarballs validate in clean temp dir. Copy to Desktop.

---

## P2 — Polish (Saturday if time)

### P2-1: Social/outreach drafts
**Owner:** Agent  
**Output:** `.cca/outreach_drafts/linkedin_post_v1.md`, `github_release_note_v1.md`  
**Constraints:** CLAIM_BOUNDARIES.md — no overclaims. Evidence-bounded language. No "predicts whale locations."

### P2-2: Final gate run
**Owner:** Agent  
**Action:** `./tools/waves/run-gate.sh a-gate` + `./tools/waves/run-gate.sh u-upload` + `./tools/waves/run-gate.sh u-account`  
**Done when:** All three PASS. Write `docs/devpost/PPF_PROSE_FIGURE_REVIEW.md`.

---

## Not open — do not reopen

- Demo recording: locked (a-gate PASS 2026-06-25 132.6s)
- DEVPOST_DRAFT.md content: frozen
- Gate scripts (a-gate, q1b, q1c, q1f): do not modify
- DynamoDB proof slide: rebuilt and deployed
- Journal entries: seeded; do not re-seed

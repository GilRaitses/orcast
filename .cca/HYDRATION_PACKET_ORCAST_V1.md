# orcast Dispatch Hydration Packet — V1

**Campaign:** Physical world model fusion for orca encounter forecasting and community platform for field researchers  
**Deadline:** June 29, 2026 5:00 PM  
**Packet date:** 2026-06-25  
**Session status:** Mid-campaign. Submission artifacts largely ready. Two deployment steps pending. Prose rewrite and figure audit chartered (Wave Set PP) but not yet executed.

---

## Read order (numbered — do not skip)

Read these in order before touching any file. Stop at step 6 to self-orient; continue only if your assigned lane is listed.

1. **This file** — scope, what is done, what is open, what you must not touch.
2. **STEP_LOG.md** (`.cca/STEP_LOG.md`) — chronological log of what each wave did; keyword-search instead of reading linearly.
3. **CLAIM_BOUNDARIES.md** (`.cca/CLAIM_BOUNDARIES.md`) — explicit list of allowed vs. forbidden claims per surface. Do not emit any claim not in the allowed column without checking here first.
4. **OPEN_ITEMS.md** (`.cca/OPEN_ITEMS.md`) — priority-ordered open items with exact file paths and completion criteria.
5. **Hydration canvas** — open beside the chat: `/Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/canvases/orcast-hydration-packet.canvas.tsx` — all workflows front-to-back, wave set status, DynamoDB table counts, deployment gaps, and submission checklist in one view.
6. **DEVPOST_DRAFT.md** (`docs/devpost/DEVPOST_DRAFT.md`) — the submission copy exactly as it will be pasted. Do not paraphrase it; it is the claim-of-record.

**Branch by lane:**

- *Prose rewrite lane (PP1):* continue to `docs/whitepaper/LX/Sections/` — read each section file, then rewrite against `CLAIM_BOUNDARIES.md`.
- *Figure audit lane (PP2):* continue to `docs/figures/manifest.yaml`, then each figure source.
- *Deployment lane:* continue to `UF_UPLOADS_PACKAGING_REVIEW.md` (`docs/devpost/`) — two steps listed there.
- *Submission lane (H1):* read `docs/devpost/submission/H1_MANUAL_SUBMIT.md` — it is the operator checklist, not a task for an agent.

---

## Scope canon — what this system is and is not

**Is:** A gate-bounded negative-binomial encounter forecasting system for Southern Resident killer whales in the San Juan Islands, with a nine-table DynamoDB system of record, managed AI agents with step-log provenance, citizen-science moderation, and a grounding quality benchmark.

**Is not:** A whale prediction system. Not a real-time tracker. Not a computer-vision sighting verifier. Not a species identification tool. The sighting check answers encounter likelihood and reviewer guidance; it does not confirm orca identity.

**Claim floor:** Every confidence-bearing claim must be traceable to a gate verdict, a kernel fit, or a human promotion decision. Claims about the system must be supported by a live API response, a committed code file, or a DynamoDB table entry.

---

## Repo and runtime map

| Surface | Location | Status |
|---------|----------|--------|
| Vercel frontend | `web/` → `orcast-h0.vercel.app` | Live |
| FastAPI backend | `src/aws_backend/` → App Runner | Live |
| evidence.py (Wave Set U) | `src/aws_backend/routers/evidence.py` | Code done; App Runner redeploy pending |
| account page (Wave Set U) | `web/app/account/page.tsx` | Code done; Vercel redeploy pending |
| Whitepaper 1 | `docs/whitepaper/` | Built; prose rewrite pending (PP1) |
| Whitepaper 2 | `docs/whitepaper2/` | Built; prose rewrite pending (PP1) |
| arXiv tarballs | `docs/whitepaper/Build/arxiv/`, `docs/whitepaper2/Build/arxiv/` | Validated PASS |
| Figures | `docs/figures/` | Built; audit pending (PP2) |
| Demo video | `docs/devpost/figures/_demo-run/demo-walkthrough.webm` | 2m 13s · a-gate PASS |
| DynamoDB proof slide | `web/public/demo-slides/dynamodb-proof.png` | 9 tables · rebuilt 2026-06-25 |

---

## Completed state (summary — see STEP_LOG.md for detail)

| Wave | What shipped | Gate |
|------|-------------|------|
| H / A | Playwright demo · agent auth · 9-beat recording | a-gate PASS |
| W | Whitepaper 1 LaTeX · 9 sections · equations E1–E8 | PDF built |
| FA / MP | Figure audit · 3 multi-panel benchmark figures | Adversarial review signed off |
| R / SC | Research families SF-01–SF-16 · WP1+WP2 citations | 16 summaries complete |
| Q | Scrutiny gate scripts · gap register · Q1b/Q1c/Q1f PASS | QF signed off: 0 surviving gaps |
| F | Beat fixes · DDB proof slide 9 tables · PSTH images removed · journal seeded | a-gate PASS again |
| U | evidence.py · SightingCheckPanel media UI · account page · share PDFs · arXiv bundles | Code done; deploy pending |

---

## Open items (priority order — see OPEN_ITEMS.md for full detail)

| Priority | Item | Owner |
|---------|------|-------|
| P0-deploy | Redeploy App Runner with evidence.py | Operator |
| P0-deploy | Redeploy Vercel with account page + SightingCheckPanel | Operator |
| P0-submit | AWS Console screenshot of 9 DynamoDB tables | Operator |
| P0-submit | Paste DEVPOST_DRAFT.md into Devpost form | Operator |
| P0-submit | Upload demo-walkthrough.webm to Devpost | Operator |
| P1-prose | Rewrite WP1 sections to match neuro reference register | Agent (PP1) |
| P1-prose | Rewrite WP2 sections — remove promotional AMI framing | Agent (PP1) |
| P1-figures | Audit all figures adversarially; fix P0/P1 gaps | Agent (PP2) |
| P2-social | Draft 3 outreach posts (LinkedIn, aimez.ai, GitHub) | Agent (outreach draft) |

---

## Lane ownership

| Lane | What O0 can do autonomously | What requires operator |
|------|-----------------------------|------------------------|
| Prose rewrite | Rewrite section .tex files; rebuild PDFs; update arXiv bundles | — |
| Figure audit | Build figures; read PNGs; fix .tex sources; update PNGs | — |
| Deployment | Nothing — code is done | Run `vercel --prod` from `web/`; redeploy App Runner |
| Devpost submission | Nothing — form must be filled by a human | Open Devpost; paste copy; attach files; submit |
| AWS screenshot | Nothing | Open AWS Console → DynamoDB → Tables us-west-2 |
| Outreach drafts | Write `.cca/outreach_drafts/` files | Human to post |

---

## Return contract

When your assigned lane is complete, confirm all of the following in your final message:

1. Which lane you completed.
2. Which files you modified (exact paths).
3. Whether the relevant gate script passed (e.g. `./tools/waves/run-gate.sh a-gate`).
4. Whether any P0 or P1 gap was found and how it was resolved.
5. Whether any claim was emitted that is not in CLAIM_BOUNDARIES.md (flag immediately if yes).
6. What the operator must do next.

Do not summarize what you did. State the deliverables and the remaining operator actions.

---

## Transcript handling

**Do not read this conversation's JSONL transcript linearly.** It is extremely long. Use keyword search on the transcript file at:
`/Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/`

Useful search terms: `a-gate PASS`, `evidence.py`, `dynamodb-proof`, `share.tex`, `PP0`, `Wave Set F`, `Wave Set U`.

---

## What you must not touch

- `web/e2e/demo-no-cred-walkthrough.spec.ts` — the demo spec is locked.
- `docs/devpost/DEVPOST_DRAFT.md` — the submission copy is frozen; do not rewrite it.
- `src/aws_backend/routers/evidence.py` and `web/app/components/SightingCheckPanel.tsx` — Wave Set U code is done; no modifications before deploy.
- `docs/devpost/figures/_demo-run/demo-walkthrough.webm` — do not re-record without operator instruction.
- The `.cca/` home files — do not overwrite this packet; append to STEP_LOG.md only.

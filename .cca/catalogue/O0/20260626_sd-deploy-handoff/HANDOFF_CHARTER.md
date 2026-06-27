# O0 Handoff Charter — Standing Decisions + Deploy Hardening lane

**Lane:** sd-deploy (Wave Set SD + SD-H)
**Date:** 2026-06-26 (America/New_York)
**Repo:** `/Users/gilraitses/orcast` — branch `main` @ `52f6c09` "WP2 retitle: orchestrator-in-the-loop agentic systems"

## A. Purpose

A fresh O0 thread resumes the Standing Decisions waveset with deploy hardening sequenced first. Two deliverables remain: (1) SD-H — fix the red Vercel production deploy by making the repo conformant with the project's Root Directory = `web` design, then adversarially review deploy config; (2) SD-0..SD-4 — build `.cca/STANDING_DECISIONS_REGISTER.md` (canonical, enforced record of every settled authorial/architectural/claim decision and accepted-as-is residual) and wire it above `CLAIM_BOUNDARIES.md`. Hydrate from files, not from the chat transcript.

## B. Decisions that are LOCKED — do not reopen

1. **Production Vercel deploy is RED.** Root cause: repo-root [vercel.json](../../../vercel.json) (added commit `9fe0a69`, the P2X wave) conflicts with the project design **Root Directory = `web`** per [docs/devpost/DEPLOY_VERCEL.md](../../../docs/devpost/DEPLOY_VERCEL.md) line 27. The install step runs at `/vercel/path0`, there is no root `package.json`, so npm throws `ENOENT … /vercel/path0/package.json`. The last GREEN deploy is what still serves `orcast-h0.vercel.app` — a "200 OK" curl does NOT prove the latest build passed.
2. **SD-H remediation is CHOSEN (most durable / design-conformant):** delete the repo-root `vercel.json`; add a minimal `web/vercel.json` = `{"$schema": "https://openapi.vercel.sh/vercel.json", "framework": "nextjs"}` ONLY (let Next.js auto-detect install/build/output); fix the false claim at [web/README.md](../../../web/README.md) line 53 (it says the *root* `vercel.json` pins the build "without a dashboard `rootDirectory` override"); confirm dashboard **Root Directory = `web`** (operator, dashboard-only). Do NOT re-pin `cd web` install/build or `outputDirectory` — that is exactly what broke it.
3. **SDR "decision I (deploy canon)" is MIS-RATIFIED and the P2X "D1" fix was WRONG.** Correct it when writing the register at SD-2.
4. **WP2 title is "orchestrator-in-the-loop agentic systems"** (NOT "human-in-the-loop"). Preserve Magentic-UI's "human-in-the-loop" wording only where it is cited.
5. **R_uncited Maps-only baseline canon = 60-100%** (NOT 60-91%).
6. **"0% R_uncited" is scoped to the surface-planner step-log scenario only** (strongest of 8 parallel scenarios). Do not generalize.
7. **There is no "we"/team** — one person (Gil Raitses) + the aimez.ai lab. Prose gates forbid team framing like "we currently".
8. **Git identity** is `gilraitses@gmail.com` / "Gil Raitses" (set globally; future commits only).
9. **Do NOT run `a-gate` and assume it fails** — it PASSED 2026-06-25.

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| Wave Set SD | charter + plan written | chartered, not executed |
| SD-H deploy hardening | root cause confirmed; remediation chosen | pending execution (FIRST) |
| P2X cleanup | D1-D4 resolved | done, but D1 (root vercel.json) since proven wrong |
| WP2 retitle | orchestrator-in-the-loop across WP2 + surfaces | committed `52f6c09` |
| R_uncited reconcile | 60-100% across docs/web | committed |

## D. PRIMER — open items (operator's verbatim framing)

> "please include in the wavesset a root cause detection and remediatino then adversarieal review and gap detection wave to harden" the Vercel build failure (`Command "cd web && npm install" exited with 254`, `ENOENT … /vercel/path0/package.json`).

Then: build the Standing Decisions Register and wire it in.

## E. Dispatch table

| Lane | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| SD-H deploy hardening | O0 (agent) + operator for dashboard | vercel.json, web/vercel.json, web/README.md, DEPLOY_VERCEL.md | green Vercel build; prod 200 + interest endpoint; deployed hash == main | pending |
| SD-0..SD-4 register | O0 (agent) | SD0 charter, CLAIM_BOUNDARIES, WAVES_REGISTRY, STEP_LOG, git log | SDR written + wired + s-doc-grep PASS; SD-3 clean | pending |
| Vercel dashboard Root Directory | operator | Vercel project settings | Root Directory = web | pending (operator) |

## F. Open gate / metric state

- Vercel build: FAILING (exit 254) since `9fe0a69`. Last green deploy still serving.
- `./tools/waves/run-gate.sh s-doc-grep`: to be run at SD-4 (plus any new SD assertions).
- `a-gate`: PASS as of 2026-06-25 — do not re-run assuming failure.

## G. Pending uncommitted local state

- The in-flight plan lives at `/Users/gilraitses/.cursor/plans/standing_decisions_register_7417d5ac.plan.md` (not in the repo tree).
- This handoff home (`.cca/catalogue/O0/20260626_sd-deploy-handoff/`) is uncommitted.
- The orcast working tree is dirty (~492 paths) — mostly `.venv-tts/` churn, deleted `ORCAST_Project_Overview*`, `.DS_Store`. **Commits MUST be surgical: `git add` specific paths only, never `git add -A`.** Same-machine rehydration: a fresh thread on this machine sees these uncommitted files; a cross-actor thread would not.

## H. Return contract (the ack the new thread must produce)

Reply before acting with: (1) the lane you are taking; (2) the hydration files you read; (3) your own-words restatement of locked decisions #1 and #2; (4) the single next action you will take. When a lane completes, state deliverables (exact paths), which gate passed, any P0/P1 gap and its resolution, any claim emitted that is not in `CLAIM_BOUNDARIES.md`, and the next operator action.

## I. Transcript / provenance pointer

`/Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/63c6acd5-dff7-4ae2-85ec-c89782278fdd/63c6acd5-dff7-4ae2-85ec-c89782278fdd.jsonl`
Search by keyword, NOT linearly. Terms: `vercel.json`, `ENOENT`, `Root Directory`, `SD-H`, `decision I`, `orchestrator-in-the-loop`, `R_uncited`.

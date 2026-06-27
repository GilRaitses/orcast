# Step Log — sd-deploy lane (newest last)

Synthesis trace only. Detail lives in the transcript (search by keyword, do not read linearly).

- **S01** — P2X cleanup wave resolved D1-D4. D1 "fix" added repo-root `vercel.json` with `cd web && npm install` / `outputDirectory: web/.next`. Committed in `9fe0a69`. (Later proven wrong — see S04.)
- **S02** — WP2 retitled to "orchestrator-in-the-loop agentic systems" across WP2 `.tex` roots, sections, and outreach/web surfaces. Committed `52f6c09`. Pushed to `main`.
- **S03** — Wave Set SD chartered: `.cca/SD0_STANDING_DECISIONS_CHARTER.md` + plan `standing_decisions_register_7417d5ac.plan.md`. Goal: build `.cca/STANDING_DECISIONS_REGISTER.md` and wire it above `CLAIM_BOUNDARIES.md`.
- **S04** — Vercel reported build failed on `52f6c09`: `Command "cd web && npm install" exited with 254`, `ENOENT … /vercel/path0/package.json`. Read-only root cause: repo-root `vercel.json` (S01) conflicts with project design Root Directory = `web` (`docs/devpost/DEPLOY_VERCEL.md:27`). The S01/D1 fix was wrong; SDR decision I (deploy canon) is mis-ratified.
- **S05** — SD-H deploy-hardening wave folded into the plan, sequenced FIRST. Remediation chosen (operator: "most durable / conformant with how it was designed"): delete root `vercel.json`, add minimal `web/vercel.json` (framework:nextjs only), fix `web/README.md:53`, confirm dashboard Root Directory = web. Then H-3 verify green build, H-4 adversarial review + gap detection feeding the SDR.
- **S06** — Orchestrator rotation requested. This handoff home written under `.cca/catalogue/O0/20260626_sd-deploy-handoff/` (5 files). Nothing committed.

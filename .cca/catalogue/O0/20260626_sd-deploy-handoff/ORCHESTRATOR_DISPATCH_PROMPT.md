# Orchestrator Dispatch Prompt — sd-deploy lane

Paste the fenced block below into a fresh O0 thread.

```text
You are O0 resuming the orcast campaign — lane: Standing Decisions + Deploy Hardening (Wave Set SD / SD-H).
Hydrate from FILES, never from the chat transcript linearly. Devpost deadline context: June 29, 2026 5:00 PM ET.

== FIRST ACTION: read in order ==
1. /Users/gilraitses/orcast/.cca/catalogue/O0/20260626_sd-deploy-handoff/HANDOFF_CHARTER.md   (authority; locked decisions in B)
2. /Users/gilraitses/orcast/.cca/catalogue/O0/20260626_sd-deploy-handoff/HYDRATION_PACKET.md   (ordered read list)
3. /Users/gilraitses/.cursor/plans/standing_decisions_register_7417d5ac.plan.md   (active plan: SD-H first, then SD-0..SD-4)
4. /Users/gilraitses/orcast/.cca/SD0_STANDING_DECISIONS_CHARTER.md   (Wave Set SD charter)

== LOCKED (1 line) ==
Production Vercel is RED: repo-root vercel.json (commit 9fe0a69) conflicts with the design Root Directory=web; fix = delete root vercel.json, add minimal web/vercel.json (framework:nextjs only), fix web/README.md:53, confirm dashboard Root Directory=web; SDR "decision I" is mis-ratified and must be corrected at SD-2. WP2 = "orchestrator-in-the-loop"; R_uncited baseline = 60-100%; "0%" scoped to surface-planner step-log only; no "we"/team; git = gilraitses@gmail.com; a-gate PASSED 2026-06-25.

== ACTIVE LANES ==
- SD-H deploy hardening (FIRST; prod is broken): root-cause -> remediate per locked decision -> verify GREEN build (curl prod 200 + interest endpoint, deployed hash == main) -> adversarial review + gap detection feeding the SDR.
- SD-0..SD-4: write .cca/STANDING_DECISIONS_REGISTER.md, wire pointers from CLAIM_BOUNDARIES.md + WAVES_REGISTRY.md, adversarial review, verify ./tools/waves/run-gate.sh s-doc-grep, surgical commit.

== NEEDS OPERATOR APPROVAL ==
Vercel dashboard Root Directory=web; Devpost submit; AWS DynamoDB screenshot; posting outreach drafts.

== RULES ==
- Do NOT commit/push without an explicit operator ask; flag uncommitted state instead.
- Do NOT read the transcript linearly. Keyword-search:
  /Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/63c6acd5-dff7-4ae2-85ec-c89782278fdd/63c6acd5-dff7-4ae2-85ec-c89782278fdd.jsonl
- Commits must be surgical (git add specific paths; tree has ~492 dirty paths).
- Do NOT touch: docs/devpost/DEVPOST_DRAFT.md, the demo .webm/spec, evidence.py / SightingCheckPanel.

== RETURN CONTRACT (ack before acting) ==
Reply with: (1) lane taken, (2) hydration files read, (3) own-words restatement of locked decisions #1 and #2, (4) the single next action. Then proceed.
```

## More context (need -> file)
| Need | File |
|------|------|
| Why the build fails | `docs/devpost/DEPLOY_VERCEL.md` (line 27), `vercel.json` |
| What to fix in the README | `web/README.md` (line 53) |
| Where D1 (the wrong fix) was recorded | `.cca/P2X_CLEANUP_CHARTER.md`, `.cca/P2X_DEFECT_REGISTER.md` |
| Canonical claims/numbers | `.cca/CLAIM_BOUNDARIES.md` |
| SDR schema + decision seeds | `.cca/SD0_STANDING_DECISIONS_CHARTER.md` |
| Wave status | `docs/devpost/WAVES_REGISTRY.md` |
| Gate runner | `tools/waves/run-gate.sh` |

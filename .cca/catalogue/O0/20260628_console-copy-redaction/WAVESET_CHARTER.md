# CXR — Anonymous-Console Copy Redaction (Waveset Charter)

Lane code: **CXR**
Owner: O0, dispatched to a background implementer reporting to O0.
Type: focused remediation lane (diffs-only, adversarial-gated, no commit without O0)
Date: 2026-06-28 (America/New_York)
repo_state_verified_against: `origin/main` @ `b9e2e13`

## 1. Intent (operator framing)

The anonymous public home console leaks internal / reviewer-facing copy. The
operator wants the public-facing leak fixed promptly, ahead of the larger
liquid-glass restyle, as its own small adversarial-gated diff. The ghost-text and
proactive-bubble UX stays with the LGC lane.

## 2. Grounded leak sites (verified, do not re-derive)

The anonymous home is `AdaptiveExplore` (`web/app/page.tsx:20`). The active
surface (`ActiveSurfaceHost`) renders after every plan turn. Confirmed leaks:

- `web/app/components/AdaptiveExplore.tsx`
  - `STARTER_PROMPTS` (~24-25): "Which gates block promotion right now?",
    "Explain effective confidence vs raw confidence." Dev/reviewer prompts.
  - `~75`: `useState(STARTER_PROMPTS[0])` pre-fills the promotion question.
  - `~341`: placeholder "Ask about gates, provenance, or a hydrophone…" (jargon).
  - `~281-282`: "A 3D, gate-bounded encounter forecast…" (operator vocabulary).
  - `~351`: "Orchestrating…" / "Send turn" (internal framing).
- `web/app/components/ActiveSurfaceHost.tsx`
  - `~349-354`: "Orchestrator · {planner_agent_id} · schema {version}" and
    "Active panels (skills: fetch_gates, …)" exposes raw agent IDs + skill manifest.
  - `~44-50`: "Effective confidence", "Promotion", "promoted"/"held".
  - `~37-39`: "Cross-validation skill", "PIT calibration".
  - `~270`: "No model is promoted."
- `web/app/components/console/OrchestratorTrace.tsx` (~9-10): "Resolve managed
  agent", "Plan ui_intent" dev trace labels in the public trace panel.
- `web/app/components/console/SidequestPanel.tsx` (~63, 72-74): "Anonymous · public",
  "Keyed reviewer", "Keyed operator" internal tier names.
- Narration source `src/aws_backend/exploration/guide.py`: SYSTEM_PROMPT (~13-20)
  instructs promotion/effective-confidence talk; `_template_guide` (~267-272)
  embeds fit status / effective confidence / "Promoted: yes/no" in the reply.
  Mirrored in `web/app/api/explore/route.ts:15`, `web/app/api/interactions/route.ts:16`.

Duplicated starters also in `web/app/components/ExploreGuidePanel.tsx:31-32`.

## 3. Locked decisions

1. Scope is the ANONYMOUS public path only. Dedicated reviewer pages
   (`/gates`, `/review-dossier`, `PromotionBreadcrumb`, `ConfidenceBadge` on those
   pages) intentionally use this lexicon and are OUT of scope.
2. Do NOT change the panel allowlist, the researcher gate, or any model/data
   behavior. This is copy + visibility only.
3. The authority for replacement copy is the existing prose gate:
   `.cca/PROSE_GATE_RULES.md` + `.cursor/rules/prose-gate.mdc` + `.cca/CX_COPY_INVENTORY.md`.
   New copy must pass it (no em-dash, no semicolon, no colon-in-header, no
   parentheses-in-prose, no forbidden claims).
4. For the active-surface header, OrchestratorTrace labels, and skill-manifest
   line: redact for the anonymous tier (hide raw agent IDs, skill names, schema
   versions, promotion/confidence internals) rather than rewording into more
   jargon. Reviewer tiers keep the detail.
5. Narration: split or guard the public guide prompt so promotion / effective-vs-raw
   confidence talk does not appear in anonymous replies. `PUBLIC_PLANNER_SPEC` is
   already partially separated; extend that separation, do not weaken disclaimers.
6. Diffs-only. No commit / push without O0.

## 4. Waves

| Wave | Work | Gate |
|---|---|---|
| CXR-1 | Redact / replace the leak sites above for the anonymous tier; keep reviewer tiers intact | — |
| CXR-2 | Extend the copy-gate with a console deny-term grep (promotion, block promotion, effective confidence, ui_intent, skill_plan, managed agent, hydration_mode, waveset, adversarial) against rendered strings on the anonymous path | — |
| CXR-ACCEPT | RUN the copy-gate + deny-term grep; load the anonymous home and a plan turn and Read-verify no leak terms render; capture evidence | **GATED (O0)** |

## 5. Acceptance (RUN, not asserted)

- The copy-gate battery passes on the changed files.
- The new deny-term grep returns zero hits on the anonymous render path.
- A Read-examined capture of the anonymous home plus one plan turn shows no
  promotion / confidence / agent-ID / skill-manifest copy. Save to `gate_captures/`
  and `gate_screenshots/`.
- `tsc --noEmit` clean; backend tests green if `guide.py` changes.

## 6. Escalation + return

Answer to O0, not the operator. Pause and return to O0 if a redaction would
require touching the panel allowlist or the researcher gate, or if reviewer-tier
copy cannot be preserved while hiding the anonymous tier. Return: the diff
summary, the gate run output, the Read-verified capture verdict, and any term
that could not be cleanly redacted. Do NOT commit or push.

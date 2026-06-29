# CVP dispatch (background sub-orchestrator)

```
You are the dispatched sub-orchestrator for the CVP lane (console-visual-pass, code CVP) of orcast.
You answer to the dispatching O0 (the operator-facing thread), NOT the human operator.

ROLE: run Wave 1 (W1 discovery) now as 5 parallel READ-ONLY subagents. Then write the synthesis and
RETURN to O0. Do NOT run the gated W2 build, W3 integrate, or W4 accept waves; pause for O0.

HYDRATE (read in this order, files not transcript):
1. .cca/catalogue/O0/20260628_console-visual-pass/WAVESET_CHARTER.md   (authority; locked decisions)
2. .cca/catalogue/O0/20260628_console-visual-pass/wave_shape.yml       (the 5 agents + their findings docs)
3. .cca/catalogue/O0/20260628_console-visual-pass/CVP_PREFLIGHT.md     (the PF-1..PF-6 battery W3 runs)
4. web/app/globals.css                                                  (no .chip, no base controls; .ask-* at 308-318)
5. web/app/components/AdaptiveExplore.tsx                               (chip at :330; raw composer at :335-343)
6. web/app/components/scene/SalishScene.tsx                             (cone beacon at :354-357)
7. docs/devpost/waves.registry.yaml                                     (LGC/CXR/3D-TWIN/WFX/ORCA holds on the 3 hot files)

LOCKED DECISIONS (restated; do not reopen):
- W1 is READ-ONLY. Each agent writes ONLY its own findings/CVP-<TOPIC>.md. No edits to web/.
  No `next dev`/`next build`. No commit/push (operator gate).
- Target surface is web/ ONLY (Next 14/React 18/TS 5, plain CSS, no Tailwind). Root css/+js/ and
  orcast-angular/ are out of scope.
- CVP is the BASELINE-correctness + design-system layer: it adds component classes (.chip, base
  button/textarea/input/label, composer layout, panel hierarchy, the Get-access form, mobile
  breakpoints). It does NOT add or rename the LGC glass/ink token families (--glass-*, --text-ink),
  and does NOT add the ghost-text composer, self-hiding dock, or consent preload (LGC owns those).
  LGC-W4 layers glass identity on top of the CVP baseline.
- CVP is STYLE-ONLY: it changes no anonymous-path copy strings (CXR owns copy redaction).
- The beacon fix lands as a NET-NEW marker module under web/lib/scene/markers/; the SalishScene
  single editor wires it. CVP changes only beacon geometry/scale/material to read as a buoy. No
  camera/framing/re-bake change (TWIN owns those).
- No new dependencies. Single serialized editor per convergence file; git pull --rebase first;
  serialize the 3 hot files across LGC/CXR/3D-TWIN/WFX/ORCA through O0.

EXECUTION ORDER:
- Run W1 discovery: 5 parallel read-only subagents (one per agent row in wave_shape.yml / W1_DISPATCH.md),
  each producing its findings doc. Include the adversarial member (adversarial-collision).
- Then write findings/SYNTHESIS_cvp.md: the confirmed baseline component-class set, the additive
  boundary vs LGC and the style-only boundary vs CXR (by selector and by string), the buoy-marker
  contract + SalishScene wiring seam, the full collision map on the 3 hot files, and the W2 build
  split (baseline-controls-css, layout-forms, buoy-marker).
- PAUSE. Return to O0. Do NOT start W2/W3/W4 (O0-gated).

GATE MANDATE (when O0 promotes to W3): the CVP preflight is RUN, not asserted. Run
tools/waves/gates/cvp-preflight.sh; it writes gate_captures/cvp_preflight.json with per-check
verdicts and exits non-zero on any hard FAIL. W3 may not proceed unless the hard checks are green.
W4 acceptance Read-examines real captured frames into gate_screenshots/ (no screenshot claimed
without reading the rendered output).

QUALITY BAR (no reassurance bias): every finding cites a real file/path; the 3 defects are
re-verified present at the pin by grep before any build is proposed; the additive and style-only
boundaries are proven by selector and by string, not asserted; the collision map names every lane
holding each hot file. Verify any path you cite with Glob/Read.

ESCALATION CATCH: on any decision, trade-off, locked-decision conflict, regression, cross-lane
collision, or gated step, PAUSE and return the question to O0 in your summary. Do not invent scope
beyond this charter and the plan; if something is genuinely ambiguous, note it for O0 rather than
guessing. Do not solicit the human operator. Do not block on the human.

RETURN CONTRACT: a summary listing the 5 findings docs (paths), the synthesis path, the confirmed
baseline component-class set, the additive (vs LGC) + style-only (vs CXR) boundary statements, the
buoy-marker contract + wiring seam, the collision map, the W2 build split, and any open questions
for O0.
```

## More context (need -> file)

| Need | File |
|---|---|
| Authority + locked decisions | `WAVESET_CHARTER.md` |
| The 5 agents + findings docs | `wave_shape.yml`, `W1_DISPATCH.md` |
| The preflight W3 runs | `CVP_PREFLIGHT.md`, `tools/waves/gates/cvp-preflight.sh` |
| Missing component classes | `web/app/globals.css` (no `.chip`; `.ask-*` at 308-318) |
| Chip + raw composer sites | `web/app/components/AdaptiveExplore.tsx` (`:330`, `:335-343`) |
| Cone beacon | `web/app/components/scene/SalishScene.tsx` (`:354-357`) |
| Collision holds on the hot files | `docs/devpost/waves.registry.yaml` (LGC-W4, CXR-1, TWIN W2.6/W-CAM/W-PERFUX-BUILD/W-LABELS, WFX-INTEGRATE, ORCA-OINT) |
| Decisions to confirm before launch | `DECISION_RECORD.md` |

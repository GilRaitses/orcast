# STEP_LOG (newest last)

## 2026-06-28 — S01 hydration + charter authored

- O0 grounded the lane in the live code at `main 97b6397` and re-verified the three defects:
  (1) `web/app/globals.css` has no `.chip` rule and no base `button` / `textarea` / `input` /
  `label` styles (grep for `.chip {` returns zero), so `<button className="chip">` at
  `AdaptiveExplore.tsx:330` and the bare controls render as native unstyled OS controls; the styled
  `.ask-label` / `.ask-textarea` classes exist at `globals.css:308-318` but the home does not use
  them. (2) The home composer is a raw `<label>Ask about the Salish Sea <textarea rows={2}>` at
  `AdaptiveExplore.tsx:335-343`, no width, cramped. (3) The hydrophone beacon is a 6-sided cone
  `coneGeometry args={[1.6, 5, 6]}` in `#ffcf33` at `SalishScene.tsx:354-357`, dominating the frame.
- Confirmed the hot convergence surface: `globals.css` (LGC-W4 tokens + `.glass-surface`; TWIN
  W-LABELS `.scene-label`; WFX-INTEGRATE), `AdaptiveExplore.tsx` (CXR-1 copy redaction, dispatched,
  commit gated to O0), `SalishScene.tsx` (TWIN W2.6 / W-CAM / W-PERFUX-BUILD / W-LABELS,
  WFX-INTEGRATE, ORCA-OINT). CVP carries an explicit collision lock and serializes through O0.
- Locked decisions recorded in the charter: web/ only; baseline-correctness + design-system layer
  (component classes, composer layout, panel hierarchy, Get-access form, mobile breakpoints); NO LGC
  glass/ink token families, ghost-text, self-hide, or preload; style-only (no anonymous-path copy
  change, CXR owns copy); net-new buoy marker under `web/lib/scene/markers/` with the SalishScene
  editor wiring it, no camera/framing/re-bake; no new dependencies; no commit/push/deploy without
  operator request.
- Authored: WAVESET_CHARTER, wave_shape.yml, ORCHESTRATOR_DISPATCH_PROMPT, README, DECISION_RECORD,
  W1_DISPATCH, CVP_PREFLIGHT, and the runnable preflight `tools/waves/gates/cvp-preflight.sh`
  (writes `gate_captures/cvp_preflight.json`). Appended CVP-W1..CVP-W4 + the `cvp-preflight` gate to
  `docs/devpost/waves.registry.yaml`.
- Status: CHARTERED, pending operator GO on the DECISION_RECORD items and the W3 serialize order,
  then W1 launch. W2 build, W3 integrate, and W4 accept are O0-gated.

## 2026-06-28 — S02 operator GO, W1 dispatched

- Operator confirmed DECISION_RECORD items 1-3 ("go"): separate baseline lane, full console pass,
  serialize through O0 with CVP baseline before LGC identity. The exact W3 per-file serialize order
  stays O0-gated and is re-confirmed at the W3 gate.
- Dispatched W1 discovery (read-only) to a background sub-orchestrator running the five disjoint
  agents from `W1_DISPATCH.md` (A1 controls, A2 layout, A3 scene-marker + TWIN boundary, A4
  globals.css additive boundary vs LGC, A5 adversarial + collision + defect re-verify). Each writes
  only its `findings/CVP-<TOPIC>.md`; no edits to `web/`; no dev server; no commit. The
  sub-orchestrator writes `findings/SYNTHESIS_cvp.md` (the W2 build split) and pauses, returning to
  O0. W2/W3/W4 remain O0-gated.

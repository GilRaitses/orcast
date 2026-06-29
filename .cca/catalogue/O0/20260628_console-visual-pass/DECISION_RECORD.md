# Decision record (confirm before launch)

Decisions that lock the CVP charter. Confirmed items are marked CONFIRMED; the rest are proposed
defaults awaiting operator GO. Do not launch a wave whose decisions are not CONFIRMED.

## CONFIRMED (operator GO, 2026-06-28)

1. **Separate baseline lane.** CVP is a separate fast lane that ships the full console visual pass as
   the baseline design layer, NOT folded into LGC and NOT superseding it. LGC-W4 layers its
   liquid-glass identity on top of the CVP baseline. CONFIRMED.
2. **Full console pass scope.** CVP adds the component design system (`.chip`, base
   `button` / `textarea` / `input` / `label`, composer layout, panel hierarchy, the Get-access form,
   mobile breakpoints), fixes the cramped composer, and reshapes the beacon to read as a buoy.
   CONFIRMED.
3. **Collision serialize order.** The three hot files (`globals.css`, `AdaptiveExplore.tsx`,
   `SalishScene.tsx`) are shared with LGC / CXR / 3D-TWIN / WFX / ORCA. W3 integration is a single
   serialized editor, gated on O0 confirming the order against those lanes, with `git pull --rebase`
   first. CONFIRMED at the policy level: serialize through O0, CVP baseline before LGC identity. The
   exact per-file order against the live lane states is re-confirmed at the W3 gate (still O0-gated).

## Hard rails (non-negotiable)

- Target surface `web/` only (Next 14 / React 18 / TS 5, plain CSS, no Tailwind). Root `css/` + `js/`
  and `orcast-angular/` are out of scope.
- CVP is the baseline-correctness + design-system layer. It adds NO `--glass-*` / `--text-ink` token
  family, NO ghost-text composer, NO self-hiding dock, NO consent preload. Those stay LGC's.
- CVP is style only. It changes no anonymous-path copy strings. Copy redaction stays CXR's lane.
- The beacon fix is a net-new module under `web/lib/scene/markers/`; the SalishScene single editor
  wires it. CVP changes only beacon geometry / scale / material. No camera, framing, or re-bake
  change. Those stay the 3D-TWIN lane's.
- No new dependencies. One file, one owner per wave. No dev server during a parallel wave; validate
  with type-check (`cd web && npx tsc --noEmit`).
- No deploy, no promotion, no commit by sub-agents. Operator commits on explicit request.

## Gates

- W1 discovery runs read-only after operator GO on items 1-3.
- W3 integrate and W4 accept are O0-gated; W3 runs the preflight first and must be green on its hard
  checks; W3 launch waits on the confirmed serialize order against LGC / CXR / 3D-TWIN / WFX / ORCA.

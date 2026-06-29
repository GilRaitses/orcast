# CVP Preflight — static battery before W3 integrate

Date: 2026-06-28 (America/New_York). Lane: O0 console-visual-pass (code CVP). Pin: `main 97b6397`.
Scope: the three hot convergence files (`web/app/globals.css`,
`web/app/components/AdaptiveExplore.tsx`, `web/app/components/scene/SalishScene.tsx`), the net-new CVP
files (`web/app/styles/cvp-*.css`, `web/lib/scene/markers/`), and the CVP lane home.

A runnable Phase A static battery modeled on `tools/waves/gates/selfhost-preflight.sh` plus the GP
gap-register verdict format. It runs at W3 entry and before any commit. The harness
(`tools/waves/gates/cvp-preflight.sh`) writes `gate_captures/cvp_preflight.json` with a per-check
verdict and exits non-zero on any hard FAIL.

Verdict legend: PASS (clean) / FIXED (gap found and remediated) / FLAG (recorded, owner action) /
SKIP (does not apply until W2/W3 produce edits).

## How to run

```
bash tools/waves/gates/cvp-preflight.sh
```

Run from anywhere in the repo (the harness finds the repo root). It always writes
`.cca/catalogue/O0/20260628_console-visual-pass/gate_captures/cvp_preflight.json`. Static checks that
need `web/node_modules` (tsc, lint, unit test) SKIP cleanly when dependencies are absent. Checks that
inspect CVP edits (PF-5 boundary) SKIP until CVP has produced changes against the pin. Hard FAIL
conditions: `tsc` errors, invalid YAML, a leaked secret, a defect no longer present at the pin
(plan-vs-reality broken), or a proven boundary violation. SKIP never fails the build.

## Verdict table (filled at W3 entry)

| Check | Verdict | Finding / action |
|---|---|---|
| PF-1.tsc — `cd web && npx tsc --noEmit` | _pending_ | type-check clean on the touched files |
| PF-1.lint — `cd web && npx next lint` | _pending_ | lint clean on the touched files |
| PF-1.test — `node --test "lib/**/*.test.mts"` | _pending_ | unit checks green (buoy marker + any new lib) |
| PF-1.readlints — ReadLints on touched files | _pending_ | 0 diagnostics (editor-run; recorded by the integrator) |
| PF-1.yaml — `wave_shape.yml` + registry valid | _pending_ | both parse as YAML |
| PF-2.secrets — secret-leak scan on new CVP files | _pending_ | no secret values in any new CVP file |
| PF-3.chip — `.chip` rule absent in `globals.css` | _pending_ | defect D1 still present at the pin |
| PF-3.composer — raw composer at `AdaptiveExplore.tsx:335-343` | _pending_ | defect D2 still present at the pin |
| PF-3.beacon — cone `coneGeometry` at `SalishScene.tsx` | _pending_ | defect D3 still present at the pin |
| PF-4.rebase — `git pull --rebase` clean | _pending_ | operator action before W3; harness notes |
| PF-4.worktree — 3 hot files not concurrently held | _pending_ | clean tree or an O0-confirmed serialize |
| PF-5.tokens — no `--glass-*` / `--text-ink` added | _pending_ | CVP added no LGC token family |
| PF-5.lgc — no ghost-text / self-hide / preload added | _pending_ | CVP added no LGC behavior |
| PF-5.copy — no anonymous-path copy change | _pending_ | CVP changed no copy string (CXR owns it) |
| PF-6.prose — new copy clears prose + cxr deny-terms | _pending_ | run on W4 render captures |

## The battery

- **PF-1 static.** `tsc --noEmit`, `next lint`, `node --test "lib/**/*.test.mts"`, ReadLints 0 on the
  touched files, and `wave_shape.yml` (plus the edited registry) valid YAML. The tsc / lint / test
  checks SKIP when `web/node_modules` is absent; ReadLints is an editor-run check recorded by the
  integrator.
- **PF-2 secret-leak.** No secret values (AWS keys, private keys, known token prefixes) in any new
  CVP file or the lane home.
- **PF-3 plan-vs-reality.** Re-verify the three defects are still present at the pin by grep: `.chip`
  undefined in `globals.css`, the raw composer at `AdaptiveExplore.tsx:335-343`, and the cone beacon
  `coneGeometry` at `SalishScene.tsx`. A defect that is no longer present is a hard FAIL, so the lane
  never builds against stale state.
- **PF-4 collision.** `git pull --rebase` clean (an operator action before W3; the harness notes it),
  and the three hot convergence files are not concurrently held by LGC / CXR / 3D-TWIN / WFX / ORCA
  without an O0 serialize. The harness checks the working tree of the three files and flags a dirty
  hot file for O0 to confirm.
- **PF-5 boundary.** CVP added no `--glass-*` or `--text-ink` token family and no ghost-text,
  self-hide, or preload (the LGC boundary), and changed no anonymous-path copy string (the CXR
  boundary), proven by grep against the CVP diff versus the pin. These SKIP until CVP has produced
  edits.
- **PF-6 prose gate.** Any new user-facing copy clears the prose gate and the cxr deny-terms gate.
  Runs on the W4 render captures via `tools/waves/gates/console-deny-terms.sh`; SKIP until captures
  exist.

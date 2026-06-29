# ENV — env-handle-consolidation (waveset charter)

- Lane code: `ENV`  Family: `BSWR`  Owner: dispatched sub-orchestrator (answers to O0)
- Type: execution (scene module + single convergence edit), GPU-verified
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/` ; dispatch `dispatch/ENV/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
- Umbrella: `PROGRAM.md` ; predecessor: ORCA family (`../20260628_orca-biologging-twin/`)

## Intent

Remove the duplicate WFX environment PMREM bake the homepage slice introduced.
ORCA exposes the live `WfxEnvHandle` it already builds, the slice consumes that
single bake for the reenactment pool, and the scene keeps exactly one source of
truth for the WFX environment and one `scene.environment` writer.

## Grounding (real seams + verified root cause)

The seam is documented by the slice's own WIRING note:
`web/lib/scene/wfx/WIRING-slice-note.md` (SEAM 4). It states:
- `SalishScene.tsx` `SliceRig` calls `makeRealWfxEnv` a SECOND time. This second
  PMREM bake is used ONLY as the env map handed to `createOrcaPool`, so the
  reenactment pool materials are lit by the same scene sky and underwater optic.
- The slice never assigns this handle to `scene.environment`; `OrcaRig` remains
  the sole writer of `scene.environment` (verified: exactly one writer today).
- Follow-up for ORCA: expose the live `WfxEnvHandle` that `OrcaRig` already builds,
  through a shared ref or a small accessor, so the slice consumes that single
  existing bake instead of baking a second PMREM. The second bake is a deliberate,
  scoped stopgap until ORCA publishes its handle.

Related files: `web/lib/scene/wfx/realWfxEnv.ts` (`makeRealWfxEnv`),
`web/lib/scene/orca/materials/wfxEnv.ts`, `web/lib/scene/orca/OrcaController.ts`,
`web/lib/scene/orca/index.ts`, `web/lib/scene/reenactment/OrcaPool.ts`
(`createOrcaPool` env input), and the slice mount in
`web/app/components/scene/SalishScene.tsx`.

Root cause: ORCA never published an accessor for the `WfxEnvHandle` it builds, so
the slice baked a second PMREM as a scoped stopgap. The fix is the planned
accessor plus the slice consuming it, then dropping the second bake.

## Locked decisions (do NOT reopen)

1. Exactly one `scene.environment` writer stays. `OrcaRig` is and remains the sole
   writer. ENV does not add a second writer; it removes a second BAKE.
2. The accessor is additive and ORCA-owned. It exposes the existing live
   `WfxEnvHandle` through a shared ref or a small read accessor with a defined
   lifecycle (valid after the env is built, cleared on dispose). It does not
   change when or how ORCA builds the env.
3. The slice consumes the published handle for the pool lighting. The second
   `makeRealWfxEnv` call is removed only after the slice reads the handle and the
   pool is verified lit identically.
4. No visual regression. The reenactment pool must be lit identically before and
   after (same sky + underwater optic). GPU before/after frames prove parity.
5. Disposal correctness. Removing the second bake must not leave the pool reading
   a disposed texture, and must not free the env ORCA still owns. Lifecycle is
   audited in `ENV-ADV`.
6. `SalishScene.tsx` and the orca controller are convergence files; the edit is a
   single serialized editor in `ENV-INT`, `git pull --rebase` first, serialized
   across ORCA / WFX / OCN / 3D-TWIN and the sibling BSWR lanes.

## Wave structure

- `ENV-R` (research + discovery, read-only). Parallel; each owns one `dispatch/ENV/findings/ENV-<TOPIC>.md`:
  - R1 ORCA env ownership: where `OrcaRig` / `OrcaController` builds the `WfxEnvHandle`, its lifecycle, and the cleanest accessor shape.
  - R2 slice consumer: how `SliceRig` feeds `createOrcaPool` today and the minimal change to consume a published handle.
  - R3 lifecycle + disposal: ownership of the env texture, dispose order, and the single-`scene.environment`-writer invariant.
  - R4 adversarial: the double-write / disposed-texture / lighting-mismatch failure modes; what proves parity.
- `ENV-Q` (qualify methodology). GATED. Fixes the accessor API (ref vs accessor, lifecycle contract) and the slice consumption; states the parity pass metric; coordinates ownership with the ORCA lane. Returns to O0.
- `ENV-B` (implement). ORCA-owned accessor net-new/extend under `web/lib/scene/orca/**`; the slice-side consumer prepared but not yet wired into the convergence file. No `SalishScene` edit yet.
- `ENV-INT` (integrate). GATED. Single editor wires the slice to the published handle in `SalishScene.tsx` and drops the second `makeRealWfxEnv`; serialize across ORCA/WFX/OCN/3D-TWIN.
- `ENV-ADV` (adversarial review). Audits the single-writer invariant, disposal, and lighting parity; loops back to `ENV-B`/`ENV-INT` until zero open P0/P1.
- `ENV-ACCEPT` (accept). GATED. GPU before/after frames prove the pool is lit identically with one fewer PMREM bake; Read-examined; frame-time A/B (a small improvement is expected, parity is the bar).

## Acceptance criteria (hard, checkable)

- ORCA publishes a `WfxEnvHandle` accessor; the slice consumes it; the second `makeRealWfxEnv` call in `SalishScene.tsx` is removed.
- Exactly one `scene.environment` writer remains (`OrcaRig`); a grep/AST check confirms no second writer was introduced.
- GPU before/after frames show the reenactment pool lit identically (Read-examined parity).
- No disposed-texture read; disposal order is correct (audited).
- One fewer PMREM bake at slice mount, confirmed; frame-time A/B at parity or better.

## Escalation

Per PROGRAM.md. Pause and return to O0 on the ORCA ownership coordination, the
convergence edit slot, the GPU capture, or commit.

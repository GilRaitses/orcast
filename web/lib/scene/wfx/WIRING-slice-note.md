# WIRING note for ORCA, from SLICE-INTEGRATE (SEAM 4)

This note records how the homepage B-side slice obtains its WFX environment, and
the consolidation follow-up the slice leaves for the ORCA owner. It is additive
context. It changes no ORCA file.

## What the slice does today

`SalishScene.tsx` `SliceRig` calls `makeRealWfxEnv` a SECOND time. This second
PMREM bake is used ONLY as the env map handed to `createOrcaPool`, so the
reenactment pool materials are lit by the same scene sky and the twin-unit
underwater optic. The slice never assigns this handle to `scene.environment`.

`OrcaRig` remains the sole writer of `scene.environment`. The verified state
after this integrate is exactly one `scene.environment` writer.

## Follow-up for ORCA

Expose the live `WfxEnvHandle` that `OrcaRig` already builds, through a shared
ref or a small accessor, so the slice can consume that single existing bake for
the reenactment pool instead of baking a second PMREM. That removes the
duplicate GPU PMREM bake and keeps one source of truth for the WFX env. The
second bake is a deliberate, scoped stopgap until ORCA publishes its handle.

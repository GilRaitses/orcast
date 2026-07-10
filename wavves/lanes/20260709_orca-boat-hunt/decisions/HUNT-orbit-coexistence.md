# HUNT — OrbitControls coexistence in /orca-strike

- **Date:** 2026-07-09
- **Lane:** wavves/lanes/20260709_orca-boat-hunt
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5 (main, unchanged since charter; no commits made by this lane)
- **Question:** `orcaPilot/WIRING.md` step 5 flagged that a future integrator must resolve how `OrbitControls` and the pilot's own chase camera coexist in the new route, naming two options. Which does HUNT-INT implement?
- **Options considered:**
  - A: No `OrbitControls` in this route at all; the chase camera (`orcaPilot/chaseCamera.ts`) is the sole camera control.
  - B: Mount `OrbitControls` as the other sandboxes do, but `enabled={false}` while `input.pointerLocked` is true, so free-look-by-drag is available before the player clicks in to pilot.
- **Pick:** A (no_orbit).
- **Rationale:** Fewer moving parts for a hackathon build; avoids any per-frame fight between orbit-drag and the chase camera's own `update()` writes to `camera.position`.
- **Implications for HUNT-INT:** The new `OrcaStrikeScene.tsx` never imports or mounts `<OrbitControls>`. `chaseCamera.ts`'s `ChaseCamera.update(camera, orcaWorldPos, heading, dt)` is the only per-frame camera writer in this route, called every frame regardless of `pointerLocked` state (so the camera still frames the orca even before the player clicks the canvas to lock the mouse). This also removes any need to gate on `input.pointerLocked` for camera-control purposes; that field remains meaningful only for the pilot's own mouse-look yaw/pitch deltas (which the sampler already zeroes while unlocked).

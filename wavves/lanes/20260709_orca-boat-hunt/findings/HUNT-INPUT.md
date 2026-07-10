# HUNT-INPUT — keyboard / pointer-lock discovery (W1)

Discovery member: **INPUT**. Scope: `web/` source (excluding `node_modules`). Read-only except this file.

---

## Existing input controller search

### Grep summary (no player movement controller found)

Searches across `web/**/*.{ts,tsx,js,jsx,mjs}` returned **zero matches** for:

| Pattern | Result |
|---|---|
| `pointerlock`, `PointerLockControls`, `pointer-lock`, `pointerLock` | No matches |
| `WASD`, `FirstPersonControls`, `KeyboardControls` | No matches |
| `requestPointerLock`, `exitPointerLock` | No matches |
| `FlyControls`, `TrackballControls`, `ArcballControls`, `DragControls`, `DeviceOrientation` | No matches |
| `movementX`, `movementY` | No matches |
| `gamepad`, `Gamepad`, `touchstart`, `touchmove` | No matches |
| `ArrowUp` / `ArrowDown` / `KeyW` / `KeyA` / `KeyS` / `KeyD` / `Space` (movement keys) | No matches |

**Conclusion:** There is no existing WASD + pointer-lock or first-person player movement controller anywhere in `web/`.

### Camera controls that *do* exist (orbit, not pilot)

All 3D scenes use **drei `OrbitControls`** (mouse-drag orbit / zoom / pan), not keyboard-driven movement:

| File | Import / usage |
|---|---|
| `web/app/components/scene/SalishScene.tsx:13` | `import { OrbitControls, Html } from "@react-three/drei"` |
| `web/app/(sandbox)/journey/JourneyScene.tsx:31` | `import { OrbitControls } from "@react-three/drei"` |
| `web/app/(sandbox)/water/WaterSandboxScene.tsx:23` | `import { OrbitControls } from "@react-three/drei"` |
| `web/app/(sandbox)/tiles3d/TilesSandboxScene.tsx:12` | `import { OrbitControls } from "@react-three/drei"` |
| `web/app/components/scene/realism/RealismSandbox.tsx:16` | `import { OrbitControls } from "@react-three/drei"` |

The cinematic camera director (`web/lib/scene/camera/director.ts`) drives `OrbitControls` programmatically via `flyTo` / `orbit` tweens. It holds no keyboard state and is not a player controller.

`web/app/(sandbox)/orca/OrcaSandboxScene.tsx` animates an orca from biologging tracks with an auto-orbit camera (`camera.lookAt(...)` at line 193). No user steering.

### Keyboard handling found (UI chrome only, not movement)

| File:line | Purpose |
|---|---|
| `web/app/components/ui/Tooltip.tsx:75-91` | `document.addEventListener("keydown", …)` — dismiss tooltip on `Escape` |
| `web/app/components/scene/SearchAffordance.tsx:205-208` | `onKeyDown` on search input — collapse on `Escape` |
| `web/app/components/SightingCheckPanel.tsx:155-167` | `handleKeyDown` on textarea — `Tab` accepts suggestion, `Enter` submits |

None of these track held keys or drive scene/camera movement.

### Pointer / mouse handling found (non-camera)

| File:line | Purpose |
|---|---|
| `web/lib/scene/hud/spectro/SpectroHud.ts:261-279` | `pointerdown` / `pointermove` / `pointerup` on a 2D canvas — spectrogram scrub drag |
| `web/app/components/ui/Tooltip.tsx:89` | `document.addEventListener("mousedown", …)` — outside-click dismiss |

`SpectroHud` uses `setPointerCapture` for a timeline slider, not pointer-lock or mouse-look.

### `addEventListener` inventory

All `addEventListener` calls in `web/` are for: tile streaming (`needs-update`, `load-model`), SSE abort, spectrogram HUD, tooltip dismiss, scene error relay (`salish-scene-error`), or provenance UI. No `keydown`/`keyup` listeners on `window` or `document` for movement.

### `web/lib/scene/orcaPilot/` does not exist yet

Glob for `web/lib/scene/orcaPilot/**` returned 0 files. The pilot module is greenfield.

---

## Installed-but-unused input helpers

### Dependency declaration

`web/package.json:22` declares `"@react-three/drei": "^9.122.0"`. `web/package-lock.json` pins the same range. **No `node_modules/` tree is present in this workspace**, so exports were verified from the published `@react-three/drei@9.122.0` type definitions on unpkg (same version as declared).

### What drei exports (available but unused in `web/`)

From `@react-three/drei@9.122.0` type entrypoints:

**`web/index.d.ts`** re-exports `./web` and `./core`.

**`web/index.d.ts`** includes:

- `KeyboardControls` — zustand-backed key map with `useKeyboardControls()` selector hook (`web/KeyboardControls.d.ts`)
- `ScrollControls`, `PresentationControls`, `DragControls`, `FaceControls`, …

**`core/index.d.ts`** includes camera/input controls:

- `PointerLockControls` — wraps `three-stdlib` `PointerLockControls`; props: `domElement`, `selector`, `enabled`, `onLock`, `onUnlock`, `makeDefault` (`core/PointerLockControls.d.ts`)
- `FirstPersonControls` — wraps `three-stdlib` `FirstPersonControls` (`core/FirstPersonControls.d.ts`)
- `FlyControls`, `MapControls`, `OrbitControls`, `TrackballControls`, `ArcballControls`, `CameraControls`, `DeviceOrientationControls`

### What `web/` actually imports from drei

Only **`OrbitControls`** and **`Html`** appear in import statements (5 files, listed above). No file imports `KeyboardControls`, `PointerLockControls`, `FirstPersonControls`, `FlyControls`, or `useKeyboardControls`.

### Repo convention note

Existing scene modules favor **hand-rolled, framework-free controllers** advanced per-frame:

- `web/lib/scene/camera/director.ts` — pure three.js, no React state in the hot loop; scene calls `update(deltaSeconds)` inside `useFrame`
- `web/lib/scene/camera/types.ts:3-7` — types are "deliberately framework-free"
- `web/lib/scene/tiles/useTilesLayer.ts` — imperative `TilesRenderer` lifecycle inside r3f `useFrame`, not a drei helper

A minimal hand-rolled input hook/class in `web/lib/scene/orcaPilot/` is consistent with this pattern. Drei helpers are available without new npm packages but are currently unused.

---

## Proposed input-state shape

Minimal, dependency-free interface for a pilot input sampler consumed once per frame (mirrors `CameraDirector` / `OrcaController` separation of input state from physics):

```typescript
/**
 * Snapshot of player input for one simulation tick.
 * Produced by an input sampler; consumed by the orca-boat pilot controller.
 * All look deltas are radians since the previous frame (pointer-lock movementX/Y
 * scaled by sensitivity). Keys are booleans for "held this frame".
 */
export interface OrcaPilotInput {
  /** Forward (W / ArrowUp). */
  forward: boolean;
  /** Back (S / ArrowDown). */
  back: boolean;
  /** Strafe/port (A / ArrowLeft). */
  left: boolean;
  /** Strafe/starboard (D / ArrowRight). */
  right: boolean;
  /** Throttle boost held (Shift). */
  boost: boolean;

  /** Horizontal look delta since last frame, radians (+ = turn right). */
  yawDelta: number;
  /** Vertical look delta since last frame, radians (+ = look up). */
  pitchDelta: number;

  /** Whether pointer lock is currently active (mouse-look enabled). */
  pointerLocked: boolean;
}
```

Suggested companion (not part of the per-frame snapshot, but useful for the sampler):

```typescript
/** Mutable handle the sampler fills; read once per useFrame via getInput(). */
export interface OrcaPilotInputHandle {
  /** Latest sampled input; replaced or mutated only inside the sampler. */
  input: OrcaPilotInput;
}
```

Key-binding defaults (implementation detail, not part of the interface): `WASD` + arrow aliases for movement, `Shift` for boost, click-to-lock on the canvas for pointer-lock. No new packages required.

---

## SSR/Next.js gotchas

Patterns already used in sandbox hosts that a new orca-boat-hunt scene should follow:

### 1. `dynamic(…, { ssr: false })` host shell

Every r3f sandbox uses a thin `"use client"` host that lazy-loads the scene with `ssr: false` so three/WebGL never import on the server:

- `web/app/(sandbox)/journey/JourneyHost.tsx:3-10` — comment + `dynamic(() => import("./JourneyScene"), { ssr: false })`
- `web/app/(sandbox)/orca/OrcaSandboxHost.tsx:3-9` — same pattern for the existing orca sandbox
- `web/app/(sandbox)/tiles3d/TilesSandboxHost.tsx:3-11`
- `web/app/components/scene/SceneHost.tsx:9-12` — production Salish scene

A new `orca-boat-hunt` route should use the same Host → `dynamic` Scene split.

### 2. `typeof window === "undefined"` guards

Sandbox scenes read query params or touch browser APIs only behind guards:

- `web/app/(sandbox)/orca/OrcaSandboxScene.tsx:46` — `if (typeof window === "undefined") return p;` in `readParams()`
- `web/app/(sandbox)/water/WaterSandboxScene.tsx:129,154` — same in `readConfig()` / `readTuning()`
- `web/app/components/scene/SalishScene.tsx:1856` — `useEffect` early-return before `window.location.search`
- `web/lib/scene/hydrophone/StationPlayer.ts:29` — returns `null` when `window` is undefined

Any `window`/`document` listener registration for keyboard or pointer-lock must live inside `useEffect` (or a class constructed client-side) with the same guard.

### 3. `"use client"` on all r3f entrypoints

All Canvas-bearing components carry `"use client"` (e.g. `OrcaSandboxScene.tsx:1`, `JourneyHost.tsx:1`). Server Components must not import the pilot module directly.

### 4. Pointer-lock-specific browser constraints

Not present in the repo today; relevant for implementation:

- **`requestPointerLock()` requires a user gesture** (click/keypress). A "click canvas to pilot" affordance is required; cannot auto-lock on mount.
- **Listen on the locked element** (`canvas` / `gl.domElement`) for `mousemove` (`movementX`/`movementY`) while locked; fall back to zero deltas when unlocked.
- **`pointerlockchange` / `pointerlockerror`** on `document` need cleanup on unmount.
- **Escape** exits pointer lock (browser default). Existing UI uses `Escape` for dismiss (`Tooltip.tsx:76`, `SearchAffordance.tsx:206`); ensure no conflict or accept that Escape unlocks the pilot.
- **Tab focus**: keyboard listeners on `window` or `document` should check `pointerLocked` (or canvas focus) so typing in UI inputs does not steer the boat.

### 5. WebGL availability check

`web/app/components/scene/SceneHost.tsx:20-30` probes `WebGLRenderingContext` before mounting the scene. Optional for a sandbox-only route, but worth mirroring if the hunt is embedded in a production surface.

### 6. Coexistence with `OrbitControls`

Existing scenes attach `OrbitControls` as `makeDefault`. A pilot scene must **disable or detach orbit controls** while pointer-lock is active to avoid fighting inputs (orbit drag vs. mouse-look). No precedent in-repo; this is a new integration point.

# WIRING-marker, buoy marker integration seam (CVP W2 Agent B3)

Wave 2 Agent B3 of the console-visual-pass lane. This doc describes the single
W3 integrator edit against `web/app/components/scene/SalishScene.tsx`. B3
produced net-new files only and edited no existing product file. The module
`web/lib/scene/markers/buoyMarker.tsx` and its `web/lib/scene/markers/index.ts`
barrel are not yet imported by any scene file. The W3 editor performs the wiring
below.

## What B3 built

A pure react-three-fiber module that renders a navigation buoy from core three
primitives only. No new dependency, no `@react-three/drei`, no `Html`, no label,
no `position` prop, no event handlers, no scene or camera reference.

Export contract.

```tsx
export interface BuoyMarkerProps { color: string; hovered: boolean; }
export function BuoyMarker({ color, hovered }: BuoyMarkerProps): JSX.Element;
```

Geometry of the returned `<group>`, all `meshStandardMaterial`.

- Body, a `cylinderGeometry args={[0.5, 0.5, 0.8, 16]}` at `position={[0, 0.4, 0]}`,
  so the base sits at the group origin and the body floats at the water line.
  Material uses the `color` prop with `roughness={0.6}` and a low emissive
  (`emissive={color}`, `emissiveIntensity` 0.18 at rest, 0.4 on hover) so it
  reads as a physical buoy, not a glow source.
- Mast, a `cylinderGeometry args={[0.06, 0.06, 1.0, 8]}` at `position={[0, 1.3, 0]}`,
  white with a faint `emissive={color}` at `emissiveIntensity={0.2}` so it reads
  as structure rather than a status light.
- Topmark light, a `sphereGeometry args={[0.22, 16, 16]}` at `position={[0, 1.95, 0]}`,
  carrying `color` as both color and emissive at `emissiveIntensity` 0.65 at rest
  and 1.0 on hover so the status read stays legible.

## Exact W3 integrator edit list against SalishScene.tsx

The W3 editor changes only beacon geometry, scale, and material plus the local
interaction wrapper inside `HydrophoneBeacon`. Nothing else in the file moves.

### Edit 1, add the import

Add this line near the existing `@/lib/scene/*` imports at the top of the file,
for example directly after the `@/lib/scene/water2` import at line 30.

```tsx
import { BuoyMarker } from "@/lib/scene/markers";
```

### Edit 2, replace the cone geometry+material and the white stem mesh

Inside `HydrophoneBeacon`, the current visual primitives are the cone mesh at
lines 342 to 357 and the white stem mesh at lines 358 to 361. Replace the cone
geometry+material at lines 355 to 356 AND the entire white stem mesh at lines
358 to 361 with a single `<BuoyMarker>`, and relocate the handlers and scale off
the cone `<mesh>` onto the outer `<group>` at line 341.

Current code (lines 341 to 361).

```341:361:web/app/components/scene/SalishScene.tsx
    <group position={position}>
      <mesh
        position={[0, 6, 0]}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.4 : 1}
      >
        <coneGeometry args={[1.6, 5, 6]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 0.9 : 0.4} />
      </mesh>
      <mesh position={[0, 1.5, 0]}>
        <cylinderGeometry args={[0.18, 0.18, 9, 6]} />
        <meshStandardMaterial color="#ffffff" emissive={color} emissiveIntensity={0.3} />
      </mesh>
```

Replacement. The handlers and the hover scale move from the cone `<mesh>` onto
a thin wrapping `<group>` so the multi-mesh buoy stays clickable and hoverable.
A buoy is a multi-mesh group and an r3f `<mesh>` holds one geometry and one
material, so the interaction must live on a group, not on a single mesh. Use a
gentle hover scale of 1.15 in place of the old 1.4, a scale value change that
stays geometry/scale/material only.

```tsx
    <group position={position}>
      <group
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.15 : 1}
      >
        <BuoyMarker color={color} hovered={hovered} />
      </group>
```

Note the old cone `position={[0, 6, 0]}` and the stem `position={[0, 1.5, 0]}`
are both dropped. The buoy floats at the group origin (the surface) by design,
so it no longer lifts 6 units up a 9-unit stem. The outer `<group position=
{position}>` at line 341 keeps placing the whole beacon, unchanged.

### Edit 3, leave the Html hover label untouched

The `Html` hover label at lines 362 to 366 stays exactly as is. It is
TWIN-W-LABELS territory, not CVP. Do not move it, restyle it, or change its
`position={[0, 11, 0]}`.

```362:366:web/app/components/scene/SalishScene.tsx
      {hovered && (
        <Html center distanceFactor={120} position={[0, 11, 0]} style={{ pointerEvents: "none" }}>
          <div className="scene-beacon-label">{node.name ?? node.location ?? "Hydrophone"}</div>
        </Html>
      )}
```

## Prop contract preserved across the seam

- `position`, the outer `<group position={position}>` at line 341, fed by
  `SurfaceBeacons` placement at line 404. Unchanged.
- `color`, the inline value computed at line 339 from `node.status`, passed
  straight into `BuoyMarker`. The #ffcf33 online and #888 offline contract is
  unchanged.
- `hovered`, the local state at line 337 set by the pointer handlers, now on the
  wrapping group, passed into `BuoyMarker`. Unchanged.
- `onSelect`, wired through `SurfaceBeacons` at line 404 and emitting the
  hydrophone intent at lines 892 to 901. Unchanged.

## Why these dimensions read as a buoy (reasoned, not rendered)

A true visual render needs a browser and a dev server, which is forbidden in W2.
The buoy visual read is verified in the W4 accept wave with Playwright. The
dimensions are chosen against the old cone proportions so the read holds without
a render now.

The old marker is a `coneGeometry` of radius 1.6 and height 5 sitting on a
height-9 stem, with the cone centre lifted to y 6. The cone spans roughly y 3.5
to y 8.5 and the stem spans roughly y -3 to y 6, so the combined visual reach is
about 11.5 scene units against a SCENE_WIDTH of 120 and a resting orbit framing
radius near 24 units. A 1.6-radius lit spike that tall occupies a large fraction
of the resting frame and reads as a glowing tower, not a buoy.

The new buoy has a body radius of 0.5, under one third of the old 1.6 radius, so
its footprint is roughly one ninth of the cone footprint by area. Its total
height is about 2.17 units, the topmark light centre at y 1.95 plus the 0.22
sphere radius, which is under one fifth of the old 11.5-unit reach and well under
half the old 5-unit cone height. The squat body at the surface plus a thin mast
plus a small light is the standard navigation-buoy silhouette, so the marker
reads as a floating buoy rather than a frame-dominating cone.

The emissive split carries the buoy read further. The body sits at a low
`emissiveIntensity` near 0.18 with `roughness` 0.6, so it catches the scene light
as a solid object instead of self-illuminating. The topmark light holds a high
`emissiveIntensity` near 0.65 so the status color stays legible at a glance, the
way a real buoy light does. Hover raises both emissive steps and applies a gentle
1.15 group scale, signalling selection without ballooning the marker.

## TWIN boundary, explicit

CVP changes only beacon geometry, scale, and material plus the local interaction
wrapper. No camera, framing, datum, tile loading, water, re-bake, or label change.

- No camera or controls. `IntentDirectorRig`, `createCameraDirector`, the resting
  orbit at lines 559 to 565, the `OrbitControls` at lines 908 to 918, and the
  `minDistance`/`maxDistance` zoom bounds at lines 827 to 830 stay untouched.
- No datum. `SEA_LEVEL_Y` at line 111, `TILESET_BOUNDS` at lines 93 to 98,
  `SCENE_DEPTH` at line 103, and the `worldUnitsPerMeter` fit scale stay
  untouched.
- No tile loading or re-bake. `useTilesLayer`, `FULL_TILESET_URL`, the LoD caps
  at lines 133 to 136, and the substrate load stay untouched.
- No water. `Water2Rig` at lines 275 to 326 and its mount stay untouched.
- No labels. The `Html` hover label at lines 362 to 366 and its
  `scene-beacon-label` styling stay untouched. TWIN-W-LABELS owns them.

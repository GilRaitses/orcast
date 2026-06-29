# CVP-MARKER findings, scene-marker audit and TWIN boundary

W1 Agent A3, console-visual-pass lane. READ-ONLY discovery. This is the only
file written by A3. No product code was edited.

## Pin and tree state

Dispatch named `main 97b6397`. Actual HEAD at audit time is
`a914ad1bdb482cc5a13ba514eba808ba7082b3a6`, advanced past the pin as the charter
anticipated. Every cite below is real `file:line` from the current working tree.
The beacon now sits two lines lower than the dispatch sketch, so the cone
geometry is at line 355 rather than 354. All line numbers in this doc reflect the
current tree.

## 1. Current beacon cite

The beacon is the `HydrophoneBeacon` component in
`web/app/components/scene/SalishScene.tsx`, defined at lines 328 to 369.

Hover and online state, plus the color origin.

```337:339:web/app/components/scene/SalishScene.tsx
  const [hovered, setHovered] = useState(false);
  const online = (node.status ?? "online") === "online";
  const color = online ? "#ffcf33" : "#888";
```

Color origin is line 339. The default `#ffcf33` is not a prop and not external
data. It is computed inline from `node.status`. Online resolves to `#ffcf33`, any
non-online status resolves to `#888`. The same `color` value feeds the cone
material at line 356, the white stem emissive at line 360, and is the only color
input the buoy module needs.

The interactive cone mesh, with its position, click and hover handlers, and the
frame-dominating geometry and material.

```342:357:web/app/components/scene/SalishScene.tsx
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
```

- Geometry, line 355, `coneGeometry args={[1.6, 5, 6]}`, a radius 1.6, height 5,
  6-sided cone.
- Material, line 356, `meshStandardMaterial` with `color` and `emissive` both set
  to the node color and `emissiveIntensity` 0.4 at rest, 0.9 on hover. The
  emissive on top of the color is what makes the cone glow and read as a beacon.
- Scale, line 353, `scale={hovered ? 1.4 : 1}`, a 40 percent grow on hover.
- Mesh position, line 343, `position={[0, 6, 0]}`, lifts the cone center 6 units
  above the group origin.

The white stem below the cone.

```358:361:web/app/components/scene/SalishScene.tsx
      <mesh position={[0, 1.5, 0]}>
        <cylinderGeometry args={[0.18, 0.18, 9, 6]} />
        <meshStandardMaterial color="#ffffff" emissive={color} emissiveIntensity={0.3} />
      </mesh>
```

Stem geometry is line 359, `cylinderGeometry args={[0.18, 0.18, 9, 6]}`, a radius
0.18, height 9, 6-sided cylinder centered at y 1.5, so it spans roughly y -3 to
y 6. The cone center at y 6 with height 5 spans roughly y 3.5 to y 8.5. Combined
visual reach is about y -3 to y 8.5, near 11.5 scene units tall.

The hover label, owned by the labels lane, not by CVP.

```362:366:web/app/components/scene/SalishScene.tsx
      {hovered && (
        <Html center distanceFactor={120} position={[0, 11, 0]} style={{ pointerEvents: "none" }}>
          <div className="scene-beacon-label">{node.name ?? node.location ?? "Hydrophone"}</div>
        </Html>
      )}
```

CVP does not touch lines 362 to 366. The `Html` label and its
`scene-beacon-label` styling are TWIN-W-LABELS territory.

## 2. Component shape, marker group, and instantiation

`HydrophoneBeacon` props, line 328 to 336.

- `node: HydrophoneNode`, the data record. Carries `status` for color, and `name`
  or `location` for the label.
- `position: [number, number, number]`, the placed scene position, applied to the
  outer `<group position={position}>` at line 341.
- `onSelect: (node: HydrophoneNode) => void`, the click callback.

`HydrophoneNode` is typed in `web/lib/sceneIntent.ts`.

```35:44:web/lib/sceneIntent.ts
export interface HydrophoneNode {
  id: string | number | null;
  name?: string | null;
  location?: string | null;
  latitude: number;
  longitude: number;
  status?: string;
  streamUrl?: string | null;
  source?: string;
}
```

The marker group and the instantiation live in `SurfaceBeacons`, lines 373 to
408. It projects each node to a scene XZ, raycasts the streamed tile surface for
Y, then maps one `HydrophoneBeacon` per placed node.

```401:407:web/app/components/scene/SalishScene.tsx
  return (
    <>
      {placed.map(({ node, key, position }) => (
        <HydrophoneBeacon key={key} node={node} position={position} onSelect={onSelect} />
      ))}
    </>
  );
```

`HydrophoneBeacon` is instantiated at line 404. `SurfaceBeacons` is mounted once
inside `TwinScene`, lines 888 to 902, fed by `tiles`, `tick`, `nodes`, and an
`onSelect` that emits a hydrophone intent. The hydrophone data source is the
`/api/live-hydrophones` fetch in the `SalishScene` default export, lines 966 to
973, with `ORCASOUND_FALLBACK` from `web/lib/sceneIntent.ts:48` as the offline
roster. Beacons are filtered to the modeled bbox at lines 993 to 1000.

The mount point a buoy module wires into is inside `HydrophoneBeacon`, the visual
primitives at lines 355 to 361. The placement pipeline, the marker group, the
instantiation map, and the data source all stay unchanged.

## 3. web/lib/scene/markers/ is net-new

Confirmed absent. A directory listing of `web/lib/scene/markers` returns
`No such file or directory`, and a recursive glob of `web/lib/scene/markers/**`
returns zero files. The sibling modules that already exist under
`web/lib/scene/` are `tiles`, `picking`, `substrate`, `water2`, `camera`,
`atmosphere`, `terrain`, `decor`, `bathy`, and `orca`. The buoy fix lands as a
brand-new `markers` peer that no current code imports.

## 4. Buoy contract for the net-new module

The module is pure. It renders react-three-fiber primitives only and adds no new
dependency. It performs no scene mutation, holds no camera or controls reference,
loads no tiles, and reads no datum. It is a visual factory the single SalishScene
editor mounts inside the existing beacon group.

### Export shape

Recommended file `web/lib/scene/markers/buoyMarker.tsx`, with an `index.ts`
barrel so the editor imports from `@/lib/scene/markers`.

```tsx
// web/lib/scene/markers/buoyMarker.tsx (proposed, NOT yet written by A3)
export interface BuoyMarkerProps {
  color: string;   // from node.status, #ffcf33 online or #888 offline
  hovered: boolean; // drives the hover emissive lift and the modest grow
}

// A pure r3f component returning a <group> of three primitives that read as a
// navigation buoy. No event handlers, no position. The caller owns placement,
// click, and hover, so the prop contract stays color + hover only.
export function BuoyMarker(props: BuoyMarkerProps): JSX.Element;
```

The export is a component returning a `<group>`, not a hook and not a class. The
component carries no `position` because the existing outer
`<group position={position}>` at line 341 already places it, and no handlers
because the existing interactive structure already owns click and hover.

### Geometry that reads as a buoy, not a frame-dominating cone

A buoy reads as a squat floating body with a small light or topmark, sitting at
the water surface, not a tall glowing spike. The proposed three-part group, all
core three primitives.

- A short buoy body, a `cylinderGeometry` of radius about 0.5 and height about
  0.8, centered just above the group origin so it floats at the surface.
- A thin mast, a `cylinderGeometry` of radius about 0.06 and height about 1.0
  above the body.
- A small topmark light, a `sphereGeometry` of radius about 0.22, or a small
  `coneGeometry` cardinal topmark, at the mast top, carrying the node color as
  the emissive so the status read survives at a glance.

### Scale guidance

Grounded in the current proportions. The existing cone is height 5 with a
height 9 stem, near 11.5 units of combined visual reach against a SCENE_WIDTH of
120 and a resting orbit framing radius near 24 units, so the lit cone occupies a
large fraction of the resting frame. The buoy target is a total height near 1.8
to 2.5 units and a body radius near 0.5, so the footprint is under one third of
the cone radius and the height is under one half of the cone height. The resting
scale stays 1. Hover uses a gentle lift near 1.15 in place of the current 1.4, so
hover signals selection without ballooning the marker.

### Material guidance

Keep `meshStandardMaterial`, core three only. The body uses the node color with a
moderate `roughness` near 0.6 and a low `emissiveIntensity` near 0.15 to 0.25 at
rest so it reads as a physical buoy rather than a glow source. The topmark light
keeps the node color as both color and emissive with a higher
`emissiveIntensity` near 0.5 to 0.8 so the status light stays legible. Hover
raises the emissive a step rather than the geometry size. The online and offline
color contract, `#ffcf33` and `#888`, stays exactly as computed at line 339.

## 5. SalishScene wiring seam

The single W3 editor changes only the visual primitives inside
`HydrophoneBeacon`. The exact replacement.

- Replace the cone geometry and material, lines 355 to 356, and the white stem
  mesh, lines 358 to 361, with a single `<BuoyMarker color={color} hovered={hovered} />`.
- Because a buoy is a multi-mesh group and an r3f `<mesh>` holds a single geometry
  and single material, the editor moves the `onClick`, `onPointerOver`, and
  `onPointerOut` handlers and the `scale` off the cone `<mesh>` at lines 342 to
  357 and onto the outer `<group>` at line 341, or onto a thin wrapping group
  inside the beacon, so the whole buoy stays clickable and hoverable. This stays
  inside `HydrophoneBeacon` and changes only beacon geometry, scale, material, and
  the local interaction wrapper. It touches no camera, no controls, no framing.
- Add the import at the top of the file alongside the existing
  `@/lib/scene/*` imports, `import { BuoyMarker } from "@/lib/scene/markers";`.

Prop contract preserved across the seam.

- Position stays the outer `<group position={position}>` at line 341, fed by
  `SurfaceBeacons` placement at line 404. Unchanged.
- Color stays the inline `color` computed at line 339 from `node.status`. Passed
  straight into `BuoyMarker`. Unchanged contract.
- Hover stays the local `hovered` state at line 337, set by the pointer handlers.
  Passed into `BuoyMarker`. Unchanged contract.
- `onSelect` stays wired through `SurfaceBeacons` at line 404 and the click path,
  emitting the hydrophone intent at lines 892 to 901. Unchanged.

Replace-at summary.

- Replace `web/app/components/scene/SalishScene.tsx:355-356`, the cone geometry
  and material.
- Replace `web/app/components/scene/SalishScene.tsx:358-361`, the white stem mesh.
- Relocate handlers and scale from the `<mesh>` at lines 342 to 353 to the group
  at line 341.
- Mount `<BuoyMarker color={color} hovered={hovered} />` in their place.
- Leave the `Html` hover label at lines 362 to 366 untouched.

## 6. Hard TWIN boundary

CVP changes only the beacon geometry, scale, and material so the marker reads as a
buoy. CVP introduces the net-new `web/lib/scene/markers/` module and the local
wiring seam above. CVP does not touch camera, framing, datum, tile loading, water,
re-bake, or labels. Those stay with their 3D-TWIN lanes.

- TWIN-W2.6, the sea-level datum. CVP does not touch `SEA_LEVEL_Y` at line 111,
  `TILESET_BOUNDS` at lines 93 to 98, `SCENE_DEPTH` at line 103, or the
  `worldUnitsPerMeter` fit scale.
- TWIN-W-CAM and TWIN-W-CAM-REG, the camera director and registration. CVP does
  not touch `IntentDirectorRig`, `createCameraDirector`, the resting orbit at
  lines 559 to 565, the `OrbitControls` at lines 908 to 918, or the focus journey
  path.
- TWIN-W-PERFUX-BUILD, the framing and startup build. CVP does not touch the
  resting and detail LoD caps at lines 133 to 136, `fitScaleToWidth`,
  `FULL_TILESET_URL`, the `minDistance` and `maxDistance` zoom bounds at lines 827
  to 830, or the resting orbit framing values.
- TWIN-W-LABELS, the marker labels. CVP does not touch the `Html` hover label at
  lines 362 to 366 or its `scene-beacon-label` styling.

CVP also leaves the water surface, `Water2Rig` at lines 275 to 326 and its mount
at line 858, and any re-bake of tiles or substrate, fully untouched.

## Return summary

- Findings doc, `.cca/catalogue/O0/20260628_console-visual-pass/findings/CVP-MARKER.md`.
- Buoy contract, a pure net-new `web/lib/scene/markers/buoyMarker.tsx` exporting
  `BuoyMarker({ color, hovered })` that returns a `<group>` of core three
  primitives, a short body plus a thin mast plus a small topmark light, total
  height near 1.8 to 2.5 units and body radius near 0.5, `meshStandardMaterial`
  with low body emissive and a brighter topmark light, no new dependency, no scene
  or camera reference.
- Wiring seam, replace `web/app/components/scene/SalishScene.tsx:355-356` and
  `:358-361` with `<BuoyMarker color={color} hovered={hovered} />`, relocate the
  click, hover, and scale from the `<mesh>` at lines 342 to 353 onto the group at
  line 341, preserve position, color, hover, and `onSelect`.
- TWIN boundary, CVP changes only beacon geometry, scale, and material. No camera,
  framing, datum, tile loading, water, re-bake, or label change. Lanes held off
  are TWIN-W2.6, TWIN-W-CAM and TWIN-W-CAM-REG, TWIN-W-PERFUX-BUILD, and
  TWIN-W-LABELS.
- A3 wrote exactly one file, this findings doc, and edited nothing else.

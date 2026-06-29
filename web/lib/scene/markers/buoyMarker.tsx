"use client";

// Pure react-three-fiber marker module for the hydrophone beacon (CVP lane).
// It renders a navigation buoy out of core three primitives only and adds no
// new dependency. It holds no scene/camera/controls reference, performs no
// scene mutation, owns no position, no event handlers, and no label: the
// SalishScene caller owns placement (the outer group), click/hover, and the
// Html label (TWIN-W-LABELS). The contract is color + hovered, nothing else.
//
// Buoy read replaces the old frame-dominating cone (radius 1.6, height 5, on a
// height-9 stem, ~11.5 units of combined reach): a squat floating body, a thin
// mast, and a small topmark light, ~2.2 units tall with a 0.5 body radius. The
// online/offline color contract (#ffcf33 / #888) is preserved purely by passing
// the caller's computed `color` through to both the body and the topmark light.

export interface BuoyMarkerProps {
  // Node status color computed by the caller: #ffcf33 online, #888 offline.
  color: string;
  // Hover state owned by the caller; lifts the emissive a step (not geometry).
  hovered: boolean;
}

// Emissive levels: the body reads as a physical buoy (low glow), the topmark
// light stays legible as a status light (higher glow). Hover raises each a step
// rather than ballooning the geometry, so hover signals selection cleanly.
const BODY_EMISSIVE_REST = 0.18;
const BODY_EMISSIVE_HOVER = 0.4;
const LIGHT_EMISSIVE_REST = 0.65;
const LIGHT_EMISSIVE_HOVER = 1.0;

export function BuoyMarker({ color, hovered }: BuoyMarkerProps): JSX.Element {
  return (
    <group>
      {/* Squat body floating at the surface: cylinder radius 0.5, height 0.8,
          centred at y 0.4 so its base sits at the group origin (water line). */}
      <mesh position={[0, 0.4, 0]}>
        <cylinderGeometry args={[0.5, 0.5, 0.8, 16]} />
        <meshStandardMaterial
          color={color}
          roughness={0.6}
          emissive={color}
          emissiveIntensity={hovered ? BODY_EMISSIVE_HOVER : BODY_EMISSIVE_REST}
        />
      </mesh>
      {/* Thin mast: cylinder radius 0.06, height 1.0, rising from the body top
          (y 0.8) to y 1.8. White so it reads as structure, not a status light. */}
      <mesh position={[0, 1.3, 0]}>
        <cylinderGeometry args={[0.06, 0.06, 1.0, 8]} />
        <meshStandardMaterial
          color="#ffffff"
          roughness={0.5}
          emissive={color}
          emissiveIntensity={0.2}
        />
      </mesh>
      {/* Topmark status light at the mast top (y ~1.95): sphere radius 0.22,
          carrying `color` as both color and emissive so the online/offline read
          survives at a glance. Total buoy height ~2.17 units. */}
      <mesh position={[0, 1.95, 0]}>
        <sphereGeometry args={[0.22, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={hovered ? LIGHT_EMISSIVE_HOVER : LIGHT_EMISSIVE_REST}
        />
      </mesh>
    </group>
  );
}

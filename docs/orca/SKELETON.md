# ORCA SKELETON and RIG CONTRACT

Lane: ORCA-RIG research wave (OR-R), read only. This document is the rig contract. It
describes the real killer whale (Orcinus orca) skeleton from cited anatomy references, then
maps that skeleton to a practical render armature with named degrees of freedom (DOFs) that
the biologging motion driver (ORCA-MOTION, lane OG) will address.

The single most important rig fact is stated up front. Orca swimming thrust is produced by a
DORSO-VENTRAL (up and down) oscillation of the tail flukes, driven by bending the posterior
caudal vertebral chain. This is unlike the lateral (side to side) oscillation of fish. The
fluke itself contains no bone, so all fluke motion in the rig must come from the caudal bone
chain, never from an independent boneless fluke flap and never as a lateral sway.

---

## 1. Cited anatomical write-up of the Orcinus orca skeleton

### 1.1 Skull

The orca skull has two functional parts for rig purposes. The cranium and the rostrum form a
single rigid mass (the rostrum is the elongated, telescoped snout typical of odontocetes), and
the lower jaw (mandible) articulates against the cranium at the jaw hinge. The mandible is the
only freely moving element of the skull and it opens and closes about that hinge. References:
Heyning and Dahlheim, "Orcinus orca", Mammalian Species 304, 1988, pages 1 to 9
(https://doi.org/10.2307/3504225). General odontocete cranial telescoping is summarized in
the New Bedford Whaling Museum comparative anatomy resource
(https://www.whalingmuseum.org/research/research-resources/whale-science/biology/comparative-anatomy/).

### 1.2 Vertebral column and counts

The column runs cervical, then thoracic (rib bearing), then lumbar, then caudal. Orca has the
conserved mammalian count of seven cervical vertebrae, and in adults all seven are fused into a
short block. This fusion stiffens the neck and is one reason the anterior body bends very
little while the posterior body does the swimming work.

Total vertebral count for Orcinus orca is approximately 50 to 54, and the counts vary between
individuals, so any single number is an approximation. A commonly cited regional formula is:

| Region | Count (approx) | Notes |
|---|---|---|
| Cervical (C) | 7 | all fused in adults |
| Thoracic (T) | 11 to 13 | bear the ribs |
| Lumbar (L) | 10 to 12 | elongate centra |
| Caudal (Ca) | 20 to 24 | carry the tail and support the fluke |
| Total | about 50 to 54 | varies per individual |

References for the counts and fusion: Buchholtz and Schur, "Vertebral osteology in Delphinidae
(Cetacea)", Zoological Journal of the Linnean Society 140(3), 2004, pages 383 to 401
(https://doi.org/10.1111/j.1096-3642.2003.00105.x). A specimen example is AMNH 34276 with total
count 53 and all seven cervicals fused (Buchholtz and Schur, Figure 7,
https://doi.org/10.5281/zenodo.5429021). The C7, T11 to 13, L10 to 12, Ca20 to 24 formula
summing to 50 to 54 is also reported in a comparative review of orca and horse columns (Atas de
Saude Ambiental, https://revistaseletronicas.fmu.br/index.php/ASA/article/view/1478). Note that
unlike many smaller delphinids, Orcinus orca does not show neural spine syncliny (a reversal of
spine inclination), per Buchholtz and Schur 2004.

### 1.3 Ribs

The thoracic vertebrae carry the ribs. The rib cage braces the anterior trunk and further
restricts bending there, which reinforces the functional split between a stiff front body and a
flexible tail. Reference: Fish et al., stabilization and swimming kinematics work
(https://www-dr.wcupa.edu/sciences-mathematics/biology/fFish/documents/2003MMS-Stabilization.pdf).

### 1.4 Pectoral girdle and flippers (modified forelimb)

Each pectoral flipper is a modified mammalian forelimb. The bones present are the same as a
land mammal arm and hand: scapula (the pectoral girdle element), humerus, radius, ulna,
carpals, metacarpals, and phalanges. There is no functional clavicle. Two anatomical facts
matter for the rig. First, the elbow and wrist joints are immobile (the articular facets are
flattened and the elements are effectively locked), so the flipper behaves as a single rigid
hydrofoil rather than a jointed arm. Second, orca shows extreme hyperphalangy (digits, mainly
II and III, carry six or more phalanges) that lengthens the flipper. The flipper functions for
steering, turning, and stabilization in the water column, not for propulsion. References:
Cooper et al. 2017 on flipper development and hyperphalangy in dolphins, which figures Orcinus
specifically (https://cooperbonelab.com/wp-content/uploads/2017/12/cooperetal2017cetaceanflipperevodevo.pdf).
Cooper et al. on cetacean forelimb neuromuscular anatomy and the immobile cubital (elbow) joint
(https://doi.org/10.1002/ar.20571). New Bedford Whaling Museum comparative anatomy (same URL as
1.1) on the present bone set and lack of a mobile elbow.

### 1.5 No pelvic girdle and no hind limbs

Orca has no articulated pelvic girdle and no hind limbs. Only vestigial pelvic remnants exist,
embedded in soft tissue and not articulated to the column. The rig does not include any pelvic
or hind limb bones. Reference: New Bedford Whaling Museum comparative anatomy (cetaceans lack
legs and feet, same URL as 1.1).

### 1.6 Fluke and dorsal fin (no bone) and the swimming stroke

The tail flukes are lateral extensions of the distal tail and are composed of fibrous
connective tissue with no internal bone (Felts 1966, as reported in Fish and colleagues). The
dorsal fin is likewise boneless connective tissue. Because the fluke has no skeleton, fluke
motion is produced by bending the caudal vertebral chain, not by any bone inside the fluke.

The propulsive stroke is dorso-ventral. The posterior one third of the body bends up and down,
which heaves the flukes vertically, and a pitch (angle of attack) change is superimposed at the
base of the flukes through a double hinge of the caudal vertebrae that includes the so called
ball vertebra. This is the thunniform (carangiform with lunate tail) mode shared with tuna and
lamnid sharks, except cetaceans oscillate in the vertical plane. In the stroke cycle the
peduncle leads the fluke tip in phase (the bend propagates tailward with a phase delay), and
for orca the peak to peak fluke amplitude is roughly 17 to 25 percent of body length and stays
about constant with speed while beat frequency rises with speed. References: Fish, "Comparative
kinematics and hydrodynamics of odontocete cetaceans", Journal of Experimental Biology 201,
1998, pages 2867 to 2877 (https://doi.org/10.1242/jeb.201.20.2867). Fish, "A biomechanical
perspective on the origin of cetacean flukes", 1998
(https://www.wcupa.edu/sciences-mathematics/biology/fFish/documents/1998FlukeMech.pdf), which
states the posterior one third bends dorsoventrally and the flukes pitch at a base hinge formed
by the ball vertebrae. Fish et al. fluke geometry and fibrous composition
(https://www.wcupa.edu/sciences-mathematics/biology/fFish/documents/2007AnatRec.pdf). Fish et
al. stabilization study reporting peduncle leading the flukes in phase and per body point
amplitudes (https://www-dr.wcupa.edu/sciences-mathematics/biology/fFish/documents/2003MMS-Stabilization.pdf).

---

## 2. Render armature (labelled bone hierarchy)

The armature collapses the real 50 to 54 vertebrae into a smaller number of control joints
while preserving the functional regions. The key design choice is a multi joint caudal chain so
the tail bends smoothly and drives the boneless fluke surface, plus a stiff single segment per
flipper (because the real elbow and wrist are locked), plus a separate mandible.

```text
root                         (world transform: position + body orientation)
└── hips_anchor              (rear trunk anchor; carries body_pitch/roll/yaw pivot)
    └── spine_lumbar         (lumbar block, lightly flexible)
        └── spine_thoracic   (thoracic + rib region, stiff anterior trunk)
            ├── neck_fused    (the 7 fused cervicals as one short rigid block)
            │   └── skull      (cranium + rostrum, rigid)
            │       └── jaw    (mandible, hinged: the only skull DOF)
            ├── scapula_L     (left pectoral girdle)
            │   └── pectoral_L (left flipper as one rigid hydrofoil; elbow/wrist locked)
            └── scapula_R     (right pectoral girdle)
                └── pectoral_R (right flipper as one rigid hydrofoil; elbow/wrist locked)
    └── caudal[0]            (peduncle base; start of the propulsive chain)
        └── caudal[1]
            └── caudal[2]
                └── caudal[3]
                    └── caudal[4]
                        └── caudal[5]   (fluke insertion / "ball vertebra" hinge)
                            └── fluke_surface  (boneless skinned membrane; NOT a driven bone;
                                                 it is weighted to caudal[3..5] and bends only
                                                 because those caudal bones bend)
dorsal_fin_surface          (boneless skinned membrane on spine_thoracic; not driven)
```

Notes on the hierarchy:

- The caudal chain is the propulsive element. It is a six joint chain, caudal[0] through
  caudal[5], rooted at the peduncle and ending at the fluke insertion. The fluke surface is
  skinned (weighted) to the last caudal joints and has no joint of its own, which keeps the
  anatomy honest (no bone in the fluke).
- The anterior trunk (spine_thoracic, neck_fused, skull) is intentionally stiff, matching the
  rib bracing and cervical fusion.
- Each flipper is a single rigid segment hinged at its scapula, because the real elbow and
  wrist are immobile. Individual finger or wrist joints are deliberately not modeled.
- No pelvic or hind limb bones exist in the armature, by anatomy.

---

## 3. Named degrees of freedom (DOFs) the motion driver addresses

Axis frame is defined in section 5. In short, heading is +X forward, up is +Y, and the lateral
axis is Z. All rotations follow the right hand rule about the named axis.

| DOF | Bone(s) | Rotation axis | Positive direction (right hand rule) | Sensible limit (degrees) |
|---|---|---|---|---|
| body_yaw | root / hips_anchor | world up (+Y) | nose swings from +X toward +Z (turns toward the port side) | unbounded heading, practical per turn about plus or minus 60 from current |
| body_pitch | root / hips_anchor | lateral (Z) | nose up | plus or minus 60 typical, allow plus or minus 90 for steep dives and ascents |
| body_roll | root / hips_anchor | longitudinal (+X) | dorsal surface banks toward +Z (port) | plus or minus 45 typical, allow plus or minus 90 |
| caudal[0..5] (fluke beat) | caudal chain | lateral (Z), same axis as pitch | dorso-ventral, positive bends that joint dorsally (tail tip up) | per joint, increasing tailward: caudal[0] about plus or minus 8, caudal[1] plus or minus 10, caudal[2] plus or minus 14, caudal[3] plus or minus 18, caudal[4] plus or minus 22, caudal[5] plus or minus 25 |
| pectoral_L | scapula_L / pectoral_L | see flipper sub axes below | see below | see below |
| pectoral_R | scapula_R / pectoral_R | see flipper sub axes below | see below | see below |
| jaw (optional) | jaw (mandible) | lateral (Z) | open (mandible tip swings ventrally) | 0 (closed) to about 35 (open) |

### 3.1 The caudal fluke beat (the critical DOF)

The fluke beat is a DORSO-VENTRAL oscillation, never lateral. It is applied as a pitch axis
(Z axis) rotation on each caudal joint. The beat propagates tailward with a phase delay, so
caudal[0] leads and each successive joint lags, which reproduces the real peduncle leading the
fluke tip. Per joint amplitude increases tailward (small at the peduncle, largest at the fluke
insertion), as in the amplitude table above. The fluke surface is dragged along by caudal[3..5]
because it is skinned to them, so the visible fluke heave and pitch emerge from the bone chain.

The driver sets this beat through one call, setFluke(phase, amplitude), described in section 4.
The amplitude argument scales the whole per joint amplitude profile, and the phase argument
advances the oscillation in the stroke cycle. This is the DOF the biologging accelerometer Az
oscillation maps onto.

### 3.2 Pectoral flipper articulation

Each flipper is a rigid hydrofoil hinged at the shoulder (scapula joint). It is for steering and
stabilizing, not propulsion, so it gets a small set of slow control axes rather than an
oscillation. Three sub axes per flipper:

| Flipper sub axis | Rotation axis | Positive direction | Limit (degrees) |
|---|---|---|---|
| flipper_pitch (angle of attack) | lateral (Z) | leading edge up | plus or minus 30 |
| flipper_sweep (protraction/retraction, fore-aft) | up (+Y) | trailing edge swings rearward | plus or minus 25 |
| flipper_dihedral (elevation/depression) | longitudinal (+X) | flipper tip raised away from belly | plus or minus 30 |

pectoral_L and pectoral_R each expose these three sub axes. In the data driven mode the flippers
are held near neutral or used as slow stabilizers, since the biologging stream does not carry
per flipper telemetry.

---

## 4. Proposed typed rig API (the build wave implements this)

The build wave (OR-BUILD) implements an OrcaRig object exposing the following methods. The
motion wave (OG) relies only on these signatures and on the DOF semantics above. All angles are
radians at the API boundary unless noted, and degrees are used only for the human readable
limits in this document.

```ts
interface OrcaRig {
  // Sets the whole body orientation DOFs on the root.
  // pitch -> body_pitch (about Z), roll -> body_roll (about +X), yaw -> body_yaw (about +Y).
  setOrientation(pitch: number, roll: number, yaw: number): void;

  // Drives the dorso-ventral caudal beat. phase advances the oscillation through the stroke
  // cycle (radians, wraps at 2*pi). amplitude scales the per-joint amplitude profile on
  // caudal[0..5] (0 = no beat, 1 = full nominal stroke). The beat is pitch-axis (Z) on the
  // caudal chain and propagates tailward with a fixed per-joint phase delay. This is the only
  // call that animates the fluke, and the fluke surface follows because it is skinned to the
  // caudal tip.
  setFluke(phase: number, amplitude: number): void;

  // Places the body vertically and optionally adjusts dive posture. depthMeters maps to world
  // Y on the twin datum (NAVD88 0 m == scene Y 0), scaled by worldUnitsPerMeter. This is a
  // TRANSLATION of the root, not a bone rotation. Optional descent/ascent posture can bias
  // body_pitch but the canonical pitch still comes from setOrientation.
  setDepthPose(depthMeters: number, opts?: { pitchBias?: number }): void;

  // Sets the steering flippers. Each side takes the three flipper sub axes from section 3.2.
  // Defaults hold the flippers near neutral when telemetry does not drive them.
  setPectoral(
    side: "L" | "R",
    pose: { pitch?: number; sweep?: number; dihedral?: number }
  ): void;

  // Optional. Opens/closes the mandible about the jaw hinge (Z axis). 0 = closed.
  setJaw?(openRadians: number): void;
}
```

Mapping of API to DOFs:

- setOrientation sets body_pitch, body_roll, body_yaw on the root.
- setFluke drives the caudal[0..5] dorso-ventral oscillation (the fluke beat).
- setDepthPose translates the root along world Y from depth and may add a small pitch bias.
- setPectoral sets the pectoral_L or pectoral_R sub axes (steering/stabilizing).
- setJaw (optional) opens the mandible.

---

## 5. Axis and frame convention

The scene is three.js style y-up and right handed. The locked convention is:

- +X is forward (heading, the direction the rostrum points).
- +Y is up (world vertical, and the axis depth maps onto as world Y).
- Z is the lateral axis. With a right handed frame and +X forward, +Y up, the cross product
  X cross Y gives +Z, which points to the animal's port (left) side. So +Z is left (port) and
  -Z is right (starboard).

Rotation sign uses the right hand rule about each named axis:

- body_yaw about +Y, positive turns the nose from +X toward +Z (toward port).
- body_pitch about Z, positive is nose up.
- body_roll about +X, positive banks the dorsal surface toward +Z (port side, that is a left
  bank).
- The caudal fluke beat uses the same Z (pitch) axis as body_pitch, which is exactly why the
  beat is dorso-ventral and not lateral.

This frame is stated explicitly so the motion wave's sensor mapping can align tag axes to scene
axes.

---

## 6. Consistency with the ORCA-MOTION (OG) sensor mapping

The sibling motion wave maps biologging sensor channels onto these exact DOFs. The locked
mapping and the DOF it targets in this document are:

| Sensor channel (OG) | DOF in this document | How it is applied |
|---|---|---|
| heading | body_yaw | setOrientation yaw, rotation about world up (+Y) |
| pitch | body_pitch | setOrientation pitch, rotation about lateral Z, nose up positive |
| roll | body_roll | setOrientation roll, rotation about longitudinal +X, bank into turns |
| depth (from pressure) | world Y position (not a bone) | setDepthPose translates the root along world Y on the twin datum |
| accelerometer Az oscillation | caudal[0..5] fluke beat | setFluke(phase, amplitude), dorso-ventral pitch-axis oscillation on the caudal chain |
| dive/foraging context (optional) | speed/behavior tint | not a skeletal DOF, optional labeled hint |

The names and semantics match the OG mapping exactly. Depth is a vertical translation along
world Y, not a bone rotation. The fluke beat is dorso-ventral, driven by the caudal bone chain
through setFluke, and is never a lateral sway and never an independent boneless fluke flap.

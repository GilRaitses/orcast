// Turn BAM's precomputed acoustic classification into a multi-orca spawn record.
//
// Honest rules (R05/R08, locked):
//  - ACOUSTIC presence/count decides WHETHER and HOW MANY orcas spawn and the
//    HUD label. It NEVER decides the trajectory or which behavior clip plays.
//  - The spawn count is exactly what BAM's estimate supports, capped at nMax.
//    With the current presence-only model that is 0 or 1; the model does not
//    claim a whale count, so this code never invents one.
//  - WHICH behavior clip each orca plays is a KINEMATIC choice from the ethogram
//    (R04), disclosed as a modeled match, never driven by the acoustic output.
//
// `demoCountOverride` exists ONLY for the sandbox to exercise the multi-orca rig
// at nMax. It is stamped `capability_demo` and labeled on-screen as NOT a model
// estimate, so breadth can be shown without overclaiming the classifier.

import {
  buildEthogram,
  type EthogramEntry,
} from "@/lib/scene/orca/motion/clips/ethogram";
import type {
  AcousticClassificationRecord,
  BehaviorClassId,
  BehaviorMotionClip,
  ClipManifest,
  OrcaSpawnInstance,
  ReenactmentSpawnRecord,
  SpawnCountBasis,
} from "./types";

export interface SpawnOptions {
  anchor: { lat: number; lng: number };
  /** Force one behavior clip for all instances (by clip id or behavior name). */
  clipId?: string;
  /** Restrict the breadth rotation to these behavior classes, in order. */
  behaviorClasses?: BehaviorClassId[];
  nMax?: number; // hard cap; R08 default 3
  bodyScale?: number;
  /** Per-instance modeled offset step (seconds) into the shared clip window so
   * multiple orcas do not move in perfect lockstep. Default 7. */
  phaseOffsetStepS?: number;
  /** SANDBOX ONLY: force a spawn count to exercise the rig. Explicitly NOT a
   * model estimate; the record is stamped `capability_demo`. */
  demoCountOverride?: number;
}

/** Back-compat single-clip chooser (kept for callers that pick one clip). */
export function chooseClip(manifest: ClipManifest, clipId?: string): BehaviorMotionClip {
  if (clipId) {
    const hit = manifest.clips.find((c) => c.id === clipId || c.behaviorName === clipId);
    if (hit) return hit;
  }
  return manifest.clips[0] ?? manifest.fallback;
}

function countBasisLabel(basis: SpawnCountBasis, count: number, nMax: number): string {
  switch (basis) {
    case "count_head":
      return `Model count estimate. Showing ${count} within the cap of ${nMax}.`;
    case "capped_fallback":
      return `Capped fallback. Showing ${count} within the cap of ${nMax}.`;
    case "capability_demo":
      return `Capability demo. ${count} orcas is not a model estimate. The classifier resolves presence only, not count.`;
    case "presence_only":
    default:
      return `Model estimate is presence only. Count is not claimed by the classifier. Showing ${count} from presence.`;
  }
}

export function buildSpawnRecord(
  classification: AcousticClassificationRecord,
  manifest: ClipManifest,
  opts: SpawnOptions,
): ReenactmentSpawnRecord {
  const nMax = opts.nMax ?? 3;
  const phaseStep = opts.phaseOffsetStepS ?? 7;

  let count: number;
  let basis: SpawnCountBasis;
  if (opts.demoCountOverride != null) {
    count = Math.min(nMax, Math.max(0, Math.floor(opts.demoCountOverride)));
    basis = "capability_demo";
  } else {
    count = Math.min(nMax, Math.max(0, classification.summary.spawnCount));
    basis = classification.summary.spawnCountBasis;
  }

  const ethogram = buildEthogram(manifest);
  const entries: EthogramEntry[] = ethogram.assign(count, {
    fixedId: opts.clipId,
    behaviorClasses: opts.behaviorClasses,
    policy: opts.clipId ? "fixed" : "distinct",
  });

  const conf = classification.summary.meanConfidence;

  const instances: OrcaSpawnInstance[] = [];
  for (let i = 0; i < count; i++) {
    const entry = entries[i] ?? ethogram.fallback;
    // Centered, readable ~8 m lateral spacing with a slight depth stagger (R08).
    const lateral = (i - (count - 1) / 2) * 8;
    const stagger = (i % 2) * 4;
    instances.push({
      instanceId: `${classification.clipId}-orca-${i}`,
      anchor: opts.anchor,
      sceneOffsetM: { x: lateral, z: stagger },
      clip: entry.clip,
      behaviorLabel: entry.modeledLabel,
      phaseOffsetS: i * phaseStep,
      acousticLabel: {
        text: `estimated SRKW call present, confidence ${(conf * 100).toFixed(0)} percent`,
        confidence: conf,
      },
      bodyScale: opts.bodyScale,
    });
  }

  return {
    classification,
    instances,
    timelineDurationS: classification.audio.durationS,
    countBasis: basis,
    countBasisLabel: countBasisLabel(basis, count, nMax),
    honesty: {
      motion: "measured_srkw_dtag",
      spawn: "modeled_3d_placement",
      crossSensor: "illustrative",
      representativeness: classification.honesty.representativeness,
    },
  };
}

/** Presence + confidence at a playhead second (for presence-gated visibility
 * and a live HUD readout). Returns the window covering `t`. */
export function presenceAtTime(
  classification: AcousticClassificationRecord,
  t: number,
): { presence: boolean; confidence: number } {
  const w = classification.windows;
  if (w.length === 0) return { presence: false, confidence: 0 };
  // windows are hop-spaced; pick the nearest covering window.
  let best = w[0];
  for (const win of w) {
    if (t >= win.tStartS && t < win.tEndS) {
      best = win;
      break;
    }
    if (Math.abs((win.tStartS + win.tEndS) / 2 - t) <
        Math.abs((best.tStartS + best.tEndS) / 2 - t)) {
      best = win;
    }
  }
  return { presence: best.presence, confidence: best.presenceConfidence };
}

// Turn BAM's precomputed acoustic classification into a spawn record. Honest
// rules (R05/R08): acoustic PRESENCE decides WHETHER an orca spawns and the HUD
// label; it never decides the trajectory. With a presence-only model the spawn
// count is 0 or 1 (capped); there is no count claim.

import type {
  AcousticClassificationRecord,
  BehaviorMotionClip,
  ClipManifest,
  OrcaSpawnInstance,
  ReenactmentSpawnRecord,
} from "./types";

export interface SpawnOptions {
  anchor: { lat: number; lng: number };
  /** Which measured behavior clip the spawned orca plays (modeled UX choice). */
  clipId?: string;
  nMax?: number; // hard cap; R08 default 3
  bodyScale?: number;
}

export function chooseClip(manifest: ClipManifest, clipId?: string): BehaviorMotionClip {
  if (clipId) {
    const hit = manifest.clips.find((c) => c.id === clipId || c.behaviorName === clipId);
    if (hit) return hit;
  }
  return manifest.clips[0] ?? manifest.fallback;
}

export function buildSpawnRecord(
  classification: AcousticClassificationRecord,
  manifest: ClipManifest,
  opts: SpawnOptions,
): ReenactmentSpawnRecord {
  const nMax = opts.nMax ?? 3;
  const count = Math.min(nMax, Math.max(0, classification.summary.spawnCount));
  const clip = chooseClip(manifest, opts.clipId);
  const conf = classification.summary.meanConfidence;

  const instances: OrcaSpawnInstance[] = [];
  for (let i = 0; i < count; i++) {
    instances.push({
      instanceId: `${classification.clipId}-orca-${i}`,
      anchor: opts.anchor,
      sceneOffsetM: { x: i * 8, z: i * 4 }, // ~8 m readable spacing (R08)
      clip,
      acousticLabel: {
        text: `estimated: SRKW call present (confidence ${(conf * 100).toFixed(0)}%)`,
        confidence: conf,
      },
      bodyScale: opts.bodyScale,
    });
  }

  return {
    classification,
    instances,
    timelineDurationS: classification.audio.durationS,
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

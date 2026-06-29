// TimelineDriver: binds BSH's scene-time authority to the orca pool. It reads
// the authoritative playhead each frame (it does NOT run its own clock), gates
// orca visibility by the acoustic presence estimate at the playhead, and drives
// every instance from the measured SRKW telemetry at the clip sample time.
//
// Scrub seeks both audio and reenactment (currentTimeS jumps). Slow-mo lowers
// the authority playbackRate, which slows how fast currentTimeS advances, so
// the reenactment slows in lockstep without BRE rescaling time.

import * as THREE from "three";
import type { OrcaPool } from "./OrcaPool";
import { presenceAtTime } from "./spawnFromClassification";
import type {
  AcousticClassificationRecord,
  ReenactmentTimeline,
} from "./types";

export interface TimelineDriverState {
  currentTimeS: number;
  presence: boolean;
  confidence: number;
  hudLabel: string;
}

export interface TimelineDriver {
  /** Call inside the render loop (r3f useFrame). */
  update(dt: number, cameraWorldPos: THREE.Vector3 | null): void;
  getState(): Readonly<TimelineDriverState>;
  dispose(): void;
}

export interface TimelineDriverOptions {
  /** Hide the orca when the acoustic estimate says no SRKW call at the playhead. */
  presenceGated?: boolean;
}

export function createTimelineDriver(
  timeline: ReenactmentTimeline,
  pool: OrcaPool,
  classification: AcousticClassificationRecord,
  opts: TimelineDriverOptions = {},
): TimelineDriver {
  const presenceGated = opts.presenceGated ?? true;
  const state: TimelineDriverState = {
    currentTimeS: timeline.currentTimeS,
    presence: false,
    confidence: 0,
    hudLabel: "",
  };

  // Subscribe only to keep a fresh snapshot; the actual drive runs per frame.
  const unsub = timeline.subscribe((s) => {
    state.currentTimeS = s.currentTimeS;
  });

  function update(dt: number, cam: THREE.Vector3 | null): void {
    const t = timeline.currentTimeS;
    state.currentTimeS = t;
    const { presence, confidence } = presenceAtTime(classification, t);
    state.presence = presence;
    state.confidence = confidence;
    state.hudLabel = presence
      ? `estimated: SRKW call present (confidence ${(confidence * 100).toFixed(0)}%)`
      : "estimated: no SRKW call in this window";
    if (presenceGated) pool.setVisible(presence);
    pool.update(dt, t, cam);
  }

  return {
    update,
    getState() {
      return state;
    },
    dispose() {
      unsub();
    },
  };
}

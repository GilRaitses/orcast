// OrcaPool: spawn and drive N orca instances for the reenactment. Each instance
// is a real OrcaController driven by the measured SRKW DTAG driver; the pool
// only adds scene placement + per-instance clip sample time. No fabricated
// motion. The pool supports N<=nMax (R08 cap 3).
//
// Perf note: this uses createOrcaController per instance (the tested path), so
// each instance loads the mesh + driver once at spawn. The R08 shared-asset
// optimization (one loadOrcaMesh + one makeOrcaMaterial + one BiologgingTrack
// shared across rigs) requires createOrcaController to accept preloaded assets,
// which lives in the ORCA-owned stack (web/lib/scene/orca/OrcaController.ts) and
// is a serialized, O0-coordinated change. It is deferred to BRE-INTEGRATE and
// flagged; for nMax=3 the per-frame cost is N rig skinning passes either way,
// and the only saving is one-time spawn load + memory.

import * as THREE from "three";
import {
  createOrcaController,
  REAL_SRKW_MOTION_URL,
  type OrcaController,
  type WfxEnvHandle,
} from "@/lib/scene/orca";
import { projectToScene, type HeightmapBounds } from "@/lib/sceneIntent";
import { clipSampleTime } from "@/lib/scene/orca/motion/clips/clipSampleTime";
import type { OrcaSpawnInstance, ReenactmentSpawnRecord } from "./types";

export interface OrcaPoolOptions {
  env: WfxEnvHandle;
  bounds: HeightmapBounds;
  sceneDepth: number;
  worldUnitsPerMeter: number;
  depthScale?: number;
}

interface PooledOrca {
  spec: OrcaSpawnInstance;
  wrapper: THREE.Group; // positioned at the anchor; controller.root parented here
  controller: OrcaController;
}

/** Per-instance HUD readout. Behavior label is a disclosed modeled match; the
 * acoustic label is HUD-only and never affects kinematics. */
export interface OrcaInstanceLabel {
  instanceId: string;
  behaviorName: string;
  behaviorLabel: string;
  acoustic?: string;
}

export interface OrcaPool {
  group: THREE.Group;
  /** (Re)spawn from a classification-derived record. */
  setSpawn(record: ReenactmentSpawnRecord): Promise<void>;
  /** Advance all instances to the timeline playhead (seconds). */
  update(dt: number, currentTimeS: number, cameraWorldPos: THREE.Vector3 | null): void;
  /** Show/hide all instances (presence-gated visibility). */
  setVisible(v: boolean): void;
  count(): number;
  /** Per-instance behavior + acoustic labels for the HUD. */
  instanceLabels(): OrcaInstanceLabel[];
  dispose(): void;
}

export function createOrcaPool(opts: OrcaPoolOptions): OrcaPool {
  const group = new THREE.Group();
  group.name = "bsw-reenactment-pool";
  const wupm = opts.worldUnitsPerMeter;
  const depthScale = opts.depthScale ?? 1;
  let pooled: PooledOrca[] = [];

  function clearPool() {
    for (const p of pooled) {
      group.remove(p.wrapper);
      p.controller.dispose();
    }
    pooled = [];
  }

  async function setSpawn(record: ReenactmentSpawnRecord): Promise<void> {
    clearPool();
    const built = await Promise.all(
      record.instances.map(async (spec) => {
        const controller = await createOrcaController({
          env: opts.env,
          motionUrl: REAL_SRKW_MOTION_URL, // ALWAYS the real SRKW driver
          worldUnitsPerMeter: wupm,
          depthScale,
          timeScale: 1,
        });
        const [ax, az] = projectToScene(
          spec.anchor.lat, spec.anchor.lng, opts.bounds, opts.sceneDepth,
        );
        const ox = (spec.sceneOffsetM?.x ?? 0) * wupm;
        const oz = (spec.sceneOffsetM?.z ?? 0) * wupm;
        const wrapper = new THREE.Group();
        wrapper.position.set(ax + ox, 0, az + oz);
        if (spec.bodyScale) wrapper.scale.setScalar(spec.bodyScale);
        wrapper.add(controller.root);
        return { spec, wrapper, controller } as PooledOrca;
      }),
    );
    for (const p of built) group.add(p.wrapper);
    pooled = built;
  }

  function update(dt: number, currentTimeS: number, cam: THREE.Vector3 | null): void {
    const d = Math.min(dt, 1 / 30);
    for (const p of pooled) {
      // Map the audio playhead into the measured clip window. currentTimeS is
      // already advanced at the timeline playbackRate, so do NOT scale again.
      // phaseOffsetS samples a different REAL moment of the driver per instance.
      const elapsed = clipSampleTime(currentTimeS, p.spec.clip, p.spec.phaseOffsetS ?? 0);
      p.controller.update(d, elapsed, cam);
    }
  }

  return {
    group,
    setSpawn,
    update,
    setVisible(v) {
      group.visible = v;
    },
    count() {
      return pooled.length;
    },
    instanceLabels() {
      return pooled.map((p) => ({
        instanceId: p.spec.instanceId,
        behaviorName: p.spec.clip.behaviorName,
        behaviorLabel: p.spec.behaviorLabel ?? "",
        acoustic: p.spec.acousticLabel?.text,
      }));
    },
    dispose() {
      clearPool();
    },
  };
}

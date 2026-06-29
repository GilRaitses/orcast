// Map a timeline playhead second to a sample time INSIDE a behavior clip window.
// The result is always a real time into the measured SRKW driver, so the pose
// returned by track.sample() is measured telemetry, never synthesized.

import type { BehaviorMotionClip } from "@/lib/scene/reenactment/types";

/**
 * For a clip [t0,t1], fold the playhead `t` into the window. Looping clips wrap;
 * non-looping clips clamp to the window end. When no clip window is given the
 * playhead passes through unchanged (continuous-driver fallback).
 */
export function clipSampleTime(t: number, clip?: BehaviorMotionClip | null): number {
  if (!clip) return t;
  const span = clip.t1_s - clip.t0_s;
  if (span <= 0) return clip.t0_s;
  if (!clip.loop) return clip.t0_s + Math.min(Math.max(0, t), span);
  const m = ((t % span) + span) % span;
  return clip.t0_s + m;
}

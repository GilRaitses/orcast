// Frame-time A/B harness for the spectrogram HUD + interpretive ocean layer.
//
// It samples requestAnimationFrame intervals over a fixed wall-clock window and
// reports mean / p95 / max frame time and an estimated fps. runFrameTimeAB runs
// a list of named conditions STRICTLY SERIALLY (each condition fully settles and
// is measured before the next starts), because concurrent GL contexts corrupt
// frame timing. The caller supplies setup/teardown closures that flip the HUD or
// the ocean layer on/off between conditions.
//
// This module only MEASURES; it never asserts a verdict. The real numbers come
// from running it on the isolated GPU host (the O0-gated capture step). Off the
// GPU host it still type-checks and runs, but the numbers are not authoritative.

/** Desktop and laptop frame budgets the A/B is judged against. */
export interface FrameBudget {
  label: string;
  targetFps: number;
  budgetMs: number;
}

export const FRAME_BUDGETS: { desktop: FrameBudget; laptop: FrameBudget } = {
  desktop: { label: "60 fps desktop", targetFps: 60, budgetMs: 1000 / 60 },
  laptop: { label: "30 fps laptop", targetFps: 30, budgetMs: 1000 / 30 },
};

export interface FrameTimeStats {
  /** Number of frame intervals sampled. */
  frames: number;
  meanMs: number;
  p95Ms: number;
  maxMs: number;
  minMs: number;
  /** Estimated sustained fps from the mean interval. */
  estFps: number;
}

function summarize(intervals: number[]): FrameTimeStats {
  if (intervals.length === 0) {
    return { frames: 0, meanMs: 0, p95Ms: 0, maxMs: 0, minMs: 0, estFps: 0 };
  }
  const sorted = [...intervals].sort((a, b) => a - b);
  const sum = sorted.reduce((s, v) => s + v, 0);
  const mean = sum / sorted.length;
  const p95 = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))];
  return {
    frames: sorted.length,
    meanMs: mean,
    p95Ms: p95,
    maxMs: sorted[sorted.length - 1],
    minMs: sorted[0],
    estFps: mean > 0 ? 1000 / mean : 0,
  };
}

/**
 * Sample frame intervals for `durationMs` of wall-clock time. A short warmup is
 * discarded so the first scheduling hiccup does not skew the mean. Resolves with
 * the summary once the window elapses.
 */
export function measureFrameTimes(
  durationMs = 2000,
  opts: { warmupFrames?: number } = {},
): Promise<FrameTimeStats> {
  const warmup = opts.warmupFrames ?? 5;
  return new Promise((resolve) => {
    if (typeof requestAnimationFrame === "undefined" || typeof performance === "undefined") {
      resolve(summarize([]));
      return;
    }
    const intervals: number[] = [];
    let last = performance.now();
    const start = last;
    let frame = 0;
    const tick = (now: number) => {
      const dt = now - last;
      last = now;
      frame++;
      if (frame > warmup) intervals.push(dt);
      if (now - start >= durationMs) {
        resolve(summarize(intervals));
        return;
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

export interface ABCondition {
  /** Short condition label, e.g. "hud+ocean" or "baseline". */
  label: string;
  /** Apply this condition (toggle HUD / ocean layer). May be async. */
  setup: () => void | Promise<void>;
  /** Undo the condition before the next one runs. */
  teardown?: () => void | Promise<void>;
}

export interface ABResult {
  label: string;
  stats: FrameTimeStats;
  /** True if the mean frame time fits inside the budget. */
  withinDesktop: boolean;
  withinLaptop: boolean;
}

/**
 * Run each condition serially: setup, settle, measure, teardown, then the next.
 * Conditions never overlap, so the per-condition numbers are comparable.
 */
export async function runFrameTimeAB(
  conditions: ABCondition[],
  opts: { perConditionMs?: number; settleMs?: number } = {},
): Promise<ABResult[]> {
  const perConditionMs = opts.perConditionMs ?? 2000;
  const settleMs = opts.settleMs ?? 250;
  const results: ABResult[] = [];
  for (const cond of conditions) {
    await cond.setup();
    if (settleMs > 0) await new Promise((r) => setTimeout(r, settleMs));
    const stats = await measureFrameTimes(perConditionMs);
    await cond.teardown?.();
    results.push({
      label: cond.label,
      stats,
      withinDesktop: stats.meanMs <= FRAME_BUDGETS.desktop.budgetMs,
      withinLaptop: stats.meanMs <= FRAME_BUDGETS.laptop.budgetMs,
    });
  }
  return results;
}

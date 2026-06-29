// Axis-tick math for the spectrogram HUD. Pure functions: they take a span and a
// target tick count and return ticks at "nice" round values (1/2/5 x 10^n) with
// their fractional position along the axis. The HUD turns these into pixel
// positions and labels. No DOM, no canvas; trivially testable.

export interface AxisTick {
  /** Position along the axis in [0,1] (0 = start, 1 = end). */
  frac: number;
  /** Value at this tick in axis units (Hz for frequency, seconds for time). */
  value: number;
  /** Formatted label, e.g. "12k" or "30s". */
  label: string;
}

/** Pick a "nice" step (1, 2, or 5 times a power of ten) near span/target. */
function niceStep(span: number, target: number): number {
  if (span <= 0 || target <= 0) return 1;
  const rough = span / target;
  const mag = Math.pow(10, Math.floor(Math.log10(rough)));
  const norm = rough / mag;
  let nice: number;
  if (norm < 1.5) nice = 1;
  else if (norm < 3) nice = 2;
  else if (norm < 7) nice = 5;
  else nice = 10;
  return nice * mag;
}

function formatHz(hz: number): string {
  if (hz >= 1000) {
    const k = hz / 1000;
    return `${Number.isInteger(k) ? k.toFixed(0) : k.toFixed(1)}k`;
  }
  return `${Math.round(hz)}`;
}

function formatSeconds(s: number): string {
  if (s >= 100) return `${Math.round(s)}s`;
  if (Number.isInteger(s)) return `${s.toFixed(0)}s`;
  return `${s.toFixed(1)}s`;
}

/**
 * Frequency ticks from 0 to nyquistHz. frac 0 is the bottom of the canvas (low
 * frequency), frac 1 the top (Nyquist), matching the rgba image whose row 0 is
 * the highest frequency.
 */
export function frequencyTicks(nyquistHz: number, targetCount = 5): AxisTick[] {
  if (!(nyquistHz > 0)) return [];
  const step = niceStep(nyquistHz, targetCount);
  const ticks: AxisTick[] = [];
  for (let hz = 0; hz <= nyquistHz + 1e-6; hz += step) {
    ticks.push({ frac: hz / nyquistHz, value: hz, label: formatHz(hz) });
  }
  return ticks;
}

/** Time ticks from 0 to durationS, left (frac 0) to right (frac 1). */
export function timeTicks(durationS: number, targetCount = 6): AxisTick[] {
  if (!(durationS > 0)) return [];
  const step = niceStep(durationS, targetCount);
  const ticks: AxisTick[] = [];
  for (let s = 0; s <= durationS + 1e-6; s += step) {
    ticks.push({ frac: s / durationS, value: s, label: formatSeconds(s) });
  }
  return ticks;
}

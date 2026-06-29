// Shared magma-style colormap for the STFT spectrogram. The off-thread bake
// (stft.worker.ts) and the on-screen legend (legend.ts) both build from these
// stops so the legend swatch is guaranteed to match the rendered spectrogram.
//
// black -> deep purple -> magenta -> orange -> pale yellow, linearly interpolated
// into a 256-entry RGB LUT.

export type ColorStop = readonly [pos: number, r: number, g: number, b: number];

export const MAGMA_STOPS: readonly ColorStop[] = [
  [0.0, 0, 0, 4],
  [0.15, 28, 16, 68],
  [0.35, 79, 18, 123],
  [0.55, 137, 34, 106],
  [0.75, 205, 64, 67],
  [0.9, 247, 144, 60],
  [1.0, 252, 253, 191],
];

/** Build a 256x3 (RGB) LUT by linear interpolation between the stops. */
export function buildMagmaLut(stops: readonly ColorStop[] = MAGMA_STOPS): Uint8Array {
  const lut = new Uint8Array(256 * 3);
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    let s = 0;
    while (s < stops.length - 2 && t > stops[s + 1][0]) s++;
    const [t0, r0, g0, b0] = stops[s];
    const [t1, r1, g1, b1] = stops[s + 1];
    const f = t1 > t0 ? (t - t0) / (t1 - t0) : 0;
    lut[i * 3] = Math.round(r0 + (r1 - r0) * f);
    lut[i * 3 + 1] = Math.round(g0 + (g1 - g0) * f);
    lut[i * 3 + 2] = Math.round(b0 + (b1 - b0) * f);
  }
  return lut;
}

/** Sample the LUT at a normalized [0,1] position, returning [r,g,b] 0-255. */
export function sampleMagma(norm: number, lut: Uint8Array = buildMagmaLut()): [number, number, number] {
  let n = norm;
  if (n < 0) n = 0;
  else if (n > 1) n = 1;
  const ci = Math.round(n * 255) * 3;
  return [lut[ci], lut[ci + 1], lut[ci + 2]];
}

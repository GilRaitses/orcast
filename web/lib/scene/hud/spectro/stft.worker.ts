// Dedicated module Worker: bakes a Short-Time Fourier Transform spectrogram from
// a mono Float32Array channel of REAL clip audio, OFF the main thread. After the
// one-shot bake it costs the r3f loop 0 ms/frame. No external dependency: the FFT
// is an inline iterative radix-2 Cooley-Tukey transform.
//
// Message in:  { channel: Float32Array, sampleRate, fftSize, hopSize }
// Message out: { magnitudes: Float32Array, rgba: Uint8ClampedArray,
//                freqBins, timeBins, hopS }
//
// magnitudes layout: row-major [timeBin * freqBins + freqBin], value is power in
//   dB (10*log10(power)), freqBin 0 = DC, freqBin freqBins-1 = just below Nyquist.
// rgba layout: an image of width=timeBins, height=freqBins. Row 0 is the HIGHEST
//   frequency (top of the canvas), so drawImage renders low freq at the bottom.
//
// The DOM `lib` is the one configured for this project, so the worker global is
// reached through a narrow typed cast rather than the conflicting webworker lib.

import { buildMagmaLut } from "./colormap";

// Dynamic range mapped to the full colormap: 80 dB below the loudest bin so real
// SRKW call structure stays visible regardless of clip gain. The legend reads it.
const DYNAMIC_RANGE_DB = 80;

interface StftRequest {
  channel: Float32Array;
  sampleRate: number;
  fftSize: number;
  hopSize: number;
}

interface StftResponse {
  magnitudes: Float32Array;
  rgba: Uint8ClampedArray;
  freqBins: number;
  timeBins: number;
  hopS: number;
  // Adaptive normalization range used to build rgba: dbCeil is the loudest bin,
  // dbFloor = dbCeil - dynamicRangeDb. The legend keys its dB labels to these.
  dbCeil: number;
  dbFloor: number;
  dynamicRangeDb: number;
}

const ctx = self as unknown as {
  onmessage: ((ev: MessageEvent<StftRequest>) => void) | null;
  postMessage(message: StftResponse, transfer: Transferable[]): void;
};

// Iterative in-place radix-2 FFT. re/im are length-n (n a power of two) and are
// overwritten with the transform. Bit-reversal permutation, then log2(n) butterfly
// stages with precomputed-per-stage twiddles.
function fftRadix2(re: Float32Array, im: Float32Array, n: number): void {
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      const tr = re[i];
      re[i] = re[j];
      re[j] = tr;
      const ti = im[i];
      im[i] = im[j];
      im[j] = ti;
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const half = len >> 1;
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang);
    const wi = Math.sin(ang);
    for (let start = 0; start < n; start += len) {
      let curR = 1;
      let curI = 0;
      for (let k = 0; k < half; k++) {
        const aIdx = start + k;
        const bIdx = aIdx + half;
        const br = re[bIdx] * curR - im[bIdx] * curI;
        const bi = re[bIdx] * curI + im[bIdx] * curR;
        re[bIdx] = re[aIdx] - br;
        im[bIdx] = im[aIdx] - bi;
        re[aIdx] += br;
        im[aIdx] += bi;
        const nextR = curR * wr - curI * wi;
        curI = curR * wi + curI * wr;
        curR = nextR;
      }
    }
  }
}

function computeStft(req: StftRequest): StftResponse {
  const { channel, sampleRate, fftSize, hopSize } = req;
  const freqBins = fftSize >> 1;
  const n = channel.length;
  const timeBins = n >= fftSize ? Math.floor((n - fftSize) / hopSize) + 1 : 0;
  const hopS = hopSize / sampleRate;

  // Periodic Hann window.
  const window = new Float32Array(fftSize);
  for (let i = 0; i < fftSize; i++) {
    window[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / fftSize);
  }

  const magnitudes = new Float32Array(timeBins * freqBins);
  const re = new Float32Array(fftSize);
  const im = new Float32Array(fftSize);

  let maxDb = -Infinity;
  for (let t = 0; t < timeBins; t++) {
    const offset = t * hopSize;
    for (let i = 0; i < fftSize; i++) {
      re[i] = channel[offset + i] * window[i];
      im[i] = 0;
    }
    fftRadix2(re, im, fftSize);
    const base = t * freqBins;
    for (let f = 0; f < freqBins; f++) {
      const power = re[f] * re[f] + im[f] * im[f];
      const db = 10 * Math.log10(power + 1e-12);
      magnitudes[base + f] = db;
      if (db > maxDb) maxDb = db;
    }
  }

  // Adaptive normalization: 80 dB of dynamic range below the loudest bin maps to
  // the full colormap so real SRKW call structure is visible regardless of clip gain.
  const dbCeil = Number.isFinite(maxDb) ? maxDb : 0;
  const dbFloor = dbCeil - DYNAMIC_RANGE_DB;
  const span = dbCeil - dbFloor;
  const lut = buildMagmaLut();
  const rgba = new Uint8ClampedArray(timeBins * freqBins * 4);
  for (let t = 0; t < timeBins; t++) {
    const base = t * freqBins;
    for (let f = 0; f < freqBins; f++) {
      let norm = (magnitudes[base + f] - dbFloor) / span;
      if (norm < 0) norm = 0;
      else if (norm > 1) norm = 1;
      const ci = Math.round(norm * 255) * 3;
      // Row 0 = highest freq -> place freqBin f at row (freqBins-1-f).
      const px = ((freqBins - 1 - f) * timeBins + t) * 4;
      rgba[px] = lut[ci];
      rgba[px + 1] = lut[ci + 1];
      rgba[px + 2] = lut[ci + 2];
      rgba[px + 3] = 255;
    }
  }

  return {
    magnitudes,
    rgba,
    freqBins,
    timeBins,
    hopS,
    dbCeil,
    dbFloor,
    dynamicRangeDb: DYNAMIC_RANGE_DB,
  };
}

ctx.onmessage = (ev: MessageEvent<StftRequest>) => {
  const result = computeStft(ev.data);
  ctx.postMessage(result, [result.magnitudes.buffer, result.rgba.buffer]);
};

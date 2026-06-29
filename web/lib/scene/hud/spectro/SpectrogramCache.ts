// Holds the baked STFT and implements the read-only SpectrogramFeatures view that
// the acoustic lane consumes. The rgba image is kept for the HUD to draw once.

import type { SpectrogramFeatures } from "./types";

export interface SpectrogramCacheInit {
  rgba: Uint8ClampedArray; // image, width=timeBins, height=freqBins, row 0 = highest freq
  magnitudes: Float32Array; // [timeBin * freqBins + freqBin], power in dB
  sampleRate: number;
  hopS: number; // seconds per time bin (hopSize / sampleRate)
  fftSize: number;
  freqBins: number;
  timeBins: number;
}

export class SpectrogramCache implements SpectrogramFeatures {
  readonly rgba: Uint8ClampedArray;
  readonly magnitudes: Float32Array;
  readonly sampleRate: number;
  readonly hopS: number;
  readonly fftSize: number;
  readonly freqBins: number;
  readonly timeBins: number;

  /** Image dimensions for the HUD: width spans time, height spans frequency. */
  readonly width: number;
  readonly height: number;

  constructor(init: SpectrogramCacheInit) {
    this.rgba = init.rgba;
    this.magnitudes = init.magnitudes;
    this.sampleRate = init.sampleRate;
    this.hopS = init.hopS;
    this.fftSize = init.fftSize;
    this.freqBins = init.freqBins;
    this.timeBins = init.timeBins;
    this.width = init.timeBins;
    this.height = init.freqBins;
  }

  get hopSize(): number {
    return Math.round(this.hopS * this.sampleRate);
  }

  /** Map a scene time in seconds to the nearest STFT column index, clamped. */
  timeToBin(t: number): number {
    if (this.timeBins <= 0 || this.hopS <= 0) return 0;
    const bin = Math.floor(t / this.hopS);
    if (bin < 0) return 0;
    if (bin > this.timeBins - 1) return this.timeBins - 1;
    return bin;
  }

  /** Total spectrogram time span in seconds. */
  get spanS(): number {
    return this.timeBins * this.hopS;
  }
}

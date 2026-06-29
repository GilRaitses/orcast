// LOCKED cross-lane contract. BSH (this lane) exports it; BRE/BST/BAM subscribe.
// Keep this interface stable and documented. The integrator and the reenactment
// lane receive this text verbatim.

/** BSH exports; BRE/BST/BAM subscribe. Single source of truth for scene time. */
export interface SpectroTimelineAuthority {
  durationS: number;
  currentTimeS: number; // authoritative playhead [0, durationS]
  playbackRate: number; // 1.0 realtime; 0.25 slow-mo
  playing: boolean;
  sampleRate: number;
  seek(timeS: number, opts?: { play?: boolean }): void;
  setPlaybackRate(rate: number): void;
  play(): void;
  pause(): void;
  subscribe(fn: (state: Readonly<SpectroTimelineAuthority>) => void): () => void;
}

/** Read-only view of the precomputed STFT (shared with the acoustic lane). */
export interface SpectrogramFeatures {
  fftSize: number; // e.g. 2048
  hopSize: number; // e.g. 512
  freqBins: number; // fftSize / 2
  timeBins: number;
  magnitudes: Float32Array; // [timeBin * freqBins + freqBin], dB or power (document which)
  sampleRate: number;
  timeToBin(t: number): number;
}

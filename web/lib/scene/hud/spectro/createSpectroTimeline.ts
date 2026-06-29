// Integrator / BRE entry point. Wires the WebAudio engine and the off-thread STFT
// bake into a concrete SpectroTimelineAuthority + SpectrogramFeatures (+ optional
// HUD), from either an already-decoded AudioBuffer or a clip URL.
//
// Bake pipeline:
//   1. obtain the decoded AudioBuffer (shared, or fetched + decoded via the engine)
//   2. downmix to a mono Float32Array and transfer it to stft.worker.ts
//   3. the worker computes the Hann-windowed STFT + dB magnitudes + an rgba image
//      and transfers them back (0 ms on the main thread after this one-shot bake)
//   4. wrap the result in a SpectrogramCache (implements SpectrogramFeatures)
//   5. the engine doubles as the SpectroTimelineAuthority; build the HUD over it

import { SpectroAudioEngine } from "./audioEngine";
import { SpectrogramCache } from "./SpectrogramCache";
import { SpectroHud, type SpectroHudOptions } from "./SpectroHud";
import type { SpectroTimelineAuthority, SpectrogramFeatures } from "./types";

export interface CreateSpectroTimelineOptions {
  /** Already-decoded buffer (shared with the station player). */
  audioBuffer?: AudioBuffer;
  /** Fallback: fetch + decode this clip URL. */
  url?: string;
  /** Optional shared AudioContext. */
  context?: AudioContext;
  fftSize?: number;
  hopSize?: number;
  /** Build a Canvas 2D HUD (requires a DOM). Defaults to true in the browser. */
  buildHud?: boolean;
  hud?: SpectroHudOptions;
}

export interface SpectroTimeline {
  authority: SpectroTimelineAuthority;
  features: SpectrogramFeatures;
  cache: SpectrogramCache;
  engine: SpectroAudioEngine;
  hud: SpectroHud | null;
  dispose(): void;
}

interface WorkerResponse {
  magnitudes: Float32Array;
  rgba: Uint8ClampedArray;
  freqBins: number;
  timeBins: number;
  hopS: number;
  dbCeil: number;
  dbFloor: number;
  dynamicRangeDb: number;
}

function downmixToMono(buffer: AudioBuffer): Float32Array {
  const channels = buffer.numberOfChannels;
  const n = buffer.length;
  if (channels === 1) {
    // Copy so the transfer to the worker does not detach the engine's buffer.
    return buffer.getChannelData(0).slice();
  }
  const out = new Float32Array(n);
  for (let c = 0; c < channels; c++) {
    const data = buffer.getChannelData(c);
    for (let i = 0; i < n; i++) out[i] += data[i];
  }
  const inv = 1 / channels;
  for (let i = 0; i < n; i++) out[i] *= inv;
  return out;
}

function bakeStft(
  channel: Float32Array,
  sampleRate: number,
  fftSize: number,
  hopSize: number,
): Promise<{ worker: Worker; result: WorkerResponse }> {
  return new Promise((resolve, reject) => {
    // Next.js / webpack 5 native worker: the new URL(..., import.meta.url) form is
    // statically detected so the worker is emitted as its own chunk.
    const worker = new Worker(new URL("./stft.worker.ts", import.meta.url), { type: "module" });
    worker.onmessage = (ev: MessageEvent<WorkerResponse>) => resolve({ worker, result: ev.data });
    worker.onerror = (err) => {
      worker.terminate();
      reject(err);
    };
    worker.postMessage({ channel, sampleRate, fftSize, hopSize }, [channel.buffer]);
  });
}

export async function createSpectroTimeline(
  opts: CreateSpectroTimelineOptions,
): Promise<SpectroTimeline> {
  const fftSize = opts.fftSize ?? 2048;
  const hopSize = opts.hopSize ?? 512;

  const engine = new SpectroAudioEngine({ audioBuffer: opts.audioBuffer, context: opts.context });
  let buffer = opts.audioBuffer ?? null;
  if (!buffer) {
    if (!opts.url) throw new Error("createSpectroTimeline: provide audioBuffer or url");
    buffer = await engine.loadUrl(opts.url);
  }

  const channel = downmixToMono(buffer);
  const sampleRate = buffer.sampleRate;
  const { worker, result } = await bakeStft(channel, sampleRate, fftSize, hopSize);
  worker.terminate(); // one-shot bake; no further work on the worker

  const cache = new SpectrogramCache({
    rgba: result.rgba,
    magnitudes: result.magnitudes,
    sampleRate,
    hopS: result.hopS,
    fftSize,
    freqBins: result.freqBins,
    timeBins: result.timeBins,
    dbCeil: result.dbCeil,
    dbFloor: result.dbFloor,
    dynamicRangeDb: result.dynamicRangeDb,
  });

  const wantHud = opts.buildHud ?? typeof document !== "undefined";
  const hud = wantHud ? new SpectroHud(engine, cache, opts.hud) : null;

  return {
    authority: engine,
    features: cache,
    cache,
    engine,
    hud,
    dispose() {
      hud?.dispose();
      engine.dispose();
    },
  };
}

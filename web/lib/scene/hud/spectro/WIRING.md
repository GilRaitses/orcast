# BSH spectro HUD wiring

The BSH lane owns the STFT spectrogram HUD and the scene-time authority. This
document is the integrator and BRE handoff. The interface below is locked.

## Locked cross-lane contract

```typescript
/** BSH exports; BRE/BST/BAM subscribe. Single source of truth for scene time. */
export interface SpectroTimelineAuthority {
  durationS: number;
  currentTimeS: number;       // authoritative playhead [0, durationS]
  playbackRate: number;       // 1.0 realtime; 0.25 slow-mo
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
  fftSize: number;       // e.g. 2048
  hopSize: number;       // e.g. 512
  freqBins: number;      // fftSize / 2
  timeBins: number;
  magnitudes: Float32Array;   // [timeBin * freqBins + freqBin], dB or power (document which)
  sampleRate: number;
  timeToBin(t: number): number;
}
```

`magnitudes` is power in dB, computed as `10 * log10(re^2 + im^2)`. `freqBin 0` is
DC, `freqBin freqBins-1` is just below Nyquist (`sampleRate/2`). `timeToBin(t)`
returns `floor(t / hopS)` clamped to `[0, timeBins-1]`, where `hopS = hopSize /
sampleRate`.

## How BRE consumes it

```typescript
const { authority, features } = await createSpectroTimeline({ url });
authority.subscribe(({ currentTimeS, playbackRate, playing }) => {
  orca.update(dt, currentTimeS, cameraPos);
});
```

`currentTimeS` is a live getter. While playing it is
`startOffset + (ctx.currentTime - startClock) * playbackRate`, clamped to
`[0, durationS]`. While paused it reports the last committed offset, so
scrub-while-paused still reports the scrubbed time. A requestAnimationFrame notify
loop fires subscribers every frame while playing, so the subscribe callback alone
is enough to drive a per-frame follower. `seek`, `pause`, `play`, and
`setPlaybackRate` each notify once. `setPlaybackRate` rebases the clock so
`currentTimeS` stays continuous through a rate change.

A subscriber can also poll `authority.currentTimeS` directly inside its own
`useFrame` loop; both paths return the same value.

## Bake pipeline

1. `createSpectroTimeline({ audioBuffer | url })` obtains the decoded
   `AudioBuffer`. Pass `audioBuffer` to reuse the exact buffer the station player
   decoded, or pass `url` to fetch and decode via `AudioContext.decodeAudioData`.
2. The buffer is downmixed to a mono `Float32Array` and transferred to
   `stft.worker.ts`.
3. The worker computes the STFT off the main thread: Hann window, the supplied
   `hopSize` overlap, an inline radix-2 FFT (no dependency), power in dB, plus an
   adaptively normalized RGBA image from a 256-entry magma LUT. It transfers back
   `{ magnitudes, rgba, freqBins, timeBins, hopS }`.
4. The result is wrapped in a `SpectrogramCache` (implements `SpectrogramFeatures`).
5. The `SpectroAudioEngine` is itself the `SpectroTimelineAuthority`; the HUD is
   built over it.

After this one-shot bake the worker is terminated, so the STFT costs the r3f loop
0 ms/frame.

### Worker instantiation under Next.js

The worker is created with the webpack-5 native form:

```typescript
new Worker(new URL("./stft.worker.ts", import.meta.url), { type: "module" });
```

Next.js (webpack 5) statically detects this form and emits the worker as its own
chunk. The worker references the worker global through a narrow typed cast
(`self as unknown as { onmessage; postMessage }`) rather than `/// <reference lib=
"webworker" />`, because the project `tsconfig` uses the `dom` lib and the
`webworker` lib conflicts with it. This typechecks under `tsc --noEmit` with the
existing config. No `tsconfig` change is required.

## HUD mount

`SpectroHud` is a DOM SIBLING overlay, NOT a child of the r3f `<Canvas>` (it
mirrors the journey `StateHud` pattern). Call `hud.mount(parentEl)` to append its
root. It draws the prebaked spectrogram once into an offscreen base canvas, then
each frame blits that base and draws a single playhead line at
`x = currentTimeS / durationS * width` plus frequency and time axis ticks.

The frequency axis runs 0 to Nyquist (0 to 24 kHz for the 48 kHz clip), low at the
bottom. The time axis runs 0 to `durationS` left to right.

## Scrub and slow-mo

- Pointer drag on the canvas calls `authority.seek(x/width * durationS, {play:false})`.
- Three rate buttons (1.0x / 0.5x / 0.25x) call `authority.setPlaybackRate`.
- A play/pause button toggles `authority.play()` / `authority.pause()`.
- The HUD redraws on every authority notification (every frame while playing, once
  per scrub while paused).

## Per-frame cost

- Worker bake: one-shot, off the main thread, 0 ms/frame afterward.
- HUD redraw: one scaled `drawImage` of the cached base plus one playhead stroke
  and a handful of axis-tick fills. Estimated <= 1.5 ms/frame; not yet measured on
  the GPU host (GPU-host verification is serialized by the sub-orchestrator).

## Interpretive ocean layer

`web/lib/scene/ocean/interpretiveOceanLayer.ts` exports
`createInterpretiveOceanLayer` and the constant `INTERPRETIVE_OCEAN_LABEL`. It is
an additive, transparent, depth-write-off stratified-gradient stub. It defaults to
`enabled: false` and its `object3D` starts hidden. When enabled the host MUST show
the mandatory chip text exactly: `interpretive · stratified ocean mixing`. The
module asserts at load that the forbidden claims `measured thermohaline` and
`biosonar perception` never appear in the label. It adds no new render pass and
never writes depth, so it cannot regress the real water.

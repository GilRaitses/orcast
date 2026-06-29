# BSW-R06 - Spectrogram HUD tech

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent fbeaf532; written by the BSW sub-orchestrator.

## Summary

- **Today there is no client-side spectrogram.** `HydrophoneSignalPanel.tsx` renders a static ONC PNG from `/api/be/api/onc/hydrophone-signal`, which requires `ONC_API_TOKEN` on the backend. No `AudioContext`, `AnalyserNode`, or `AudioWorklet` exists in active `web/` code.
- **Default path (no new dependency):** `decodeAudioData` -> **Web Worker STFT** (inline power-of-2 FFT + Hann window, 50% overlap) -> bake RGBA spectrogram once -> **Canvas 2D HUD** as a DOM overlay sibling to the r3f `<Canvas>` (follow `StateHud` in `JourneyScene.tsx`, not the disabled `PerfHud` portal pattern).
- **Runtime cost target:** **0 ms/frame FFT** on the main thread/r3f loop if the spectrogram is fully precomputed; per-frame work is playhead line + optional column highlight (**estimated 0.3-1.5 ms/frame** for an 800x256 canvas). Fits **60 fps desktop / 30 fps laptop**.
- **`AnalyserNode` is for live tail visualization only** (fixed Blackman window, no overlap control, tied to playback clock). **Offline scrub requires precomputed STFT** in a Worker, not `OfflineAudioContext.suspend()` + `AnalyserNode`.
- **`AudioWorklet` FFT** is viable for live streaming tails but risky for large FFT sizes on the audio render thread (~3 ms budget per 128-sample quantum at 44.1 kHz); not the default for a scrubbable full-clip spectrogram.
- **BSH is the time authority:** `AudioContext.currentTime` / `AudioBufferSourceNode` playback drives `currentTimeS`; BRE consumes the same `t` for `track.sample(t)`; BAM shares the precomputed magnitude tensor.

## In-repo findings (cited)

### Current spectrogram (static ONC PNG, no WebAudio)

```59:70:web/app/components/console/HydrophoneSignalPanel.tsx
          {data.enabled && data.spectrogram_url ? (
            <img
              src={data.spectrogram_url}
              alt="Recent ONC hydrophone spectrogram"
              className="hydrophone-spectrogram"
              loading="lazy"
            />
          ) : (
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              {data.message ??
                "Live ONC spectrogram requires ONC_API_TOKEN on the backend. Station metadata shown."}
            </p>
          )}
```

Backend relay (`onc.py`): token stays server-side; client gets same-origin `spectrogram_url`. When token missing, `enabled:false`, `spectrogram_url:null`. Product is pre-generated ONC archivefile PNG, not computed from the slice clip. CSS: `.hydrophone-spectrogram` in `globals.css`.

### HUD precedents

| Pattern | File | Mechanism | Notes |
|---------|------|-----------|-------|
| DOM portal inside Canvas | `web/lib/scene/picking/PerfHud.tsx` | `createPortal` + `useFrame` | reads `gl.info.render`; not a 3D pass |
| Disabled in twin | `SalishScene.tsx:184-190,1110` | `SHOW_PERF_HUD=false` | r3f reconciler rejects portalled DOM span |
| **Sibling overlay outside Canvas** | `web/app/(sandbox)/journey/JourneyScene.tsx:360-396,432` | `StateHud` fixed absolute div next to `<Canvas>` | **best precedent for spectrogram HUD** |
| 3D-attached HTML label | `SalishScene.tsx:414-416` | drei `<Html>` on beacon hover | screen-space label |

No `web/lib/scene/hud/spectro/` exists yet (planned in BSH charter).

### Time sampling precedent (BRE will mirror)

```118:119:web/lib/scene/orca/OrcaController.ts
  function update(dt: number, elapsed: number, cameraWorldPos: THREE.Vector3 | null): void {
    const pose = track.sample(elapsed * timeScale);
```

`BiologgingTrack.sample(t)` interpolates frame-rate-independently (`biologging.ts:83-98`).

### WebAudio grep
None in active `web/` TS/TSX. Only `archive/public-templates-backup-20250720/real-time-detection.html:733` has `AudioContext` + oscillator beep (notification, not analysis). No `Worker`, `OffscreenCanvas`, or `SharedArrayBuffer` in `web/`.

### package.json (web/) - already available

| Package | Version | Relevant |
|---------|---------|----------|
| `three` | `^0.169.0` | `CanvasTexture`, `DataTexture`, colormap shader |
| `@react-three/fiber` | `^8.18.0` | `useFrame` (avoid heavy work) |
| `@react-three/drei` | `^9.122.0` | `Html` overlay |
| Audio libs | **none** | no wavesurfer/fft.js/tone.js |

Program constraint: **built on three + WebAudio**; new deps are costed recommendations only.

### Cross-lane seams
BST owns audio playback; spectrogram is BSH's; `streamUrl` not yet wired through `AdaptiveExplore.tsx`. BRE: scrub timeline authority is BSH playhead; `track.sample(t)` on slow/scrub. BAM: spectrogram input shares front-end FFT path with BSH (compute once).

## WebAudio FFT approach (AnalyserNode vs AudioWorklet; offline scrub strategy)

**AnalyserNode:** `fftSize` powers of 2 (32-32768); `getFloatFrequencyData()` on main thread; fixed Blackman window, **no overlap**, exponential smoothing. Good for live playback tail. Bad for scrubbable full-clip spectrogram (no hop/overlap control -> smearing; `OfflineAudioContext.suspend` path fragile; scrub needs random access -> precompute). Live tail cost est. 0.05-0.15 ms/frame.

**AudioWorklet:** `process()` every 128 samples, must complete in ~3 ms at 44.1 kHz; FFT size 2048 needs ring buffer (~37 ms latency before first frame). Good for real-time streaming tail; bad for full offline bake / scrub of pre-baked data. Worklet FFT risk est. 0.2-1.0 ms/hop.

**Recommended offline scrub strategy (default, no new dep):**
```
[Load] fetch(audioUrl) -> ArrayBuffer
[Main] AudioContext.decodeAudioData() -> AudioBuffer (mono mixdown)
       -> postMessage(transferable channel 0)
[Worker] STFT: fftSize=2048, hop=512, Hann, 50% overlap
         per frame: window -> radix-2 FFT -> magnitude -> dB -> uint8 colormap
         -> Float32Array magnitudes + Uint8ClampedArray RGBA
[Main] SpectrogramCache { width, height, rgba, magnitudes, sampleRate, hopS }
[Runtime] AudioBufferSourceNode + GainNode -> destination
         currentTimeS = startOffset + (ctx.currentTime - startClock) * playbackRate
         seek(t): stop source, restart at t
         HUD: drawImage prebaked canvas; playhead at x = t/duration * width
```
Worker (not AudioWorklet) for bake: 60 s clip @ hop 512 / 44.1 kHz ~5160 frames; at ~0.3 ms/FFT ~1.5 s total off main thread; 0 ms in r3f loop thereafter. Playback/scrub via `AudioBufferSourceNode`; `playbackRate` for slow-mo. No ONC token required.

## Render approach (canvas 2D vs WebGL texture over r3f; compute-neutral)

- **Option A - Canvas 2D DOM HUD (recommended):** StateHud sibling overlay; 0 extra r3f draw calls; `drawImage` once, per frame only playhead line (est. 0.3-1.5 ms/frame for 800x256); scrub maps pointer x; BAM shares `magnitudes`.
- **Option B - CanvasTexture on screen-aligned Plane (three-only):** bake to OffscreenCanvas in Worker; +1 draw call; full upload est. 1-3 ms (dirty playhead strip 0.2-0.8 ms); not a third full-scene pass.
- **Option C - DataTexture + fragment shader (three-only, for BAM overlay):** upload freq x time texture once; shader maps magnitude -> colormap; playhead via uniform (est. 0.05 ms/frame); best when BAM needs GPU sampling.

Not recommended: full spectrogram re-render per frame; third water/orca-scale pass for HUD; ONC PNG `<img>` for slice demo.

**Compute-neutral verdict:** STFT precompute 0 ms/frame (async); HUD draw <=1.5 ms desktop / <=2 ms laptop; r3f twin unchanged.

## Time-sync / scrub-seek contract (what BRE/BSH consume)

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

/** BAM: read-only view of precomputed STFT (shared bake). */
export interface SpectrogramFeatures {
  fftSize: number;       // e.g. 2048
  hopSize: number;       // e.g. 512
  freqBins: number;      // fftSize / 2
  timeBins: number;
  magnitudes: Float32Array;   // [timeBin * freqBins + freqBin]
  timeToBin(t: number): number;
}
```
BRE wiring: `authority.subscribe(({currentTimeS, playbackRate}) => orcaController.update(dt, currentTimeS*playbackRate, cameraPos))`. Scrub: pointer drag -> `seek(x/width*durationS, {play:false})`; slow-mo lowers `playbackRate`; BRE uses same scaled `t`. **HUD is time authority:** BRE must not run its own clock during scrub.

## Library survey (three-only fallback)

| Name | Version | License | Bundle (min+gzip est.) | Needed? |
|------|---------|---------|------------------------|---------|
| **(none - default)** | - | - | **0 KB** | **Default.** Worker STFT + Canvas 2D + WebAudio |
| `wavesurfer.js` | 7.12.8 | BSD-3-Clause | core ~47 KB ESM; spectrogram plugin ~30-50 KB | No (costed). Overlaps BST player; scrub/sync needs custom glue anyway |
| `fft.js` | 4.0.4 | MIT | ~22 KB unpacked (~13 KB lib) | Optional costed. Speeds Worker STFT vs inline. Fallback: ~150-line inline radix-2 FFT |
| `pretty-fast-fft` | 1.1.0 | MIT | WASM + JS | Optional. Fallback: inline JS FFT |
| `@echogarden/pffft-wasm` | 0.4.2 | BSD-3-Clause | ~173 KB unpacked; WASM 28.6/37.8 KB | Optional costed for long clips (>5 min); may need COOP/COEP for SIMD |
| `colormap` (npm) | - | MIT | small | No. Fallback: fixed 256-entry LUT in TS |
| `tone.js` | - | MIT | large | No. Fallback: AudioContext directly |

## Perf budget analysis (estimated ms/frame, FFT size, update rate)

Budget: 60 fps desktop (16.7 ms) / 30 fps laptop (33.3 ms). New work must not steal from existing depth pre-pass + water + orca + tiles.

Recommended STFT params: `fftSize=2048` (~21.5 Hz/bin at 44.1 kHz), `hopSize=512` (~11.6 ms/column), `freqBins=1024`, display 800x256 px, band 0-24 kHz.

One-time precompute (Worker, not per-frame), 60 s clip @ 44.1 kHz: `timeBins ~5160`; JS FFT 2048 ~0.15-0.5 ms each; total ~0.8-2.6 s in Worker. Memory: magnitudes ~21 MB Float32; RGBA downsampled 800x256 ~0.8 MB. For demo slice 30-90 s, acceptable with loading indicator.

Runtime per frame (60 Hz): FFT 0 (prebaked); read currentTimeS <0.01 ms; canvas blit + playhead 0.3-1.5 ms; BRE subscribe <0.1 ms; optional AnalyserNode tail 0.05-0.15 ms; CanvasTexture dirty strip 0.2-0.8 ms. Headroom: HUD <=~2 ms/frame vs 16.7 ms -> compute-neutral if precompute stays off-thread. STFT recompute only on new clip load.

## Recommendations with cost + three-only fallback

1. **Default stack (no new dep) - BUILD THIS:** decode via `AudioContext.decodeAudioData`; FFT in dedicated module Worker `web/lib/scene/hud/spectro/stft.worker.ts` (inline radix-2 2048, Hann, hop 512); `SpectrogramCache` RGBA + Float32 magnitudes for BAM; audio `AudioContext` + `AudioBufferSourceNode` (`currentTimeS` authority); Canvas 2D HUD in fixed DOM panel (StateHud placement); export `SpectroTimelineAuthority`. Cost: 0 npm deps, ~400-700 LOC in `web/lib/scene/hud/spectro/`.
2. **Costed optional `fft.js@4.0.4` (MIT, ~13 KB):** if inline FFT misses precompute budget on laptop for >120 s clips. Fallback: inline FFT.
3. **Costed optional `wavesurfer.js@7.12.8` + Spectrogram plugin:** only if BST wants turnkey waveform+scrub and O0 accepts ~80-120 KB gzip + Shadow DOM friction; must still export `SpectroTimelineAuthority`.
4. **Costed optional `@echogarden/pffft-wasm@0.4.2`:** for >5 min archived files. Fallback: JS Worker FFT + time-axis downsampling.
5. **Render choice:** ship Canvas 2D DOM HUD first (0 r3f draw calls); add DataTexture shader only if BAM needs GPU sampling.
6. **Do not use as primary:** ONC PNG for slice; AnalyserNode-only for scrub; full AudioWorklet FFT bake on audio render thread.

## Open questions for O0

1. Slice clip spec (R01): exact Orcasound URL, duration, format, station for STFT bake sizing.
2. HUD placement: scene overlay (StateHud on SalishScene) vs console panel vs both; convergence files include `SalishScene.tsx`, `globals.css`.
3. Frequency scale: linear 0-24 kHz vs mel (OrcaHello mel 1x256x312) for BAM alignment.
4. Replace or complement ONC panel? Keep ONC `<img>` as separate live-station context panel?
5. Confirm sibling DOM overlay as the locked HUD mount (not inside `<Canvas>`).
6. COOP/COEP headers required if O0 chooses WASM SIMD FFT on the Next.js host.
7. Slow-mo floor (e.g. 0.1) before BRE motion unreadable; does scrub-while-paused still drive orca pose (yes per charter)?
8. Shared feature handoff to BAM: export magnitudes only vs mel rebin in BSH Worker.

## Sources

### In-repo (commit 240570e)
`web/app/components/console/HydrophoneSignalPanel.tsx`, `web/app/globals.css`, `src/aws_backend/routers/onc.py`, `src/aws_backend/sources/onc.py`, `web/lib/scene/picking/PerfHud.tsx`, `web/app/components/scene/SalishScene.tsx`, `web/app/(sandbox)/journey/JourneyScene.tsx`, `web/lib/scene/atmosphere/transition.ts`, `web/lib/scene/wfx/realWfxEnv.ts`, `web/package.json`, `web/lib/scene/orca/OrcaController.ts`, `web/lib/scene/orca/motion/biologging.ts`, `.cca/.../BSW-{SPECTRO-HUD,REENACTMENT,STATION,ACOUSTIC-ML}_CHARTER.md`, `wave_shape.yml`, `archive/public-templates-backup-20250720/real-time-detection.html`

### External

| Source | URL | License / version |
|--------|-----|-------------------|
| Web Audio API 1.1 | https://www.w3.org/TR/webaudio-1.1/ | W3C spec |
| MDN AudioWorkletProcessor | https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletProcessor/process | CC-BY-SA |
| Chrome audio worklet design pattern | https://developer.chrome.com/blog/audio-worklet-design-pattern | Google dev doc |
| wavesurfer.js | https://www.npmjs.com/package/wavesurfer.js | 7.12.8, BSD-3-Clause |
| wavesurfer Spectrogram plugin | https://wavesurfer.xyz/example/spectrogram/ | BSD-3-Clause |
| fft.js | https://www.npmjs.com/package/fft.js | 4.0.4, MIT |
| @echogarden/pffft-wasm | https://www.npmjs.com/package/@echogarden/pffft-wasm | 0.4.2, BSD-3-Clause |
| pffft.wasm | https://github.com/JorenSix/pffft.wasm | BSD-2-Clause |
| Spectastiq (WebAudio offline STFT) | https://hardiesoft.com/posts/spectastiq-spectrogram-viewer | Blog (Worker STFT rationale) |

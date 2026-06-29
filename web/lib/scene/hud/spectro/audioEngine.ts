// WebAudio playback engine that IS the SpectroTimelineAuthority: the single scene
// -time source of truth the reenactment, station, and acoustic lanes follow.
//
// Authoritative playhead while playing:
//   currentTimeS = startOffset + (ctx.currentTime - startClock) * playbackRate
// While paused it reports the last committed offset (so scrub-while-paused still
// reports the scrubbed time). An AudioBufferSourceNode is one-shot, so seek() and
// setPlaybackRate() stop the current source and start a fresh one at the new offset.
//
// A requestAnimationFrame notify loop runs only while playing, so subscribers see a
// fresh currentTimeS every frame during playback; seek/pause/rate notify once.

import type { SpectroTimelineAuthority } from "./types";

type Listener = (state: Readonly<SpectroTimelineAuthority>) => void;

export interface SpectroEngineOptions {
  /** Reuse a buffer already decoded by the station player (exact same audio). */
  audioBuffer?: AudioBuffer;
  /** Optional shared AudioContext; one is created if omitted. */
  context?: AudioContext;
}

export class SpectroAudioEngine implements SpectroTimelineAuthority {
  private ctx: AudioContext;
  private ownsContext: boolean;
  private buffer: AudioBuffer | null;
  private source: AudioBufferSourceNode | null = null;
  private gain: GainNode;

  private _playing = false;
  private _playbackRate = 1;
  private startOffset = 0; // buffer time at which the live source began
  private startClock = 0; // ctx.currentTime captured when the source began
  private listeners = new Set<Listener>();
  private rafId: number | null = null;

  constructor(opts: SpectroEngineOptions = {}) {
    this.ctx = opts.context ?? new AudioContext();
    this.ownsContext = !opts.context;
    this.buffer = opts.audioBuffer ?? null;
    this.gain = this.ctx.createGain();
    this.gain.connect(this.ctx.destination);
  }

  /** Fallback path: fetch + decode the clip ourselves when no buffer was shared. */
  async loadUrl(url: string): Promise<AudioBuffer> {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`spectro audio fetch failed: ${res.status} ${url}`);
    const bytes = await res.arrayBuffer();
    this.buffer = await this.ctx.decodeAudioData(bytes);
    return this.buffer;
  }

  /** Adopt a buffer the station player already decoded. */
  useBuffer(buffer: AudioBuffer): void {
    this.buffer = buffer;
  }

  getBuffer(): AudioBuffer | null {
    return this.buffer;
  }

  get audioContext(): AudioContext {
    return this.ctx;
  }

  get durationS(): number {
    return this.buffer?.duration ?? 0;
  }

  get sampleRate(): number {
    return this.buffer?.sampleRate ?? this.ctx.sampleRate;
  }

  get playbackRate(): number {
    return this._playbackRate;
  }

  get playing(): boolean {
    return this._playing;
  }

  get currentTimeS(): number {
    let t = this.startOffset;
    if (this._playing) t += (this.ctx.currentTime - this.startClock) * this._playbackRate;
    const d = this.durationS;
    if (t < 0) return 0;
    if (d > 0 && t > d) return d;
    return t;
  }

  private stopSource(): void {
    if (this.source) {
      this.source.onended = null;
      try {
        this.source.stop();
      } catch {
        // already stopped; ignore
      }
      this.source.disconnect();
      this.source = null;
    }
  }

  private startSource(offset: number): void {
    if (!this.buffer) return;
    this.stopSource();
    const src = this.ctx.createBufferSource();
    src.buffer = this.buffer;
    src.playbackRate.value = this._playbackRate;
    src.connect(this.gain);
    src.onended = () => {
      // Only react to a true end-of-buffer (not a stop() from seek/rate change).
      if (this.source === src && this._playing) {
        this._playing = false;
        this.startOffset = this.durationS;
        this.stopRaf();
        this.notify();
      }
    };
    this.startOffset = Math.max(0, Math.min(offset, this.durationS));
    this.startClock = this.ctx.currentTime;
    src.start(0, this.startOffset);
    this.source = src;
  }

  seek(timeS: number, opts?: { play?: boolean }): void {
    const wantPlay = opts?.play ?? this._playing;
    this.stopSource();
    this.startOffset = Math.max(0, Math.min(timeS, this.durationS));
    this.startClock = this.ctx.currentTime;
    if (wantPlay && this.buffer) {
      this._playing = true;
      void this.ctx.resume();
      this.startSource(this.startOffset);
      this.startRaf();
    } else {
      this._playing = false;
      this.stopRaf();
    }
    this.notify();
  }

  setPlaybackRate(rate: number): void {
    const r = rate > 0 ? rate : 1;
    // Rebase so currentTimeS stays continuous across the rate change.
    const now = this.currentTimeS;
    this._playbackRate = r;
    if (this._playing) {
      this.startSource(now);
    } else {
      this.startOffset = now;
      this.startClock = this.ctx.currentTime;
    }
    this.notify();
  }

  play(): void {
    if (this._playing || !this.buffer) return;
    this._playing = true;
    void this.ctx.resume();
    this.startSource(this.startOffset);
    this.startRaf();
    this.notify();
  }

  pause(): void {
    if (!this._playing) return;
    const now = this.currentTimeS;
    this.stopSource();
    this._playing = false;
    this.startOffset = now;
    this.startClock = this.ctx.currentTime;
    this.stopRaf();
    this.notify();
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    fn(this);
    return () => {
      this.listeners.delete(fn);
    };
  }

  private notify(): void {
    for (const fn of this.listeners) fn(this);
  }

  private startRaf(): void {
    if (this.rafId !== null) return;
    const tick = () => {
      if (!this._playing) {
        this.rafId = null;
        return;
      }
      this.notify();
      this.rafId = requestAnimationFrame(tick);
    };
    this.rafId = requestAnimationFrame(tick);
  }

  private stopRaf(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  dispose(): void {
    this.stopRaf();
    this.stopSource();
    this.gain.disconnect();
    this.listeners.clear();
    if (this.ownsContext) void this.ctx.close();
  }
}

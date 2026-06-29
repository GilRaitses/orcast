// Framework-agnostic WebAudio player bound to the one real archived clip.
//
// MEASURED audio. This plays the real Orcasound Lab hydrophone recording at
// `audioUrl`; it never synthesises a waveform. If the fetch or decode fails it
// surfaces an error state instead of inventing audio. The decoded `AudioBuffer`
// is exposed so a spectrogram lane can analyse the SAME real samples.
//
// AudioBufferSourceNode cannot be paused, so play/pause/seek track an offset and
// recreate the source each time playback resumes from a known position.

export interface StationPlayerOptions {
  /** URL of the real archived clip (e.g. /hydrophone/slice/...m4a). */
  audioUrl: string;
  /** Optional live-listen stream URL surfaced by the UI (not decoded here). */
  streamUrl?: string;
  /** Attribution string the UI MUST display (license + source). */
  attribution: string;
}

export type StationPlayerStatus = "idle" | "loading" | "ready" | "error";

type AudioContextCtor = typeof AudioContext;

function resolveAudioContextCtor(): AudioContextCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    AudioContext?: AudioContextCtor;
    webkitAudioContext?: AudioContextCtor;
  };
  return w.AudioContext ?? w.webkitAudioContext ?? null;
}

export class StationPlayer {
  readonly audioUrl: string;
  readonly streamUrl: string | null;
  readonly attribution: string;
  /** This audio is real, not synthesised. */
  readonly honesty = "measured" as const;

  private ctx: AudioContext | null = null;
  private buffer: AudioBuffer | null = null;
  private source: AudioBufferSourceNode | null = null;
  private gain: GainNode | null = null;

  private playing = false;
  private offsetSec = 0;
  private startedAtCtxTime = 0;
  private rate = 1;

  private status: StationPlayerStatus = "idle";
  private errorMessage: string | null = null;

  constructor(opts: StationPlayerOptions) {
    this.audioUrl = opts.audioUrl;
    this.streamUrl = opts.streamUrl ?? null;
    this.attribution = opts.attribution;
  }

  getStatus(): StationPlayerStatus {
    return this.status;
  }

  getError(): string | null {
    return this.errorMessage;
  }

  /** The decoded real audio, or null until `load()` resolves. */
  getAudioBuffer(): AudioBuffer | null {
    return this.buffer;
  }

  /** Fetch the real clip and decode it. Rejects (and sets error state) on failure. */
  async load(): Promise<void> {
    const Ctor = resolveAudioContextCtor();
    if (!Ctor) {
      this.fail("WebAudio is unavailable in this environment");
      throw new Error(this.errorMessage ?? "no AudioContext");
    }
    this.status = "loading";
    this.errorMessage = null;
    try {
      if (!this.ctx) {
        this.ctx = new Ctor();
        this.gain = this.ctx.createGain();
        this.gain.connect(this.ctx.destination);
      }
      const res = await fetch(this.audioUrl);
      if (!res.ok) {
        throw new Error(`fetch ${this.audioUrl} failed (${res.status} ${res.statusText})`);
      }
      const data = await res.arrayBuffer();
      this.buffer = await this.ctx.decodeAudioData(data);
      this.status = "ready";
    } catch (e) {
      this.fail(e instanceof Error ? e.message : String(e));
      throw e;
    }
  }

  private fail(message: string): void {
    this.status = "error";
    this.errorMessage = message;
    this.buffer = null;
  }

  isPlaying(): boolean {
    return this.playing;
  }

  getDuration(): number {
    return this.buffer ? this.buffer.duration : 0;
  }

  getCurrentTime(): number {
    if (this.playing && this.ctx) {
      const t = this.offsetSec + (this.ctx.currentTime - this.startedAtCtxTime) * this.rate;
      return Math.min(t, this.getDuration());
    }
    return this.offsetSec;
  }

  play(): void {
    if (!this.ctx || !this.buffer || this.playing) return;
    if (this.ctx.state === "suspended") void this.ctx.resume();
    this.startFromOffset(this.offsetSec);
  }

  private startFromOffset(offset: number): void {
    if (!this.ctx || !this.buffer || !this.gain) return;
    this.stopSource();
    const src = this.ctx.createBufferSource();
    src.buffer = this.buffer;
    src.playbackRate.value = this.rate;
    src.connect(this.gain);
    src.onended = () => {
      // Distinguish a natural end-of-clip from a programmatic stop: only a
      // natural end advances the offset to the duration and clears playing.
      if (this.source === src && this.playing) {
        this.playing = false;
        this.offsetSec = this.getDuration();
        this.source = null;
      }
    };
    const clamped = Math.max(0, Math.min(offset, this.getDuration()));
    src.start(0, clamped);
    this.source = src;
    this.offsetSec = clamped;
    this.startedAtCtxTime = this.ctx.currentTime;
    this.playing = true;
  }

  private stopSource(): void {
    if (this.source) {
      this.source.onended = null;
      try {
        this.source.stop();
      } catch {
        // Already stopped; ignore.
      }
      this.source.disconnect();
      this.source = null;
    }
  }

  pause(): void {
    if (!this.playing) return;
    this.offsetSec = this.getCurrentTime();
    this.playing = false;
    this.stopSource();
  }

  seek(t: number): void {
    const clamped = Math.max(0, Math.min(t, this.getDuration()));
    if (this.playing) {
      this.startFromOffset(clamped);
    } else {
      this.offsetSec = clamped;
    }
  }

  setPlaybackRate(r: number): void {
    const rate = Number.isFinite(r) && r > 0 ? r : 1;
    if (this.playing) {
      // Re-anchor the offset at the current position before changing the rate so
      // getCurrentTime stays continuous, then resume from there at the new rate.
      this.offsetSec = this.getCurrentTime();
      this.rate = rate;
      this.startFromOffset(this.offsetSec);
    } else {
      this.rate = rate;
    }
  }

  getPlaybackRate(): number {
    return this.rate;
  }

  dispose(): void {
    this.stopSource();
    this.playing = false;
    this.buffer = null;
    if (this.gain) {
      this.gain.disconnect();
      this.gain = null;
    }
    if (this.ctx) {
      void this.ctx.close();
      this.ctx = null;
    }
  }
}

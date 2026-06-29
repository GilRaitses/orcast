// Canvas 2D spectrogram HUD, mounted as a DOM SIBLING overlay (NOT inside the r3f
// <Canvas>), mirroring the StateHud pattern in the journey sandbox.
//
// The prebaked spectrogram is drawn ONCE into an offscreen base canvas. Each frame
// the HUD blits that base and draws a single playhead line plus axis ticks, so the
// per-frame cost is one scaled drawImage and a few strokes (estimated <= 1.5 ms).
//
// Pointer drag on the canvas scrubs: authority.seek(x/width * durationS, {play:false}).
// Slow-mo buttons (1.0x / 0.5x / 0.25x) call authority.setPlaybackRate, and a
// play/pause button toggles playback. The HUD redraws whenever the authority
// notifies (every frame while playing, once per scrub while paused).

import type { SpectroTimelineAuthority } from "./types";
import type { SpectrogramCache } from "./SpectrogramCache";
import { frequencyTicks, timeTicks } from "./axes";
import { createSpectroLegend } from "./legend";

export interface SpectroHudOptions {
  /** Displayed width/height of the spectrogram canvas in CSS pixels. */
  width?: number;
  height?: number;
  /** Caption rendered under the HUD (provenance honesty line). */
  caption?: string;
  /** Show the colormap legend keyed to the adaptive dB normalization. Default true. */
  legend?: boolean;
}

const RATES = [1, 0.5, 0.25];

export class SpectroHud {
  readonly root: HTMLDivElement;
  private canvas: HTMLCanvasElement;
  private g: CanvasRenderingContext2D;
  private base: HTMLCanvasElement;
  private timeReadout: HTMLSpanElement;
  private rateButtons: HTMLButtonElement[] = [];
  private playButton: HTMLButtonElement;

  private authority: SpectroTimelineAuthority;
  private cache: SpectrogramCache;
  private unsubscribe: (() => void) | null = null;
  private dragging = false;

  private readonly dispW: number;
  private readonly dispH: number;
  private nyquist: number;

  private readonly showLegend: boolean;
  private specRow: HTMLDivElement;
  private canvasWrap: HTMLDivElement;
  private legendEl: HTMLDivElement | null = null;
  private titleEl: HTMLDivElement;

  constructor(authority: SpectroTimelineAuthority, cache: SpectrogramCache, opts: SpectroHudOptions = {}) {
    this.authority = authority;
    this.cache = cache;
    this.dispW = opts.width ?? 900;
    this.dispH = opts.height ?? 280;
    this.nyquist = cache.sampleRate / 2;
    this.showLegend = opts.legend ?? true;

    this.root = document.createElement("div");
    Object.assign(this.root.style, {
      position: "absolute",
      left: "12px",
      bottom: "12px",
      padding: "10px 12px",
      borderRadius: "8px",
      background: "rgba(8,38,61,0.86)",
      font: "11px/1.4 ui-monospace, monospace",
      color: "#cfe6ff",
    } as CSSStyleDeclaration);

    // Title row (refreshed by bindClip for multi-clip swaps).
    this.titleEl = document.createElement("div");
    this.titleEl.style.marginBottom = "6px";
    this.root.appendChild(this.titleEl);

    // Base offscreen canvas at native bin resolution (filled by bindClip).
    this.base = document.createElement("canvas");

    // Spectrogram row holds a canvas wrapper sized EXACTLY to the display canvas.
    this.specRow = document.createElement("div");
    Object.assign(this.specRow.style, {
      display: "flex",
      alignItems: "flex-start",
    } as CSSStyleDeclaration);

    // Canvas wrapper: position:relative + an explicit canvas-sized box makes this
    // the containing block for the absolutely-positioned colormap legend, so the
    // legend is anchored to the CANVAS bounds (not the wider HUD row) and can
    // never overflow the canvas or be occluded by the console panel.
    this.canvasWrap = document.createElement("div");
    Object.assign(this.canvasWrap.style, {
      position: "relative",
      width: this.dispW + "px",
      height: this.dispH + "px",
    } as CSSStyleDeclaration);

    // Display canvas.
    this.canvas = document.createElement("canvas");
    this.canvas.width = this.dispW;
    this.canvas.height = this.dispH;
    Object.assign(this.canvas.style, {
      display: "block",
      width: this.dispW + "px",
      height: this.dispH + "px",
      borderRadius: "4px",
      cursor: "ew-resize",
      touchAction: "none",
    } as CSSStyleDeclaration);
    const g = this.canvas.getContext("2d");
    if (!g) throw new Error("SpectroHud: 2D context unavailable for display canvas");
    this.g = g;
    this.g.imageSmoothingEnabled = false;
    this.canvasWrap.appendChild(this.canvas);
    this.specRow.appendChild(this.canvasWrap);
    this.root.appendChild(this.specRow);

    this.buildBase();
    this.buildLegend();
    this.refreshTitle();

    // Controls row: play/pause, slow-mo rates, time readout.
    const controls = document.createElement("div");
    Object.assign(controls.style, {
      display: "flex",
      alignItems: "center",
      gap: "6px",
      marginTop: "6px",
    } as CSSStyleDeclaration);

    this.playButton = this.makeButton(this.authority.playing ? "pause" : "play");
    this.playButton.addEventListener("click", () => {
      if (this.authority.playing) this.authority.pause();
      else this.authority.play();
    });
    controls.appendChild(this.playButton);

    const sep = document.createElement("span");
    sep.textContent = "rate";
    sep.style.opacity = "0.7";
    controls.appendChild(sep);

    for (const rate of RATES) {
      const btn = this.makeButton(rate === 1 ? "1.0x" : rate.toFixed(2) + "x");
      btn.addEventListener("click", () => this.authority.setPlaybackRate(rate));
      this.rateButtons.push(btn);
      controls.appendChild(btn);
    }

    this.timeReadout = document.createElement("span");
    this.timeReadout.style.marginLeft = "auto";
    this.timeReadout.style.opacity = "0.95";
    controls.appendChild(this.timeReadout);
    this.root.appendChild(controls);

    if (opts.caption) {
      const cap = document.createElement("div");
      cap.style.marginTop = "4px";
      cap.style.opacity = "0.7";
      cap.textContent = opts.caption;
      this.root.appendChild(cap);
    }

    this.attachPointer();
    this.unsubscribe = this.authority.subscribe(() => this.draw());
    this.draw();
  }

  /** Draw the prebaked rgba into the offscreen base canvas at native bin res. */
  private buildBase(): void {
    const cache = this.cache;
    this.base.width = Math.max(1, cache.timeBins);
    this.base.height = Math.max(1, cache.freqBins);
    const bg = this.base.getContext("2d");
    if (!bg) throw new Error("SpectroHud: 2D context unavailable for base canvas");
    if (cache.timeBins > 0 && cache.freqBins > 0) {
      // Copy into a fresh ArrayBuffer-backed view so ImageData accepts it (the
      // baked rgba arrives over a worker message typed as ArrayBufferLike).
      const pixels = new Uint8ClampedArray(cache.rgba);
      const img = new ImageData(pixels, cache.timeBins, cache.freqBins);
      bg.putImageData(img, 0, 0);
    }
  }

  /** (Re)build the colormap legend keyed to this clip's adaptive dB range. */
  private buildLegend(): void {
    if (!this.showLegend) return;
    // Compact inset sized to a corner of the canvas (not the full height), so it
    // reads as an inset and hides as little of the spectrogram as possible.
    const insetHeight = Math.min(this.dispH - 16, 140);
    const next = createSpectroLegend(
      { dbCeil: this.cache.dbCeil, dbFloor: this.cache.dbFloor, dynamicRangeDb: this.cache.dynamicRangeDb },
      { height: insetHeight },
    );
    // Anchor inside the canvas bounds at the TOP-LEFT. canvasWrap is sized to the
    // canvas and is the relative containing block. The left corner is chosen on
    // purpose: the console panel always sits to the RIGHT of the scene, so a
    // left-anchored inset can never be occluded by the console at any viewport.
    // The left offset clears the on-canvas frequency-axis labels (drawn at x=3).
    Object.assign(next.style, {
      position: "absolute",
      top: "6px",
      left: "30px",
    } as CSSStyleDeclaration);
    if (this.legendEl) this.canvasWrap.replaceChild(next, this.legendEl);
    else this.canvasWrap.appendChild(next);
    this.legendEl = next;
  }

  private refreshTitle(): void {
    this.titleEl.innerHTML =
      "<strong>STFT spectrogram</strong> measured Orcasound Lab audio. freq 0 to " +
      (this.nyquist / 1000).toFixed(0) +
      " kHz, low at bottom, time left to right.";
  }

  /**
   * Rebind the HUD to a different clip's authority + cache (multi-clip support).
   * Rebuilds the base image, legend, frequency axis range, and redraws. The
   * locked SpectroTimelineAuthority contract is unchanged; only which authority
   * the HUD listens to swaps.
   */
  bindClip(authority: SpectroTimelineAuthority, cache: SpectrogramCache): void {
    this.unsubscribe?.();
    this.authority = authority;
    this.cache = cache;
    this.nyquist = cache.sampleRate / 2;
    this.buildBase();
    this.buildLegend();
    this.refreshTitle();
    this.unsubscribe = this.authority.subscribe(() => this.draw());
    this.draw();
  }

  private makeButton(label: string): HTMLButtonElement {
    const btn = document.createElement("button");
    btn.textContent = label;
    Object.assign(btn.style, {
      font: "11px ui-monospace, monospace",
      color: "#cfe6ff",
      background: "rgba(20,70,100,0.9)",
      border: "1px solid rgba(120,180,220,0.4)",
      borderRadius: "4px",
      padding: "2px 8px",
      cursor: "pointer",
    } as CSSStyleDeclaration);
    return btn;
  }

  private attachPointer(): void {
    const seekFromEvent = (e: PointerEvent) => {
      const rect = this.canvas.getBoundingClientRect();
      let x = (e.clientX - rect.left) / rect.width;
      if (x < 0) x = 0;
      else if (x > 1) x = 1;
      const d = this.authority.durationS;
      this.authority.seek(x * d, { play: false });
    };
    this.canvas.addEventListener("pointerdown", (e) => {
      this.dragging = true;
      this.canvas.setPointerCapture(e.pointerId);
      seekFromEvent(e);
    });
    this.canvas.addEventListener("pointermove", (e) => {
      if (this.dragging) seekFromEvent(e);
    });
    const end = (e: PointerEvent) => {
      if (!this.dragging) return;
      this.dragging = false;
      try {
        this.canvas.releasePointerCapture(e.pointerId);
      } catch {
        // pointer may already be released; ignore
      }
    };
    this.canvas.addEventListener("pointerup", end);
    this.canvas.addEventListener("pointercancel", end);
  }

  /** Blit the prebaked spectrogram, then the playhead and axis ticks. */
  draw(): void {
    const g = this.g;
    const w = this.dispW;
    const h = this.dispH;
    g.clearRect(0, 0, w, h);
    if (this.base.width > 0 && this.base.height > 0) {
      g.drawImage(this.base, 0, 0, this.base.width, this.base.height, 0, 0, w, h);
    }

    const d = this.authority.durationS;
    const t = this.authority.currentTimeS;
    const x = d > 0 ? (t / d) * w : 0;

    // Playhead.
    g.strokeStyle = "#ffffff";
    g.lineWidth = 1.5;
    g.beginPath();
    g.moveTo(x, 0);
    g.lineTo(x, h);
    g.stroke();

    this.drawAxes(g, w, h, d);

    // State readouts.
    const rate = this.authority.playbackRate;
    this.timeReadout.textContent =
      `t = ${t.toFixed(2)} s / ${d.toFixed(1)} s  ${rate.toFixed(2)}x  ${this.authority.playing ? "playing" : "paused"}`;
    this.playButton.textContent = this.authority.playing ? "pause" : "play";
    this.rateButtons.forEach((btn, i) => {
      btn.style.outline = Math.abs(RATES[i] - rate) < 1e-6 ? "1px solid #cfe6ff" : "none";
    });
  }

  private drawAxes(g: CanvasRenderingContext2D, w: number, h: number, d: number): void {
    g.font = "10px ui-monospace, monospace";

    // Frequency ticks on the left (bottom = 0, top = Nyquist) at nice values.
    g.textAlign = "left";
    for (const tick of frequencyTicks(this.nyquist, 5)) {
      const y = h - tick.frac * h;
      const cy = Math.max(9, Math.min(h - 2, y + 3));
      // Faint gridline then the label, so the tick reads over the colormap.
      g.strokeStyle = "rgba(207,230,255,0.18)";
      g.lineWidth = 1;
      g.beginPath();
      g.moveTo(22, y);
      g.lineTo(w, y);
      g.stroke();
      g.fillStyle = "rgba(207,230,255,0.9)";
      g.fillText(tick.label, 3, cy);
    }

    // Time ticks along the bottom at nice values.
    g.textAlign = "center";
    g.fillStyle = "rgba(207,230,255,0.9)";
    for (const tick of timeTicks(d, 6)) {
      const x = tick.frac * w;
      g.fillText(tick.label, Math.max(10, Math.min(w - 10, x)), h - 3);
    }
    g.textAlign = "left";
  }

  /** Mount the HUD root under a parent element. */
  mount(parent: HTMLElement): void {
    parent.appendChild(this.root);
  }

  dispose(): void {
    this.unsubscribe?.();
    this.unsubscribe = null;
    this.root.remove();
  }
}

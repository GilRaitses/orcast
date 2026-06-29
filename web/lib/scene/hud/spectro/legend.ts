// Colormap legend for the spectrogram HUD. Renders the same magma LUT used by the
// off-thread bake as a vertical color bar, with dB tick labels keyed to the
// adaptive 80 dB normalization (dbCeil at the top, dbFloor at the bottom). Built
// once from the SpectrogramCache; it is a small DOM element the HUD appends.

import { buildMagmaLut } from "./colormap";

export interface SpectroLegendOptions {
  /** Bar height in CSS pixels. */
  height?: number;
  /** Bar width in CSS pixels. */
  width?: number;
  /** Number of dB tick labels along the bar. */
  ticks?: number;
}

export interface SpectroLegendInput {
  dbCeil: number;
  dbFloor: number;
  dynamicRangeDb: number;
}

/** Build the legend element. Returns a root the caller appends to the HUD. */
export function createSpectroLegend(
  input: SpectroLegendInput,
  opts: SpectroLegendOptions = {},
): HTMLDivElement {
  const height = opts.height ?? 120;
  const width = opts.width ?? 12;
  const tickCount = opts.ticks ?? 4;

  const root = document.createElement("div");
  Object.assign(root.style, {
    display: "flex",
    alignItems: "stretch",
    gap: "4px",
    font: "10px ui-monospace, monospace",
    color: "rgba(207,230,255,0.95)",
    // Inset-overlay styling: this legend is anchored INSIDE the spectrogram
    // canvas bounds (top-right) by the HUD, so it can never be occluded by the
    // surrounding page chrome. The translucent backing keeps the dB labels
    // legible over the colormap, and it never intercepts the scrub pointer.
    background: "rgba(8,30,48,0.62)",
    padding: "4px 5px",
    borderRadius: "5px",
    pointerEvents: "none",
  } as CSSStyleDeclaration);

  // Vertical color bar: top row = loudest (dbCeil), bottom row = quietest.
  const bar = document.createElement("canvas");
  bar.width = 1;
  bar.height = Math.max(2, height);
  Object.assign(bar.style, {
    width: width + "px",
    height: height + "px",
    borderRadius: "2px",
    display: "block",
  } as CSSStyleDeclaration);
  const bg = bar.getContext("2d");
  if (bg) {
    const lut = buildMagmaLut();
    const img = bg.createImageData(1, bar.height);
    for (let y = 0; y < bar.height; y++) {
      // y=0 is the top -> loudest -> norm 1.
      const norm = 1 - y / (bar.height - 1);
      const ci = Math.round(norm * 255) * 3;
      const px = y * 4;
      img.data[px] = lut[ci];
      img.data[px + 1] = lut[ci + 1];
      img.data[px + 2] = lut[ci + 2];
      img.data[px + 3] = 255;
    }
    bg.putImageData(img, 0, 0);
  }

  // dB tick labels next to the bar.
  const labels = document.createElement("div");
  Object.assign(labels.style, {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    height: height + "px",
  } as CSSStyleDeclaration);
  for (let i = 0; i <= tickCount; i++) {
    const frac = i / tickCount; // 0 at top
    const db = input.dbCeil - frac * input.dynamicRangeDb;
    const span = document.createElement("span");
    span.textContent = `${db.toFixed(0)} dB`;
    labels.appendChild(span);
  }

  const caption = document.createElement("div");
  Object.assign(caption.style, {
    writingMode: "vertical-rl",
    transform: "rotate(180deg)",
    opacity: "0.7",
  } as CSSStyleDeclaration);
  caption.textContent = "power (dB)";

  root.appendChild(caption);
  root.appendChild(bar);
  root.appendChild(labels);
  return root;
}

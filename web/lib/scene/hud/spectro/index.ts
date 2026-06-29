// BSH spectro HUD barrel. Single source of scene time for BRE/BST/BAM.
// See WIRING.md for the locked SpectroTimelineAuthority contract.

export type { SpectroTimelineAuthority, SpectrogramFeatures } from "./types";
export { createSpectroTimeline } from "./createSpectroTimeline";
export type {
  CreateSpectroTimelineOptions,
  SpectroTimeline,
} from "./createSpectroTimeline";
export { SpectroAudioEngine } from "./audioEngine";
export type { SpectroEngineOptions } from "./audioEngine";
export { SpectrogramCache } from "./SpectrogramCache";
export type { SpectrogramCacheInit } from "./SpectrogramCache";
export { SpectroHud } from "./SpectroHud";
export type { SpectroHudOptions } from "./SpectroHud";
export { frequencyTicks, timeTicks } from "./axes";
export type { AxisTick } from "./axes";
export { createSpectroLegend } from "./legend";
export type { SpectroLegendOptions, SpectroLegendInput } from "./legend";
export { MAGMA_STOPS, buildMagmaLut, sampleMagma } from "./colormap";
export type { ColorStop } from "./colormap";
export { createSpectroClipSet } from "./multiClip";
export type {
  SpectroClipSet,
  SpectroClipDescriptor,
  SpectroClipSetOptions,
} from "./multiClip";

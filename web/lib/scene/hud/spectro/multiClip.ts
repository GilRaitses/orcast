// Multi-clip support for the spectrogram HUD. Bakes one SpectroTimeline per clip
// (lazily, on first selection) and drives a SINGLE shared SpectroHud across them
// via hud.bindClip. The active clip's authority is the SpectroTimelineAuthority
// that BRE/BST/BAM follow; switching clips swaps which authority is active but
// never changes the locked authority contract.
//
// Only real, license-cleared clips should be registered here. The mechanism does
// not invent audio; an empty or single-clip set is valid.

import { createSpectroTimeline, type SpectroTimeline } from "./createSpectroTimeline";
import { SpectroHud, type SpectroHudOptions } from "./SpectroHud";
import type { SpectroTimelineAuthority, SpectrogramFeatures } from "./types";

export interface SpectroClipDescriptor {
  id: string;
  /** Short label for a selector control. */
  label: string;
  /** Clip URL (real, license-cleared audio). */
  url: string;
  /** Optional one-line provenance/attribution. */
  provenance?: string;
}

export interface SpectroClipSetOptions {
  clips: SpectroClipDescriptor[];
  /** Which clip to bake + show first. Defaults to clips[0]. */
  initialId?: string;
  fftSize?: number;
  hopSize?: number;
  /** Build a shared Canvas 2D HUD. Defaults to true in the browser. */
  buildHud?: boolean;
  hud?: SpectroHudOptions;
}

export interface SpectroClipSet {
  /** The shared HUD (null if buildHud was false or there is no DOM). */
  hud: SpectroHud | null;
  /** The currently active clip id. */
  activeId: string | null;
  /** Active authority (the time source BRE follows). Null before first bake. */
  authority: SpectroTimelineAuthority | null;
  /** Active read-only STFT features (for the acoustic lane). */
  features: SpectrogramFeatures | null;
  /** Registered clips, in order. */
  readonly clips: readonly SpectroClipDescriptor[];
  /** Bake (if needed) and switch to a clip. Resolves once it is active. */
  select(id: string): Promise<void>;
  /** Subscribe to active-clip changes (fires after each successful select). */
  onChange(fn: (id: string) => void): () => void;
  dispose(): void;
}

/**
 * Create a clip set. The initial clip is baked immediately; others are baked on
 * first select and cached. Pause the previously active clip when switching so
 * only one clip ever plays.
 */
export async function createSpectroClipSet(
  opts: SpectroClipSetOptions,
): Promise<SpectroClipSet> {
  const clips = opts.clips.slice();
  if (clips.length === 0) throw new Error("createSpectroClipSet: no clips registered");
  const wantHud = opts.buildHud ?? typeof document !== "undefined";

  const baked = new Map<string, SpectroTimeline>();
  const listeners = new Set<(id: string) => void>();

  async function bake(id: string): Promise<SpectroTimeline> {
    const existing = baked.get(id);
    if (existing) return existing;
    const desc = clips.find((c) => c.id === id);
    if (!desc) throw new Error(`createSpectroClipSet: unknown clip ${id}`);
    // Bake without a per-clip HUD; the set owns one shared HUD.
    const tl = await createSpectroTimeline({
      url: desc.url,
      fftSize: opts.fftSize,
      hopSize: opts.hopSize,
      buildHud: false,
    });
    baked.set(id, tl);
    return tl;
  }

  const firstId = opts.initialId && clips.some((c) => c.id === opts.initialId)
    ? opts.initialId
    : clips[0].id;
  const first = await bake(firstId);

  const hud = wantHud ? new SpectroHud(first.authority, first.cache, opts.hud) : null;

  const set: SpectroClipSet = {
    hud,
    activeId: firstId,
    authority: first.authority,
    features: first.features,
    clips,
    async select(id: string) {
      if (id === set.activeId) return;
      const prev = set.activeId ? baked.get(set.activeId) : null;
      prev?.authority.pause();
      const tl = await bake(id);
      set.activeId = id;
      set.authority = tl.authority;
      set.features = tl.features;
      hud?.bindClip(tl.authority, tl.cache);
      for (const fn of listeners) fn(id);
    },
    onChange(fn) {
      listeners.add(fn);
      return () => {
        listeners.delete(fn);
      };
    },
    dispose() {
      listeners.clear();
      hud?.dispose();
      for (const tl of baked.values()) tl.dispose();
      baked.clear();
    },
  };
  return set;
}

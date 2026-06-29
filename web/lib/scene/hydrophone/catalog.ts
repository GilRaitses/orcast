// Real multi-station hydrophone catalog for the station player.
//
// SOURCE OF TRUTH. The station list mirrors what the backend route
// `GET /api/live-hydrophones` serves: it maps `src/integrations/
// orcasound_hydrophones_for_orcast.json` through `OrcasoundHydrophoneAdapter`
// and filters to `SAN_JUAN_BOUNDS` (= the SalishScene TILESET_BOUNDS,
// 48.40-48.70 lat, -123.25 to -122.75 lng). Exactly three real Orcasound nodes
// fall inside the rendered tileset extent, so those are the stations the twin
// can actually place a rig at. The constants below are transcribed verbatim
// from that real catalog (id/name/slug/coords/visibility/imageUrl); nothing is
// invented.
//
// `streamUrl` is the Orcasound live-listen page built exactly as the adapter
// builds it: `https://live.orcasound.net/listen/{slug}`. Station coordinates,
// names, slugs, and live-listen links are metadata and are clear to display
// (BSW-R01; SIGN_OFF.md decision 1 authorizes the Orcasound source for
// non-commercial use, attribution recorded).
//
// HONESTY:
//   - placement (lat/lng) is MEASURED station metadata;
//   - the equipment `nodeClass` is a MODELED/representative assignment derived
//     from each node's Orcasound deployment description, not a claim about the
//     exact hardware currently in the water;
//   - `modeledFallbackDepthM` is a MODELED seabed depth used ONLY when no CUDEM
//     substrate sample is available (the sandbox); at integrate the substrate
//     sample at the real lat/lng supersedes it (see placement.ts);
//   - only Orcasound Lab has a license-clear archived clip in-repo; the other
//     nodes expose the live-listen link only. We never synthesise audio for a
//     station that has no bound clip.

import type { HydrophoneNode } from "@/lib/sceneIntent";
import { getJSON } from "@/lib/api";
import type { StationPlayerOptions } from "./StationPlayer";

/**
 * Equipment node class. A MODELED/representative grouping used to pick which
 * low-poly equipment mesh variant to show, NOT a claim about the exact current
 * hardware. `cabled` = a cabled shore hydrophone (element + housing on a seabed
 * frame, cable rising to a surface float). `mooring` = a subsurface mooring
 * (anchor, riser, subsurface buoyancy, mid-water element, thin tether to a
 * small surface marker).
 */
export type HydrophoneNodeClass = "cabled" | "mooring";

/** How the station's audio is bound. */
export type StationAudioKind = "archived-clip" | "live-listen-only";

/**
 * Audio binding for a station. `archived-clip` carries a decodable in-repo URL
 * (MEASURED real audio); `live-listen-only` carries just the Orcasound listen
 * link, because no license-clear archived clip is bound for that node. The UI
 * MUST display `attribution`.
 */
export interface StationAudioBinding {
  kind: StationAudioKind;
  /** Decodable real-audio URL, present only for `archived-clip`. */
  audioUrl?: string;
  /** Orcasound live-listen page (surfaced by the UI, never decoded here). */
  streamUrl: string | null;
  /** License string for the bound audio (archived clip only). */
  license?: string;
  /** Attribution string the UI MUST display. */
  attribution: string;
  /** Real audio is MEASURED, never synthesised. */
  honesty: "measured";
  /** Approximate clip duration in seconds (archived clip only). */
  durationS?: number;
  /** Provenance pointer (blog / bout narrative) for the archived clip. */
  provenanceUrl?: string;
}

/** A real station the twin can select, place, and (optionally) play. */
export interface StationCatalogEntry {
  id: string;
  name: string;
  slug: string;
  lat: number;
  lng: number;
  /** "online" when the node is visible/streaming, else "offline". */
  status: "online" | "offline";
  /** Orcasound live-listen page, or null when no slug. */
  streamUrl: string | null;
  source: "Orcasound";
  imageUrl: string | null;
  /** MODELED/representative equipment class (see HydrophoneNodeClass). */
  nodeClass: HydrophoneNodeClass;
  /** Always true for these constants: each is inside the rendered tileset. */
  withinTilesetExtent: boolean;
  /** MODELED seabed depth (metres, negative) used only without a substrate sample. */
  modeledFallbackDepthM: number;
  /** Audio binding (archived clip or live-listen only). */
  audio: StationAudioBinding;
}

const ATTRIBUTION = "Orcasound - orcasound.net";
const LISTEN_BASE = "https://live.orcasound.net/listen";

/** Build the live-listen URL exactly as the backend adapter does. */
export function listenUrl(slug: string | null | undefined): string | null {
  return slug ? `${LISTEN_BASE}/${slug}` : null;
}

// Slug -> MODELED equipment class, derived from each node's Orcasound
// deployment description in `live_orcasound_feeds.json`:
//   - orcasound-lab: HTI/Aquarian elements on cables, intertidal tie-downs -> cabled shore node.
//   - andrews-bay:   Dave Thaler test node between Orcasound Lab and Lime Kiln -> cabled shore node.
//   - north-sjc:     CRT-40 on a 60 m cable, "deeper and with electronics further from the
//                    intertidal" -> represented as a subsurface mooring.
// Unknown slugs fall back to the most common Orcasound deployment (cabled).
const NODE_CLASS_BY_SLUG: Record<string, HydrophoneNodeClass> = {
  "orcasound-lab": "cabled",
  "andrews-bay": "cabled",
  "north-sjc": "mooring",
};

/**
 * MODELED/representative node-class assignment for a station slug or id. This is
 * a presentation choice (which mesh variant to show), not a hardware claim.
 */
export function classifyNodeClass(slugOrId: string | null | undefined): HydrophoneNodeClass {
  if (!slugOrId) return "cabled";
  const key = slugOrId.replace(/^rpi_/, "").replace(/_/g, "-");
  return NODE_CLASS_BY_SLUG[key] ?? NODE_CLASS_BY_SLUG[slugOrId] ?? "cabled";
}

// The one license-clear archived clip in the repo (the BSW demo slice). Bound to
// Orcasound Lab only; see web/public/hydrophone/slice/PROVENANCE.md.
const SLICE_CLIP_AUDIO: StationAudioBinding = {
  kind: "archived-clip",
  audioUrl: "/hydrophone/slice/orcasound_lab_20210825_srkw.m4a",
  streamUrl: listenUrl("orcasound-lab"),
  license: "CC BY-NC-SA 4.0",
  attribution: "Audio: Orcasound (CC BY-NC-SA 4.0)",
  honesty: "measured",
  durationS: 178.5,
  provenanceUrl:
    "https://www.orcasound.net/2021/08/25/exciting-s10-l-pod-calls-as-the-sun-sets-over-orcasound-lab/",
};

function liveListenOnly(slug: string): StationAudioBinding {
  return {
    kind: "live-listen-only",
    streamUrl: listenUrl(slug),
    attribution: "Audio: Orcasound (CC BY-NC-SA 4.0)",
    honesty: "measured",
  };
}

/**
 * The real in-extent station catalog (the three Orcasound nodes inside the
 * SalishScene tileset, exactly the set `GET /api/live-hydrophones` returns).
 * Transcribed verbatim from `orcasound_hydrophones_for_orcast.json` /
 * `live_orcasound_feeds.json`.
 */
export const STATION_CATALOG: StationCatalogEntry[] = [
  {
    id: "rpi_orcasound_lab",
    name: "Orcasound Lab",
    slug: "orcasound-lab",
    lat: 48.5583362,
    lng: -123.1735774,
    status: "online",
    streamUrl: listenUrl("orcasound-lab"),
    source: "Orcasound",
    imageUrl: "https://s3-us-west-2.amazonaws.com/orcasite/rpi_orcasound_lab/thumbnail.png",
    nodeClass: "cabled",
    withinTilesetExtent: true,
    modeledFallbackDepthM: -18,
    audio: SLICE_CLIP_AUDIO,
  },
  {
    id: "rpi_north_sjc",
    name: "North San Juan Channel",
    slug: "north-sjc",
    lat: 48.591294,
    lng: -123.058779,
    status: "online",
    streamUrl: listenUrl("north-sjc"),
    source: "Orcasound",
    imageUrl: "https://s3-us-west-2.amazonaws.com/orcasite/rpi_north_sjc/thumbnail.png",
    nodeClass: "mooring",
    withinTilesetExtent: true,
    modeledFallbackDepthM: -30,
    audio: liveListenOnly("north-sjc"),
  },
  {
    id: "rpi_andrews_bay",
    name: "Andrews Bay",
    slug: "andrews-bay",
    lat: 48.5500299,
    lng: -123.1666492,
    status: "offline",
    streamUrl: listenUrl("andrews-bay"),
    source: "Orcasound",
    imageUrl: null,
    nodeClass: "cabled",
    withinTilesetExtent: true,
    modeledFallbackDepthM: -12,
    audio: liveListenOnly("andrews-bay"),
  },
];

/** All baked real stations. */
export function listStations(): StationCatalogEntry[] {
  return STATION_CATALOG;
}

/** Stations the twin can place a rig at (inside the rendered tileset extent). */
export function listSelectableStations(): StationCatalogEntry[] {
  return STATION_CATALOG.filter((s) => s.withinTilesetExtent);
}

/** Look up a station by id or slug. */
export function getStation(idOrSlug: string | null | undefined): StationCatalogEntry | null {
  if (!idOrSlug) return null;
  return (
    STATION_CATALOG.find((s) => s.id === idOrSlug || s.slug === idOrSlug) ?? null
  );
}

/**
 * Map a station's audio binding to `StationPlayer` options. A `live-listen-only`
 * station gets a null `audioUrl`, so the player stays in the honest `unbound`
 * state and surfaces just the live-listen link. No audio is invented.
 */
export function stationPlayerOptions(entry: StationCatalogEntry): StationPlayerOptions {
  return {
    audioUrl: entry.audio.kind === "archived-clip" ? entry.audio.audioUrl ?? null : null,
    streamUrl: entry.audio.streamUrl,
    attribution: entry.audio.attribution,
  };
}

// Per-slug modeled fallback seabed depth (metres, negative). Used only when no
// CUDEM substrate sample is available. Representative nearshore values; the
// substrate sample at the real lat/lng supersedes these at integrate.
const FALLBACK_DEPTH_BY_SLUG: Record<string, number> = {
  "orcasound-lab": -18,
  "north-sjc": -30,
  "andrews-bay": -12,
};

const DEFAULT_FALLBACK_DEPTH_M = -18;

/**
 * Map one `HydrophoneNode` (as returned by `GET /api/live-hydrophones`) into a
 * `StationCatalogEntry`, reusing the same node-class + depth heuristics. The
 * live API record carries no archived clip, so a station gets the in-repo clip
 * only when its id matches the bound slice clip; everything else is
 * live-listen-only. No audio is invented.
 */
export function entryFromNode(node: HydrophoneNode): StationCatalogEntry {
  const slug =
    typeof node.id === "string" ? node.id.replace(/^rpi_/, "").replace(/_/g, "-") : "";
  const streamUrl = node.streamUrl ?? listenUrl(slug);
  const isSliceStation = node.id === "rpi_orcasound_lab";
  return {
    id: String(node.id ?? slug),
    name: node.name ?? node.location ?? slug,
    slug,
    lat: node.latitude,
    lng: node.longitude,
    status: node.status === "offline" ? "offline" : "online",
    streamUrl,
    source: "Orcasound",
    imageUrl: (node as { imageUrl?: string | null }).imageUrl ?? null,
    nodeClass: classifyNodeClass(slug || String(node.id ?? "")),
    withinTilesetExtent: true, // the route already filters to SAN_JUAN_BOUNDS
    modeledFallbackDepthM: FALLBACK_DEPTH_BY_SLUG[slug] ?? DEFAULT_FALLBACK_DEPTH_M,
    audio: isSliceStation ? SLICE_CLIP_AUDIO : liveListenOnly(slug),
  };
}

/**
 * Fetch the live station catalog from `GET /api/live-hydrophones` (same proxy
 * path SalishScene uses) and map it to `StationCatalogEntry[]`. For the
 * integrator: drives the rig + player from the real served catalog rather than
 * the baked constants. Throws on a non-OK response (never falls back to fake
 * data; the caller may catch and use `STATION_CATALOG`).
 */
export async function fetchLiveHydrophones(): Promise<{
  stations: StationCatalogEntry[];
  source: "live-api";
}> {
  const res = await getJSON<{ data?: HydrophoneNode[]; hydrophones?: HydrophoneNode[] }>(
    "/api/live-hydrophones",
  );
  const list = res.hydrophones ?? res.data ?? [];
  const stations = list
    .filter((n) => Number.isFinite(n?.latitude) && Number.isFinite(n?.longitude))
    .map(entryFromNode);
  return { stations, source: "live-api" };
}

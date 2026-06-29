// Fetch helpers for the two precomputed real artifacts the reenactment consumes:
// the acoustic classification (BAM) and the behavior-clip manifest (derived
// offline from the measured SRKW driver).

import type { AcousticClassificationRecord, ClipManifest } from "./types";

export const CLASSIFICATION_URL =
  "/hydrophone/slice/classification.json";
export const CLIP_MANIFEST_URL =
  "/orca/motion/clips/manifest.json";

export async function loadClassification(
  url: string = CLASSIFICATION_URL,
): Promise<AcousticClassificationRecord> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`classification fetch failed: ${r.status} ${url}`);
  return (await r.json()) as AcousticClassificationRecord;
}

export async function loadClipManifest(
  url: string = CLIP_MANIFEST_URL,
): Promise<ClipManifest> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`clip manifest fetch failed: ${r.status} ${url}`);
  return (await r.json()) as ClipManifest;
}

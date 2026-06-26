const STALE_QC_PATTERN =
  /Level 0 detector QC is not yet (complete|available)/i;

const ACTIVE_QC_MESSAGE =
  "Spike-train fit uses unreviewed acoustic candidates; Level 0 QC reports reviewed outcome mix separately.";

/** Align API caveat strings with live Level 0 QC status (backend may lag deploy). */
export function normalizeIntegrityConditions(
  items: string[] | undefined,
  level0?: { status?: string } | null
): string[] {
  if (!items?.length) return [];
  if (level0?.status !== "active") return items;
  return items.map((item) =>
    STALE_QC_PATTERN.test(item) ? ACTIVE_QC_MESSAGE : item
  );
}

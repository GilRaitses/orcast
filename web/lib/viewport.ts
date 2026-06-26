export interface MapViewport {
  lat: number;
  lng: number;
  zoom?: number;
}

export function parseViewport(
  params: URLSearchParams | { get(name: string): string | null }
): MapViewport | null {
  const latRaw = params.get("lat");
  const lngRaw = params.get("lng");
  if (!latRaw || !lngRaw) return null;
  const lat = Number(latRaw);
  const lng = Number(lngRaw);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  const zoomRaw = params.get("zoom");
  const zoom = zoomRaw ? Number(zoomRaw) : undefined;
  return { lat, lng, zoom: Number.isFinite(zoom) ? zoom : undefined };
}

export function viewportQuery(viewport: MapViewport, extra?: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  q.set("lat", viewport.lat.toFixed(5));
  q.set("lng", viewport.lng.toFixed(5));
  if (viewport.zoom != null) q.set("zoom", String(viewport.zoom));
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      if (value != null && value !== "") q.set(key, value);
    }
  }
  return q.toString();
}

export function provenanceHref(viewport: MapViewport): string {
  return `/?${viewportQuery(viewport, { provenance: "1" })}`;
}

export function exploreHref(viewport: MapViewport): string {
  return `/explore?${viewportQuery(viewport)}`;
}

export function parseProvenanceFlag(params: URLSearchParams | { get(name: string): string | null }): boolean {
  return params.get("provenance") === "1";
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps";
import ProvenanceModal from "./ProvenanceModal";
import {
  parseProvenanceFlag,
  parseViewport,
  provenanceHref,
  viewportQuery,
  type MapViewport,
} from "@/lib/viewport";

export interface EventPoint {
  id: string;
  lat: number;
  lng: number;
  source: string;
}

const SAN_JUAN_CENTER = { lat: 48.55, lng: -123.05 };

export default function MapHero({
  events,
  initialViewport = null,
  openProvenanceOnLoad = false,
}: {
  events: EventPoint[];
  initialViewport?: MapViewport | null;
  openProvenanceOnLoad?: boolean;
}) {
  const key = process.env.NEXT_PUBLIC_MAPS_KEY;
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pick, setPick] = useState<MapViewport | null>(initialViewport);
  const [showProvenance, setShowProvenance] = useState(openProvenanceOnLoad && !!initialViewport);

  useEffect(() => {
    const vp = parseViewport(searchParams);
    if (vp) {
      setPick(vp);
      if (parseProvenanceFlag(searchParams)) setShowProvenance(true);
    }
  }, [searchParams]);

  function selectPoint(lat: number, lng: number) {
    const vp = { lat, lng, zoom: 10 };
    setPick(vp);
    setShowProvenance(true);
    router.replace(`/?${viewportQuery(vp, { provenance: "1" })}`, { scroll: false });
  }

  if (!key) {
    return (
      <div className="card" style={{ height: 360, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p className="muted">
          Set NEXT_PUBLIC_MAPS_KEY to render the map. Click-to-trace provenance still works via the list below.
        </p>
      </div>
    );
  }

  const center = pick ?? SAN_JUAN_CENTER;

  return (
    <>
      <div className="card" style={{ height: 420, padding: 0, overflow: "hidden" }}>
        <APIProvider apiKey={key}>
          <Map
            mapId="orcast-forecast"
            defaultCenter={center}
            defaultZoom={pick?.zoom ?? 10}
            gestureHandling="greedy"
            disableDefaultUI={false}
            onClick={(e) => {
              const ll = e.detail.latLng;
              if (ll) selectPoint(ll.lat, ll.lng);
            }}
            style={{ width: "100%", height: "100%" }}
          >
            {events.map((ev) => (
              <AdvancedMarker key={ev.id} position={{ lat: ev.lat, lng: ev.lng }} title={ev.source} />
            ))}
            {pick && <AdvancedMarker position={pick} title="Selected cell" />}
          </Map>
        </APIProvider>
      </div>
      <p className="muted" style={{ fontSize: "0.88rem" }}>
        Click or tap the water to trace why the forecast looks the way it does there.{" "}
        {pick && (
          <Link href={`/explore?${viewportQuery(pick)}`} className="chip" style={{ marginLeft: "0.35rem" }}>
            Open in exploration guide →
          </Link>
        )}
      </p>
      {pick && showProvenance && (
        <ProvenanceModal lat={pick.lat} lng={pick.lng} onClose={() => setShowProvenance(false)} />
      )}
    </>
  );
}

export { provenanceHref };

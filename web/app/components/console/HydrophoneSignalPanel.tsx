"use client";

import { useEffect, useState } from "react";
import GatedAction from "@/app/components/ui/GatedAction";

interface OncSignalResponse {
  status: string;
  enabled: boolean;
  station?: { name?: string; locationCode?: string; lat?: number; lng?: number } | null;
  spectrogram_url?: string | null;
  spectrogram_obtained_at?: string | null;
  data_product?: string | null;
  annotations_available?: boolean;
  message?: string | null;
}

export interface HydrophoneSignalProps {
  station?: string | null;
  lat?: number | null;
  lng?: number | null;
}

export default function HydrophoneSignalPanel({
  props,
  signedIn,
}: {
  props?: HydrophoneSignalProps;
  signedIn: boolean;
}) {
  const [data, setData] = useState<OncSignalResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams();
    if (props?.station) params.set("station", props.station);
    if (props?.lat != null) params.set("lat", String(props.lat));
    if (props?.lng != null) params.set("lng", String(props.lng));
    setLoading(true);
    setFailed(false);
    fetch(`/api/be/api/onc/hydrophone-signal?${params.toString()}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((d: OncSignalResponse) => setData(d))
      .catch(() => setFailed(true))
      .finally(() => setLoading(false));
  }, [props?.station, props?.lat, props?.lng]);

  return (
    <div className="console-panel" data-panel="hydrophone_signal">
      <h3 className="console-panel-title">Hydrophone signal</h3>
      {loading && <p className="muted">Loading hydrophone signal…</p>}
      {failed && <p className="muted">Hydrophone signal service unavailable.</p>}
      {data && (
        <>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {data.station?.name ?? props?.station ?? "Salish Sea hydrophone"}
            {data.station?.locationCode ? ` · ${data.station.locationCode}` : ""}
          </p>
          {data.enabled && data.spectrogram_url ? (
            <img
              src={data.spectrogram_url}
              alt="Recent ONC hydrophone spectrogram"
              className="hydrophone-spectrogram"
              loading="lazy"
            />
          ) : (
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              {data.message ??
                "Live ONC spectrogram requires ONC_API_TOKEN on the backend. Station metadata shown."}
            </p>
          )}
          {data.data_product && (
            <p className="muted" style={{ fontSize: "0.75rem" }}>
              Data product: {data.data_product}
            </p>
          )}
          <div className="row" style={{ marginTop: "0.6rem" }}>
            <GatedAction
              label="Annotate this detection"
              signedIn={signedIn}
              reason="Sign in to submit a hydrophone annotation"
              redirectTo="/explore"
            />
          </div>
        </>
      )}
    </div>
  );
}

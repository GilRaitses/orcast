"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSONResult, ProvenanceResponse } from "@/lib/api";
import IntegrityConditions from "@/app/components/IntegrityConditions";

function passBadge(v: boolean | null | undefined) {
  if (v === true) return <span className="badge pass">beats null</span>;
  if (v === false) return <span className="badge fail">no signal</span>;
  return <span className="badge warn">n/a</span>;
}

export default function ProvenanceModal({
  lat,
  lng,
  onClose,
}: {
  lat: number;
  lng: number;
  onClose: () => void;
}) {
  const [data, setData] = useState<ProvenanceResponse | null>(null);
  const [outOfRegion, setOutOfRegion] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setOutOfRegion(false);
    setError(null);
    getJSONResult<ProvenanceResponse>(`/api/provenance?lat=${lat}&lng=${lng}`)
      .then((res) => {
        if (cancelled) return;
        if (res.ok && res.data) {
          setData(res.data);
        } else if (res.status === 422) {
          setOutOfRegion(true);
        } else {
          setError("Could not trace provenance for this point. Please try again.");
        }
      })
      .catch(() => {
        if (!cancelled) setError("Could not trace provenance for this point. Please try again.");
      });
    return () => {
      cancelled = true;
    };
  }, [lat, lng]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
        <div className="modal" data-demo="provenance-modal" onClick={(e) => e.stopPropagation()}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Why is this cell hot?</h3>
          <button className="btn ghost" onClick={onClose}>Close</button>
        </div>
        <p className="muted">
          {lat.toFixed(3)}, {lng.toFixed(3)}
        </p>

        {outOfRegion && (
          <div className="callout">
            <p className="callout-title">Outside the modeled region</p>
            <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
              This point is outside the modeled San Juan Islands region. The forecast is only fit within the pilot
              bounds, so there is no provenance to trace here.
            </p>
            <p style={{ marginTop: "0.75rem", marginBottom: 0, fontSize: "0.88rem" }}>
              <Link href="/gates" onClick={onClose}>See how this forecast earns its confidence →</Link>
            </p>
          </div>
        )}
        {error && <p className="badge fail">{error}</p>}
        {!data && !error && !outOfRegion && <p className="muted">Tracing provenance...</p>}

        {data && (
          <>
            <p>
              Modeled intensity: <strong>{data.intensity.toFixed(4)}</strong> · confidence{" "}
              {Math.round(((data.effective_confidence ?? data.confidence) ?? 0) * 100)}%
            </p>
            {(data.caveats ?? []).length > 0 && (
              <IntegrityConditions
                items={data.caveats ?? []}
                title="Integrity conditions for this fit"
              />
            )}
            {data.spatial && data.spatial.modeled === false && (
              <div className="callout">
                <p className="callout-title">Temporal-only. Latitude not modeled</p>
                <p className="muted" style={{ margin: 0, fontSize: "0.88rem" }}>
                  {data.spatial.note ??
                    "This forecast models timing, not space. The same intensity applies across the region; the marker location does not change the prediction."}
                </p>
              </div>
            )}
            <h4>Kernel contributions</h4>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Kernel</th>
                    <th>Phase</th>
                    <th>log-rate</th>
                    <th>Gate</th>
                  </tr>
                </thead>
                <tbody>
                  {data.kernel_contributions.map((k) => (
                    <tr key={k.kernel}>
                      <td>{k.kernel}</td>
                      <td>{k.available ? k.phase?.toFixed(3) : "n/a"}</td>
                      <td>{k.available ? k.log_rate_contribution?.toFixed(3) : "-"}</td>
                      <td>{passBadge(k.beats_null)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h4 style={{ marginTop: "1rem" }}>Nearby sightings (sample)</h4>
            {data.nearby_sample.length === 0 && <p className="muted">No recent sightings within range.</p>}
            {data.nearby_sample.length > 0 && (
              <div className="table-scroll">
                <table>
                  <thead>
                  <tr><th>Sighting</th><th>Source</th><th>Distance</th><th>When</th></tr>
                  </thead>
                  <tbody>
                    {data.nearby_sample.map((e) => (
                      <tr key={e.sighting_id}>
                        <td><code>{e.sighting_id}</code></td>
                        <td>{e.source}</td>
                        <td>{e.distance_km} km</td>
                        <td>{new Date(e.timestamp).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="muted trace-text" style={{ marginTop: "1rem", fontSize: "0.85rem" }}>
              {data.trace_note}
            </p>
            <p style={{ marginTop: "0.75rem", fontSize: "0.88rem" }}>
              <Link href="/gates" onClick={onClose}>See how this forecast earns its confidence →</Link>
            </p>
            <p style={{ marginTop: "0.25rem", fontSize: "0.88rem" }}>
              <Link href="/review-dossier/latest" onClick={onClose}>Open the review dossier and audit packet →</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}

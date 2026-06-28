"use client";

/**
 * Kayak-branch console panel.
 *
 * Pure presentational component. It renders a go / no-go kayak window from a
 * MODELED tide / current series supplied as panel props. The series is produced
 * upstream by the harmonic predictor in modeling/tide_harmonic.py (fixed
 * M2/S2/N2/K1/O1 constituent basis, least-squares fit). The phase-B editor
 * wires the props source; this component performs no I/O and owns no camera.
 *
 * Honesty: the tide / current windows are a harmonic prediction, not observed
 * currents, so the panel renders an explicit MODELED label plus the station and
 * basis it was fit to. Empty inputs render as "unknown", never as a safe zero.
 */

export type KayakWindowRating = "go" | "caution" | "no-go";

/** One modeled paddling window over the tide / current series. */
export interface KayakTideWindow {
  /** Window start, ISO datetime. */
  start: string;
  /** Window end, ISO datetime. */
  end: string;
  /** Go / no-go classification derived from the modeled current. */
  rating: KayakWindowRating;
  /** Peak modeled current magnitude across the window, knots. Harmonic prediction. */
  peakCurrentKnots?: number | null;
  /** Tidal phase in [0,1) at the window midpoint, from the fitted M2 constituent. */
  phase?: number | null;
  /** Short reason for the rating, e.g. "near slack" or "max flood". */
  note?: string | null;
}

/** A short-range launch point for the kayak branch. */
export interface KayakLaunchPoint {
  name: string;
  lat?: number | null;
  lng?: number | null;
  note?: string | null;
}

/** A short-range viewing zone reachable from the launch point. */
export interface KayakViewingZone {
  name: string;
  /** Approximate range from the launch point, meters. */
  rangeMeters?: number | null;
  note?: string | null;
}

/** Station and harmonic basis the modeled series was fit to. */
export interface KayakTideBasis {
  /** Display name of the station the harmonic model is anchored to. */
  station: string;
  /** Station identifier, e.g. a NOAA station id. */
  stationId?: string | null;
  lat?: number | null;
  lng?: number | null;
  /** Constituents in the fitted basis, e.g. ["M2","S2","N2","K1","O1"]. */
  constituents?: string[];
  /** Reconstruction R^2 numerical-sanity check reported by HarmonicTide. */
  reconstructionR2?: number | null;
  /** When the modeled series was generated, ISO datetime. */
  generatedAt?: string | null;
}

export interface KayakPanelProps {
  /** Station and harmonic basis behind the modeled windows. */
  basis?: KayakTideBasis | null;
  /** Ordered modeled paddling windows. Empty means "unknown", not "no windows". */
  windows?: KayakTideWindow[];
  launchPoints?: KayakLaunchPoint[];
  viewingZones?: KayakViewingZone[];
  /** Plain safety framing lines shown beneath the windows. */
  safety?: string[];
}

const RATING_BADGE: Record<KayakWindowRating, string> = {
  go: "pass",
  caution: "caution",
  "no-go": "fail",
};

const RATING_LABEL: Record<KayakWindowRating, string> = {
  go: "Go",
  caution: "Caution",
  "no-go": "No-go",
};

function formatClock(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatPhase(phase: number | null | undefined): string | null {
  if (phase == null || Number.isNaN(phase)) return null;
  const pct = Math.round((((phase % 1) + 1) % 1) * 100);
  return `${pct}% through cycle`;
}

function formatGenerated(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function KayakPanel({ props }: { props?: KayakPanelProps }) {
  const basis = props?.basis ?? null;
  const windows = props?.windows ?? [];
  const launchPoints = props?.launchPoints ?? [];
  const viewingZones = props?.viewingZones ?? [];
  const safety = props?.safety ?? [];

  const generated = formatGenerated(basis?.generatedAt);
  const r2 = basis?.reconstructionR2;

  return (
    <div className="console-panel" data-panel="kayak_plan">
      <h3 className="console-panel-title">Kayak window</h3>

      <div
        className="console-card"
        style={{ marginBottom: "0.6rem", padding: "0.5rem 0.6rem" }}
      >
        <span className="badge warn">MODELED</span>
        <p className="muted" style={{ fontSize: "0.8rem", margin: "0.35rem 0 0" }}>
          Harmonic tide predictor, not observed currents.
        </p>
        {basis ? (
          <div className="console-metrics" style={{ marginTop: "0.4rem" }}>
            <div className="console-metric-row">
              <span>Station</span>
              <strong>
                {basis.station}
                {basis.stationId ? ` · ${basis.stationId}` : ""}
              </strong>
            </div>
            <div className="console-metric-row">
              <span>Basis</span>
              <span className="muted" style={{ fontSize: "0.82rem" }}>
                {basis.constituents && basis.constituents.length > 0
                  ? `${basis.constituents.join("/")} harmonic fit`
                  : "Least-squares harmonic fit"}
              </span>
            </div>
            {r2 != null && !Number.isNaN(r2) && (
              <div className="console-metric-row">
                <span>Reconstruction R²</span>
                <strong>{r2.toFixed(2)}</strong>
              </div>
            )}
            {generated && (
              <div className="console-metric-row">
                <span>Modeled as of</span>
                <span className="muted" style={{ fontSize: "0.82rem" }}>
                  {generated}
                </span>
              </div>
            )}
          </div>
        ) : (
          <p className="muted" style={{ fontSize: "0.8rem", margin: "0.35rem 0 0" }}>
            Station and basis unknown.
          </p>
        )}
      </div>

      {windows.length > 0 ? (
        <ul className="console-gate-list" style={{ gap: "0.5rem" }}>
          {windows.map((w, i) => {
            const phaseText = formatPhase(w.phase);
            return (
              <li
                key={`${w.start}-${i}`}
                style={{ alignItems: "flex-start", flexDirection: "column", gap: "0.2rem" }}
              >
                <div className="row" style={{ gap: "0.5rem", alignItems: "center" }}>
                  <span className={`badge ${RATING_BADGE[w.rating]}`}>
                    {RATING_LABEL[w.rating]}
                  </span>
                  <strong style={{ fontSize: "0.86rem" }}>
                    {formatClock(w.start)} to {formatClock(w.end)}
                  </strong>
                </div>
                <span className="muted" style={{ fontSize: "0.78rem" }}>
                  {w.peakCurrentKnots != null
                    ? `Modeled peak current ${w.peakCurrentKnots.toFixed(1)} kn`
                    : "Modeled current unknown"}
                  {phaseText ? `, ${phaseText}` : ""}
                  {w.note ? `. ${w.note}` : ""}
                </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="muted" style={{ fontSize: "0.84rem" }}>
          No modeled windows available. Treat the current state as unknown, not as
          safe water.
        </p>
      )}

      {launchPoints.length > 0 && (
        <div style={{ marginTop: "0.7rem" }}>
          <span className="console-panel-label">Launch points</span>
          <ul className="console-gate-list">
            {launchPoints.map((p, i) => (
              <li key={`${p.name}-${i}`}>
                <span className="gate-dot ok" />
                <span style={{ fontSize: "0.84rem" }}>
                  {p.name}
                  {p.note ? (
                    <span className="muted"> {p.note}</span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {viewingZones.length > 0 && (
        <div style={{ marginTop: "0.7rem" }}>
          <span className="console-panel-label">Short-range viewing zones</span>
          <ul className="console-gate-list">
            {viewingZones.map((z, i) => (
              <li key={`${z.name}-${i}`}>
                <span className="gate-dot unknown" />
                <span style={{ fontSize: "0.84rem" }}>
                  {z.name}
                  {z.rangeMeters != null ? (
                    <span className="muted"> within {z.rangeMeters} m</span>
                  ) : null}
                  {z.note ? <span className="muted"> {z.note}</span> : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {safety.length > 0 && (
        <div style={{ marginTop: "0.7rem" }}>
          <span className="console-panel-label">Safety</span>
          <ul className="console-gate-list">
            {safety.map((line, i) => (
              <li key={i}>
                <span className="gate-dot fail" />
                <span className="muted" style={{ fontSize: "0.8rem" }}>
                  {line}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

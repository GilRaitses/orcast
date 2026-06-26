import IntegrityConditions from "@/app/components/IntegrityConditions";

export function ConfidenceMeter({
  confidence,
  promoted,
  caveats = [],
}: {
  confidence: number | null;
  promoted?: boolean;
  caveats?: string[];
}) {
  const pct = Math.round((confidence ?? 0) * 100);
  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="confidence-label">Forecast confidence</div>
          <div className="confidence-pct">{pct}%</div>
        </div>
        {promoted ? <span className="badge pass">human-promoted</span> : <span className="badge warn">unpromoted</span>}
      </div>
      <div className="confidence-bar" style={{ marginTop: 12 }}>
        <span style={{ width: `${pct}%` }} />
      </div>
      <p className="muted" style={{ marginTop: 8, fontSize: "0.88rem" }}>
        The forecast is always shown. Its sharpness is governed by the fitness gates and a human
        promotion step, not hidden behind an "experimental" label.
      </p>
      {caveats.length > 0 && <IntegrityConditions items={caveats} compact />}
    </div>
  );
}

export function ConfidenceMeterSkeleton() {
  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div className="confidence-label">Forecast confidence</div>
          <div className="skeleton" style={{ width: 120, height: 48, marginTop: 6 }} />
        </div>
        <div className="skeleton" style={{ width: 96, height: 22, borderRadius: 999 }} />
      </div>
      <div className="skeleton" style={{ height: 10, marginTop: 12, borderRadius: 999 }} />
      <div className="skeleton" style={{ height: 14, marginTop: 12, width: "90%" }} />
      <div className="skeleton" style={{ height: 14, marginTop: 6, width: "75%" }} />
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getJSON, ReviewDossier, ReviewDossierResponse } from "@/lib/api";
import IntegrityConditions from "@/app/components/IntegrityConditions";
import PromotionBreadcrumb from "@/app/components/PromotionBreadcrumb";

export default function LatestReviewDossierPage() {
  const [dossier, setDossier] = useState<ReviewDossier | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  useEffect(() => {
    getJSON<ReviewDossierResponse>("/api/review-dossier/latest")
      .then((res) => setDossier(res.dossier))
      .catch((e) => {
        if (/->\s*401/.test(String(e))) setNeedsAuth(true);
        setError(`Could not load review dossier: ${e}`);
      });
  }, []);

  async function downloadExport() {
    if (!dossier) return;
    const res = await getJSON<{ export: unknown }>(`/api/review-dossier/${dossier.dossier_id}/export`);
    const blob = new Blob([JSON.stringify(res.export, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${dossier.dossier_id}.audit.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (needsAuth) {
    return (
      <main className="container">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Review dossier</h2>
          <p>Reviewer access required. <Link href="/login">Sign in</Link></p>
        </div>
      </main>
    );
  }

  if (!dossier) {
    return (
      <main className="container">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Review dossier</h2>
          {error ? <p className="badge fail">{error}</p> : <p className="muted">Loading dossier...</p>}
        </div>
      </main>
    );
  }

  const decision = dossier.human_decision;
  const caveats = dossier.model_card.caveats ?? [];

  return (
    <main className="container">
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>
            <h2 style={{ marginTop: 0 }}>Review dossier</h2>
            <p className="muted">Dossier <code>{dossier.dossier_id}</code> · {dossier.workflow_stage}</p>
          </div>
          <button className="btn" onClick={downloadExport}>Download audit packet</button>
        </div>
        <PromotionBreadcrumb
          reprId={dossier.provenance.repr_id}
          runId={dossier.provenance.run_id}
          decisionId={decision?.id}
          promoted={dossier.model_card.promoted}
        />
      </div>

      <div className="grid2">
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Model card lite</h3>
          <p>Raw confidence: {Math.round((dossier.model_card.confidence_raw ?? 0) * 100)}%</p>
          <p>Effective confidence: {Math.round((dossier.model_card.confidence_effective ?? 0) * 100)}%</p>
          <p>Covariates: {(dossier.model_card.covariates_fit ?? []).join(", ") || "n/a"}</p>
          {caveats.length > 0 && <IntegrityConditions items={caveats} title="Integrity conditions" />}
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Decision</h3>
          {decision ? (
            <>
              <p>Verdict: <strong>{decision.verdict}</strong></p>
              <p>Reviewer: {decision.reviewer_email || decision.reviewer || decision.reviewer_id || "unknown"}</p>
              <p>Reason: {decision.reason || "-"}</p>
              <p><Link href="/decisions">Open full decision log</Link></p>
            </>
          ) : (
            <p className="muted">No human decision has been recorded for this dossier yet.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Artifact references</h3>
        <div className="table-scroll">
          <table>
            <tbody>
              {Object.entries(dossier.provenance.artifact_refs ?? {}).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td><code>{String(v ?? "n/a")}</code></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>PROV-lite edges</h3>
        <div className="table-scroll">
          <table>
            <tbody>
              {(dossier.prov?.edges ?? []).map((e, i) => (
                <tr key={i}>
                  <td>{String(e.subject)}</td>
                  <td>{String(e.predicate)}</td>
                  <td>{String(e.object)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}

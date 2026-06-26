"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON, postJSON, GatesResponse } from "@/lib/api";
import {
  cvDisplayExplainer,
  cvDisplayLabel,
  cvDisplayStatus,
  type GateDisplayStatus,
} from "@/lib/gateDisplay";
import { normalizeIntegrityConditions } from "@/lib/integrityConditions";
import PromotionBreadcrumb from "@/app/components/PromotionBreadcrumb";
import IntegrityConditions from "@/app/components/IntegrityConditions";
import Level1PsthSection from "@/app/components/Level1PsthSection";
import GlossaryTerm from "@/app/components/GlossaryTerm";

function PassBadge({ v }: { v: boolean | null | undefined }) {
  if (v === true) return <span className="badge pass">pass</span>;
  if (v === false) return <span className="badge fail">fail</span>;
  return <span className="badge warn">n/a</span>;
}

function CvGateBadge({ status }: { status: GateDisplayStatus }) {
  const label = cvDisplayLabel(status);
  const className =
    status === "pass"
      ? "badge pass"
      : status === "caution"
        ? "badge caution"
        : status === "fail"
          ? "badge fail"
          : "badge warn";
  return <span className={className}>{label}</span>;
}

type GatesWithApproval = GatesResponse;

function GatesSkeleton() {
  return (
    <main className="container">
      <div className="card">
        <div className="skeleton" style={{ height: 26, width: 200 }} />
        <div className="skeleton" style={{ height: 16, width: "70%", marginTop: 14 }} />
        <div className="skeleton" style={{ height: 16, width: "55%", marginTop: 8 }} />
      </div>
      <div className="card">
        <div className="skeleton" style={{ height: 18, width: 260 }} />
        <div className="skeleton" style={{ height: 120, marginTop: 14 }} />
      </div>
    </main>
  );
}

function formatOutcomeCounts(counts: Record<string, number> | undefined) {
  if (!counts) return null;
  return Object.entries(counts)
    .map(([k, v]) => `${k}: ${v}`)
    .join(" · ");
}

export default function GatesPage() {
  const [g, setG] = useState<GatesWithApproval | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  async function load() {
    setG(await getJSON<GatesWithApproval>("/api/gates"));
  }
  useEffect(() => {
    load();
  }, []);

  async function decide(verdict: "promote" | "hold" | "reject") {
    if (!g?.pending_approval) return;
    setBusy(true);
    setMsg(null);
    try {
      await postJSON("/api/decision-records", {
        verdict,
        reason:
          verdict === "promote"
            ? "Gates and supervisor support promotion"
            : verdict === "hold"
              ? "Hold for more evidence before promotion"
              : "Insufficient out-of-sample skill",
      });
      setMsg(`Recorded ${verdict}. Orchestrator resumed.`);
      await load();
    } catch (e) {
      if (/->\s*401/.test(String(e))) setNeedsAuth(true);
      else setMsg(`Failed: ${e}`);
    } finally {
      setBusy(false);
    }
  }

  if (!g) return <GatesSkeleton />;

  const l1 = g.gates?.level1_psth ?? {};
  const cv = g.gates?.cross_validation ?? {};
  const tr = g.gates?.time_rescaling ?? {};
  const pit = g.gates?.pit ?? {};
  const cons = g.gates?.consistency ?? {};
  const inv = (g.data_inventory ?? {}) as Record<string, unknown>;
  const level0 = (g.level0_detector_qc ?? {}) as Record<string, any>;
  const baselines = (g.baseline_scorecard ?? {}) as Record<string, any>;
  const confPct = Math.round(((g.effective_confidence ?? g.confidence) ?? 0) * 100);
  const integrityConditions = normalizeIntegrityConditions(g.caveats, level0);
  const cvDisplay = cvDisplayStatus(cv);
  const cvExplainer = cvDisplayExplainer(cvDisplay);
  const negativeSkillCaveat = (g.caveats ?? []).find((c) =>
    c.toLowerCase().includes("mean held-out deviance skill is negative")
  );
  const fittedAt = g.generated_at ? new Date(g.generated_at) : null;
  const level0Active = level0.status === "active";

  return (
    <main className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>
          <GlossaryTerm id="fitness-gates">Fitness gates</GlossaryTerm>
        </h2>
        <p>
          Status: <strong>{g.status}</strong> · confidence {confPct}% ·{" "}
          {g.promoted ? <span className="badge pass">promoted</span> : <span className="badge warn">unpromoted</span>}
        </p>
        <IntegrityConditions items={integrityConditions} />
        <p className="muted">
          McFadden pseudo-R² vs climatology: {g.metrics?.mcfadden_r2?.toFixed(3) ?? "n/a"} · covariates:{" "}
          {(g.covariates_fit ?? []).join(", ") || "n/a"}
        </p>
        <p className="muted" style={{ fontSize: "0.85rem" }}>
          Acoustic: {String(inv.n_detections ?? "?")} detections, {String(inv.n_stations_acoustic ?? "?")} station(s).
          {inv.tide_overlaps_acoustic === false ? " Tide kernel withheld (no overlapping current data)." : ""}
        </p>
        <p className="muted" style={{ fontSize: "0.85rem" }}>
          Last fitted: {fittedAt ? fittedAt.toLocaleString() : "unknown"}
        </p>
        <PromotionBreadcrumb
          reprId={g.repr_id}
          runId={g.run_id}
          decisionId={(g.promotion as any)?.decision_id}
          promoted={g.promoted}
        />
        <details className="explainer">
          <summary>How gates relate to integrity conditions</summary>
          <p>
            <GlossaryTerm id="fitness-gates" asLink={false} /> are statistical pass/fail tests on the fit.
            <GlossaryTerm id="integrity-conditions" asLink={false} /> are scope disclosures (single station, tide overlap,
            detector QC) so the UI never oversells precision. Both appear on this page; neither is a generic
            &ldquo;caveat.&rdquo;{" "}
            <Link href="/glossary">Open the glossary →</Link>
          </p>
        </details>
      </div>

      {g.pending_approval && (
        <div className="card" style={{ borderColor: "var(--accent)" }}>
          <h3 style={{ marginTop: 0 }}>Human promotion decision required</h3>
          <p>
            Supervisor recommends:{" "}
            <strong>{g.pending_approval.recommendation?.recommendation ?? "hold"}</strong>
          </p>
          <p className="muted">{g.pending_approval.recommendation?.rationale}</p>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            Promoting applies a human-reviewed confidence marker; holding or rejecting keeps the forecast unpromoted
            until more evidence or the next fit.
          </p>
          <div className="row">
            <button className="btn" disabled={busy} onClick={() => decide("promote")}>Promote</button>
            <button className="btn ghost" disabled={busy} onClick={() => decide("hold")}>Hold</button>
            <button className="btn ghost" disabled={busy} onClick={() => decide("reject")}>Reject</button>
          </div>
        </div>
      )}
      {needsAuth && (
        <p className="muted">
          Reviewer access required to record a decision. <Link href="/login">Sign in</Link>
        </p>
      )}
      {msg && <p className="muted">{msg}</p>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>
          <GlossaryTerm id="level1-psth" />
        </h3>
        <Level1PsthSection rows={l1} />
      </div>

      <div className="grid2">
        <div className="card">
          <h3 style={{ marginTop: 0 }}>
            <GlossaryTerm id="level0-detector-qc" />
          </h3>
          <p>
            Status:{" "}
            <span className={level0Active ? "badge pass" : "badge warn"}>
              {String(level0.status ?? "not reported")}
            </span>
            {level0.truth_label ? ` · ${level0.truth_label}` : ""}
          </p>
          {level0Active ? (
            <>
              <p className="muted" style={{ fontSize: "0.9rem" }}>
                Reviewed labels: {level0.n_reviewed_labels ?? "?"} · confirmed fraction{" "}
                {level0.confirmed_fraction != null ? Number(level0.confirmed_fraction).toFixed(3) : "n/a"} · false-positive
                rate {level0.false_positive_rate != null ? Number(level0.false_positive_rate).toFixed(3) : "n/a"}
              </p>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {formatOutcomeCounts(level0.outcome_counts as Record<string, number>)}
              </p>
            </>
          ) : (
            <p className="muted">{String(level0.reason ?? "Detector characterization has not been reported yet.")}</p>
          )}
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Baseline scorecard</h3>
          <p>Climatology skill: {baselines.climatology?.mean_deviance_skill?.toFixed?.(3) ?? "n/a"}</p>
          <p className="muted">
            Single-covariate, persistence, and recent-density baselines:{" "}
            {baselines.single_covariate?.status ?? "planned"}.
          </p>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>
            <GlossaryTerm id="held-out-cv" />
          </h3>
          <p>Folds passing: {cv.n_pass ?? "?"}/{cv.n_folds ?? "?"}</p>
          <p>Mean deviance skill: {cv.mean_deviance_skill?.toFixed(3) ?? "n/a"}</p>
          <p>
            Gate: <CvGateBadge status={cvDisplay} />
          </p>
          {(cvExplainer || negativeSkillCaveat) && (
            <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.35rem" }}>
              {cvExplainer ?? negativeSkillCaveat}
            </p>
          )}
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>
            <GlossaryTerm id="time-rescaling" />
          </h3>
          <p>KS vs Exp(1) p: {tr.pooled_ks_exp_pval?.toFixed(3) ?? "n/a"}</p>
          <p>Pass: <PassBadge v={tr.pooled_pass_exp} /></p>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>
            <GlossaryTerm id="pit-calibration" />
          </h3>
          <p>KS vs Uniform p: {pit.ks_pval?.toFixed(3) ?? "n/a"}</p>
          <p>Calibrated: <PassBadge v={pit.calibrated} /></p>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>
            <GlossaryTerm id="psth-kernel-consistency" />
          </h3>
          <table>
            <tbody>
              {Object.entries(cons).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td>{v.correlation?.toFixed(2)}</td><td><PassBadge v={v.agrees} /></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}

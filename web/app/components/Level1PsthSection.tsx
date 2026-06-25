"use client";

import Link from "next/link";
import GlossaryTerm from "@/app/components/GlossaryTerm";

type L1Row = {
  modulation: number;
  null_z: number;
  null_p: number;
  beats_null: boolean;
};

function ModulationBar({ value }: { value: number }) {
  const pct = Math.min(100, Math.max(0, Math.abs(value) * 100));
  return (
    <div className="mod-bar" aria-label={`Modulation ${value.toFixed(3)}`}>
      <span style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function Level1PsthSection({ rows }: { rows: Record<string, L1Row> }) {
  const entries = Object.entries(rows);

  if (!entries.length) {
    return (
      <p className="muted">
        No Level 1 PSTH results in the current fit report.{" "}
        <Link href="/glossary#level1-psth">What is Level 1?</Link>
      </p>
    );
  }

  return (
    <div className="level1-block">
      <p className="muted" style={{ fontSize: "0.92rem", lineHeight: 1.55 }}>
        <GlossaryTerm id="level1-psth" /> compares each cyclic covariate&apos;s marginal PSTH against a
        phase-shuffle null. Hover the ⓘ icons for quick definitions; the{" "}
        <Link href="/glossary#level1-psth">glossary</Link> has full ontology and pipeline provenance.
      </p>

      <div className="level1-grid">
        {entries.map(([covariate, v]) => {
          return (
            <div key={covariate} className="level1-card">
              <div className="level1-card-head">
                <h4 style={{ margin: 0 }}>
                  <GlossaryTerm id="covariate">{covariate}</GlossaryTerm>
                </h4>
                <span className={v.beats_null ? "badge pass" : "badge fail"}>
                  {v.beats_null ? "beats null" : "no signal"}
                </span>
              </div>
              <dl className="level1-metrics">
                <div>
                  <dt><GlossaryTerm id="modulation" /></dt>
                  <dd>
                    {v.modulation?.toFixed(3)}
                    <ModulationBar value={v.modulation ?? 0} />
                  </dd>
                </div>
                <div>
                  <dt><GlossaryTerm id="null-z" /></dt>
                  <dd>{v.null_z?.toFixed(2)}</dd>
                </div>
                <div>
                  <dt><GlossaryTerm id="null-p" /></dt>
                  <dd>{v.null_p?.toFixed(3)}</dd>
                </div>
                <div>
                  <dt><GlossaryTerm id="beats-null" /></dt>
                  <dd>{v.beats_null ? "yes" : "no"}</dd>
                </div>
              </dl>
            </div>
          );
        })}
      </div>

      <div className="table-scroll" style={{ marginTop: "1rem" }}>
        <table className="level1-table">
          <thead>
            <tr>
              <th><GlossaryTerm id="covariate" /></th>
              <th><GlossaryTerm id="modulation" /></th>
              <th><GlossaryTerm id="null-z" /></th>
              <th><GlossaryTerm id="null-p" /></th>
              <th><GlossaryTerm id="beats-null" /></th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([k, v]) => (
              <tr key={k}>
                <td>{k}</td>
                <td>{v.modulation?.toFixed(3)}</td>
                <td>{v.null_z?.toFixed(2)}</td>
                <td>{v.null_p?.toFixed(3)}</td>
                <td>
                  <span className={v.beats_null ? "badge pass" : "badge fail"}>
                    {v.beats_null ? "pass" : "fail"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

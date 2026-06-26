"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DecisionRecord, DecisionRecordsResponse, getJSON } from "@/lib/api";

function VerdictBadge({ verdict }: { verdict: DecisionRecord["verdict"] }) {
  if (verdict === "promote") return <span className="badge pass">promote</span>;
  if (verdict === "reject") return <span className="badge fail">reject</span>;
  return <span className="badge warn">hold</span>;
}

export default function DecisionsPage() {
  const [records, setRecords] = useState<DecisionRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  useEffect(() => {
    getJSON<DecisionRecordsResponse>("/api/decision-records")
      .then((res) => setRecords(res.records ?? []))
      .catch((e) => {
        if (/->\s*401/.test(String(e))) setNeedsAuth(true);
        setError(`Could not load decision records: ${e}`);
      });
  }, []);

  return (
    <main className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Decision audit log</h2>
        <p className="muted">
          Human promotion, hold, and reject decisions are immutable audit records. Task tokens are never shown here.
        </p>
        {needsAuth && (
          <p>
            Reviewer access required. <Link href="/login">Sign in</Link>
          </p>
        )}
        {error && !needsAuth && <p className="badge fail">{error}</p>}
        {records === null && !error && <p className="muted">Loading decision records...</p>}
      </div>

      {records && records.length === 0 && (
        <div className="card">
          <p className="muted">No decision records have been written yet.</p>
        </div>
      )}

      {records && records.length > 0 && (
        <div className="card">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Verdict</th>
                  <th>Reviewer</th>
                  <th>Kernel version</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>{r.created_at ? new Date(r.created_at).toLocaleString() : "unknown"}</td>
                    <td><VerdictBadge verdict={r.verdict} /></td>
                    <td>{r.reviewer_email || r.reviewer || r.reviewer_id || "unknown"}</td>
                    <td>{r.kernel_version || "n/a"}</td>
                    <td>{r.reason || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}

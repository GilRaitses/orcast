"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON, postJSON } from "@/lib/api";

function isUnauthorized(e: unknown): boolean {
  return /->\s*401/.test(String(e));
}

interface Submission {
  id: string;
  place: string;
  latitude?: number | null;
  longitude?: number | null;
  observed_at: string;
  behavior: string;
  count?: number | null;
  notes?: string | null;
  observer_name?: string | null;
  status: string;
}

export default function ModerationPage() {
  const [subs, setSubs] = useState<Submission[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);
  const [loaded, setLoaded] = useState(false);

  async function load() {
    try {
      const res = await getJSON<{ submissions: Submission[] }>("/api/community/submissions?status=pending");
      setSubs(res.submissions ?? []);
      setNeedsAuth(false);
    } catch (e) {
      if (isUnauthorized(e)) setNeedsAuth(true);
      else setError(String(e));
    } finally {
      setLoaded(true);
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function moderate(id: string, action: "approve" | "reject") {
    setBusy(id);
    try {
      await postJSON(`/api/community/submissions/${id}/${action}`, {});
      await load();
    } catch (e) {
      if (isUnauthorized(e)) setNeedsAuth(true);
      else setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Community moderation queue</h2>
        <p className="muted">
          Shore sightings are quarantined here until a human approves. Approval attaches attribution
          and a low reliability weight before the observation can influence the model.
        </p>
        {needsAuth && (
          <p className="muted">
            Reviewer access required. <Link href="/login">Sign in</Link>
          </p>
        )}
        {error && <p className="badge fail">{error}</p>}
      </div>

      {!loaded && !needsAuth && (
        <div className="card">
          <div className="skeleton" style={{ height: 18, width: "40%" }} />
          <div className="skeleton" style={{ height: 14, width: "70%", marginTop: 12 }} />
          <div className="skeleton" style={{ height: 36, width: 200, marginTop: 16 }} />
        </div>
      )}

      {loaded && !needsAuth && subs.length === 0 && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>No pending submissions</h3>
          <p className="muted" style={{ marginBottom: 0 }}>
            The moderation queue is clear. New shore sightings will appear here for review.
          </p>
        </div>
      )}

      {subs.map((s) => (
        <div className="card interactive" key={s.id}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <strong>{s.place}</strong>
            <span className="badge warn">{s.status}</span>
          </div>
          <p className="muted">
            {new Date(s.observed_at).toLocaleString()} · {s.behavior}
            {s.count ? ` · ${s.count} animals` : ""} {s.observer_name ? `· ${s.observer_name}` : ""}
          </p>
          {s.notes && <p>{s.notes}</p>}
          {s.latitude != null && s.longitude != null && (
            <p className="muted">{s.latitude.toFixed(3)}, {s.longitude.toFixed(3)}</p>
          )}
          <div className="row">
            <button className="btn" disabled={busy === s.id} onClick={() => moderate(s.id, "approve")}>Approve</button>
            <button className="btn ghost" disabled={busy === s.id} onClick={() => moderate(s.id, "reject")}>Reject</button>
          </div>
        </div>
      ))}
    </main>
  );
}

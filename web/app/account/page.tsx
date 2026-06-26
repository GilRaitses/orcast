"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON } from "@/lib/api";

interface EvidenceAsset {
  id: string;
  kind: "image" | "audio" | "other";
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_uri: string;
  caption?: string;
  created_at: string;
  linked_to: { journal_entry_id: string | null; community_submission_id: string | null };
}

interface JournalEntry {
  id: string;
  kind: string;
  title: string;
  place?: string;
  behavior: string;
  count?: number;
  community_submission_id?: string;
  evidence_assets: EvidenceAsset[];
  created_at: string;
}

function fmtBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function KindBadge({ kind }: { kind: string }) {
  const cls = kind === "image" ? "badge pass" : kind === "audio" ? "badge warn" : "badge";
  return <span className={cls}>{kind}</span>;
}

export default function AccountPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [assets, setAssets] = useState<EvidenceAsset[]>([]);
  const [loadingEntries, setLoadingEntries] = useState(true);
  const [loadingAssets, setLoadingAssets] = useState(true);
  const [errorEntries, setErrorEntries] = useState<string | null>(null);
  const [errorAssets, setErrorAssets] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    getJSON<{ entries: JournalEntry[] }>("/api/be/api/journal/entries")
      .then((d) => setEntries(d.entries ?? []))
      .catch((e) => setErrorEntries(String(e)))
      .finally(() => setLoadingEntries(false));

    getJSON<{ assets: EvidenceAsset[] }>("/api/be/api/evidence/assets")
      .then((d) => setAssets(d.assets ?? []))
      .catch((e) => setErrorAssets(String(e)))
      .finally(() => setLoadingAssets(false));
  }, []);

  async function removeAsset(id: string) {
    setRemovingId(id);
    try {
      await fetch(`/api/be/api/evidence/assets/${id}`, { method: "DELETE" });
      setAssets((prev) => prev.filter((a) => a.id !== id));
    } finally {
      setRemovingId(null);
    }
  }

  // Derive published submissions from journal entries
  const publishedEntries = entries.filter((e) => e.community_submission_id);

  return (
    <main className="container">
      <h1 className="hero-title" style={{ fontSize: "1.75rem" }}>
        My content
      </h1>
      <p className="hero-subtitle">
        Your journal entries, uploaded evidence, and published community submissions.
      </p>

      {/* ── Journal entries ─────────────────────────────────────────── */}
      <section style={{ marginTop: "2rem" }}>
        <h2>Field journal</h2>
        {loadingEntries && <p className="muted">Loading…</p>}
        {errorEntries && <p className="badge fail">{errorEntries}</p>}
        {!loadingEntries && entries.length === 0 && !errorEntries && (
          <p className="muted">
            No journal entries yet.{" "}
            <Link href="/journal">Start your field journal.</Link>
          </p>
        )}
        {entries.map((e) => (
          <div key={e.id} className="card" style={{ marginBottom: "0.75rem" }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>{e.title}</strong>
              <div className="row" style={{ gap: "0.4rem" }}>
                <span className="badge">{e.kind}</span>
                {e.community_submission_id && (
                  <span className="badge pass">published</span>
                )}
              </div>
            </div>
            {e.place && <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>{e.place} · {e.behavior}</p>}
            {(e.evidence_assets ?? []).length > 0 && (
              <p className="muted" style={{ fontSize: "0.82rem", margin: "0.4rem 0 0" }}>
                {e.evidence_assets.length} evidence file{e.evidence_assets.length !== 1 ? "s" : ""} attached
              </p>
            )}
            <p className="muted" style={{ fontSize: "0.78rem", margin: "0.25rem 0 0" }}>
              {new Date(e.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </section>

      {/* ── Evidence assets ─────────────────────────────────────────── */}
      <section style={{ marginTop: "2rem" }}>
        <h2>Uploaded evidence</h2>
        {loadingAssets && <p className="muted">Loading…</p>}
        {errorAssets && (
          <p className="muted" style={{ fontSize: "0.88rem" }}>
            Evidence library not available (requires AWS storage): {errorAssets}
          </p>
        )}
        {!loadingAssets && assets.length === 0 && !errorAssets && (
          <p className="muted">
            No uploaded evidence yet. Use the{" "}
            <Link href="/ask">sighting check</Link> page to attach an image or audio file.
          </p>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "0.75rem" }}>
          {assets.map((a) => (
            <div key={a.id} className="card">
              <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <KindBadge kind={a.kind} />
                  <p style={{ margin: "0.4rem 0 0.1rem", fontWeight: 500, fontSize: "0.92rem", wordBreak: "break-all" }}>
                    {a.filename}
                  </p>
                  <p className="muted" style={{ fontSize: "0.78rem", margin: 0 }}>
                    {fmtBytes(a.size_bytes)} · {new Date(a.created_at).toLocaleDateString()}
                  </p>
                  {a.caption && (
                    <p className="muted" style={{ fontSize: "0.82rem", margin: "0.3rem 0 0" }}>
                      {a.caption}
                    </p>
                  )}
                  {a.linked_to.journal_entry_id && (
                    <p className="muted" style={{ fontSize: "0.78rem", margin: "0.2rem 0 0" }}>
                      Linked to journal entry
                    </p>
                  )}
                </div>
                <button
                  className="btn ghost"
                  style={{ fontSize: "0.78rem", padding: "0.2rem 0.5rem" }}
                  disabled={removingId === a.id}
                  onClick={() => removeAsset(a.id)}
                >
                  {removingId === a.id ? "…" : "Unlink"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Published submissions ────────────────────────────────────── */}
      <section style={{ marginTop: "2rem" }}>
        <h2>Published submissions</h2>
        {!loadingEntries && publishedEntries.length === 0 && (
          <p className="muted">
            No published submissions yet. Publish a journal entry to the community moderation queue.
          </p>
        )}
        {publishedEntries.map((e) => (
          <div key={e.community_submission_id} className="card" style={{ marginBottom: "0.75rem" }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>{e.title}</strong>
              <span className="badge pass">in review</span>
            </div>
            {e.place && <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>{e.place}</p>}
            <p className="muted" style={{ fontSize: "0.78rem", margin: "0.25rem 0 0" }}>
              Submission ID: {e.community_submission_id}
            </p>
          </div>
        ))}
      </section>
    </main>
  );
}

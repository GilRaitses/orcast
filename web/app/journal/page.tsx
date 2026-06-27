"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJSON, postJSON, type JournalEntry, type JournalEntriesResponse } from "@/lib/api";

function isUnauthorized(e: unknown): boolean {
  return /->\s*401/.test(String(e));
}

const BEHAVIORS = ["unknown", "feeding", "traveling", "socializing", "resting"] as const;

export default function JournalPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [title, setTitle] = useState("");
  const [place, setPlace] = useState("");
  const [body, setBody] = useState("");
  const [behavior, setBehavior] = useState<string>("unknown");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(true);
  const [loaded, setLoaded] = useState(false);

  async function load() {
    try {
      const res = await getJSON<JournalEntriesResponse>("api/journal/entries");
      setEntries(res.entries ?? []);
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

  async function createEntry(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy("create");
    setError(null);
    try {
      await postJSON("api/journal/entries", {
        title: title.trim(),
        place: place.trim() || null,
        body: body.trim() || null,
        behavior,
        kind: "observation",
      });
      setTitle("");
      setPlace("");
      setBody("");
      await load();
    } catch (err) {
      if (isUnauthorized(err)) setNeedsAuth(true);
      else setError(String(err));
    } finally {
      setBusy(null);
    }
  }

  async function publish(entryId: string) {
    setBusy(entryId);
    setError(null);
    try {
      await postJSON(`api/journal/entries/${entryId}/publish`, {});
      await load();
    } catch (err) {
      if (isUnauthorized(err)) setNeedsAuth(true);
      else setError(String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="container">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Field journal</h2>
        <p className="muted">
          Private notes and shore observations. Publish sends a copy to the community moderation queue;
          your journal stays yours until you share.
        </p>
        {needsAuth && (
          <p className="muted">
            Sign in to use your journal. <Link href="/login">Sign in</Link> or{" "}
            <Link href="/signup">create account</Link>.
          </p>
        )}
        {error && <p className="badge fail">{error}</p>}
      </div>

      {!needsAuth && loaded && (
        <div className="card">
          <h3>New entry</h3>
          <form onSubmit={createEntry} className="stack">
            <label>
              Title
              <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} />
            </label>
            <label>
              Place (optional)
              <input value={place} onChange={(e) => setPlace(e.target.value)} maxLength={200} />
            </label>
            <label>
              Behavior
              <select value={behavior} onChange={(e) => setBehavior(e.target.value)}>
                {BEHAVIORS.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Notes
              <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={4} maxLength={4000} />
            </label>
            <button type="submit" disabled={busy === "create"}>
              {busy === "create" ? "Saving…" : "Save to journal"}
            </button>
          </form>
        </div>
      )}

      {!loaded && !needsAuth && (
        <div className="card">
          <div className="skeleton" style={{ height: 18, width: "40%" }} />
        </div>
      )}

      {loaded && !needsAuth && entries.length === 0 && (
        <div className="card muted">No entries yet.</div>
      )}

      {entries.map((entry) => (
        <div className="card" key={entry.id}>
          <h3 style={{ marginTop: 0 }}>{entry.title}</h3>
          {entry.place && <p className="muted">{entry.place}</p>}
          {entry.body && <p>{entry.body}</p>}
          <p className="muted">
            {entry.behavior} · {new Date(entry.created_at).toLocaleString()}
          </p>
          {entry.community_submission_id ? (
            <p className="badge ok">
              Published{" "}
              <Link href="/moderation">moderation queue</Link> ({entry.community_submission_id.slice(0, 8)}…)
            </p>
          ) : (
            <button type="button" disabled={busy === entry.id} onClick={() => publish(entry.id)}>
              {busy === entry.id ? "Publishing…" : "Publish to community"}
            </button>
          )}
        </div>
      ))}
    </main>
  );
}

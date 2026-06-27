"use client";

import { useState } from "react";
import { postJSON } from "@/lib/api";

const OPTIONS: { id: string; label: string }[] = [
  { id: "early_access", label: "Early access to try it now" },
  { id: "whitepapers", label: "Read the whitepapers" },
  { id: "demo", label: "Watch a demo" },
];

interface WhitepaperLink {
  title: string;
  url: string;
}
interface InterestLinks {
  early_access?: string;
  whitepapers?: WhitepaperLink[];
  demo?: string;
}
interface InterestResponse {
  status: string;
  message: string;
  links: InterestLinks;
  email_delivered: boolean;
}

export default function InterestForm() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [interests, setInterests] = useState<string[]>(["early_access"]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InterestResponse | null>(null);

  function toggle(id: string) {
    setInterests((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function submit() {
    if (!email.trim() || !email.includes("@")) {
      setError("Enter a valid email.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const resp = await postJSON<InterestResponse>("api/interest", {
        email: email.trim(),
        name: name.trim(),
        interests,
      });
      setResult(resp);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    const l = result.links;
    return (
      <div className="card interest-card" data-demo="interest-result">
        <p>{result.message}</p>
        <div className="interest-links row" style={{ flexWrap: "wrap", gap: "0.4rem", marginTop: "0.5rem" }}>
          {l.early_access && (
            <a className="chip" href={l.early_access}>
              Open the live app
            </a>
          )}
          {l.whitepapers?.map((w) => (
            <a key={w.url} className="chip" href={w.url} target="_blank" rel="noreferrer">
              {w.title}
            </a>
          ))}
          {l.demo && (
            <a className="chip" href={l.demo} target="_blank" rel="noreferrer">
              Watch the demo
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="card interest-card" data-demo="interest-form">
      <strong>Get access</strong>
      <p className="muted" style={{ marginTop: "0.2rem" }}>
        It is all live. Pick what you want and it arrives right away.
      </p>
      <div className="interest-options" style={{ display: "flex", flexDirection: "column", gap: "0.3rem", margin: "0.5rem 0" }}>
        {OPTIONS.map((o) => (
          <label key={o.id} className="row" style={{ gap: "0.45rem", alignItems: "center" }}>
            <input type="checkbox" checked={interests.includes(o.id)} onChange={() => toggle(o.id)} />
            {o.label}
          </label>
        ))}
      </div>
      <input
        type="text"
        placeholder="Name (optional)"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{ marginBottom: "0.4rem" }}
      />
      <input
        type="email"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <div className="row" style={{ marginTop: "0.6rem" }}>
        <button type="button" onClick={submit} disabled={busy || !email.trim()}>
          {busy ? "Sending…" : "Send it to me"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

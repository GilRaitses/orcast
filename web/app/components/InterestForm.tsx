"use client";

import { useState } from "react";
import { postJSON } from "@/lib/api";

const AUDIENCES: { id: string; label: string; blurb: string }[] = [
  { id: "research_partner", label: "Research partner", blurb: "Use it, and stand it up on your data or region." },
  { id: "visitor", label: "Planning a visit", blurb: "Early access to orcast Trips for the San Juan Islands." },
  { id: "curious", label: "Just exploring", blurb: "See the live forecast and the whitepapers." },
];

interface WhitepaperLink { title: string; url: string }
interface InterestLinks { app?: string; whitepapers?: WhitepaperLink[]; demo?: string }
interface InterestResponse { status: string; message: string; links: InterestLinks; email_delivered: boolean }

export default function InterestForm() {
  const [audience, setAudience] = useState("research_partner");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InterestResponse | null>(null);

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
        audience,
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
          {l.app && (
            <a className="chip" href={l.app}>
              Open the live forecast
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

  const cta =
    audience === "research_partner"
      ? "Try it on my data"
      : audience === "visitor"
      ? "Get early access"
      : "Send it to me";

  return (
    <div className="card interest-card" data-demo="interest-form">
      <strong>Get access</strong>
      <p className="muted" style={{ marginTop: "0.2rem" }}>It is all live. Tell me what brings you and it arrives right away.</p>
      <div className="interest-options" style={{ display: "flex", flexDirection: "column", gap: "0.4rem", margin: "0.5rem 0" }}>
        {AUDIENCES.map((a) => (
          <label key={a.id} className="row" style={{ gap: "0.45rem", alignItems: "flex-start" }}>
            <input
              type="radio"
              name="audience"
              checked={audience === a.id}
              onChange={() => setAudience(a.id)}
              style={{ marginTop: "0.25rem" }}
            />
            <span>
              <strong>{a.label}.</strong> <span className="muted">{a.blurb}</span>
            </span>
          </label>
        ))}
      </div>
      <input type="text" placeholder="Name (optional)" value={name} onChange={(e) => setName(e.target.value)} style={{ marginBottom: "0.4rem" }} />
      <input type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      <div className="row" style={{ marginTop: "0.6rem" }}>
        <button type="button" onClick={submit} disabled={busy || !email.trim()}>
          {busy ? "Sending…" : cta}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

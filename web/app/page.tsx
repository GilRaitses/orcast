"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getJSON, postJSON, GatesResponse } from "@/lib/api";
import { normalizeIntegrityConditions } from "@/lib/integrityConditions";
import { parseProvenanceFlag, parseViewport } from "@/lib/viewport";
import { ConfidenceMeter, ConfidenceMeterSkeleton } from "./components/ConfidenceBadge";
import MapHero, { EventPoint } from "./components/MapHero";

const PANELS = [
  {
    title: "Gate-bounded forecast map",
    href: "/",
    description:
      "Every map cell carries only the confidence its evidence has earned. Gates suppress display when statistical tests fail — click any cell to trace the value back to its detections and kernel fits.",
    label: "Open map",
  },
  {
    title: "Integrity conditions dashboard",
    href: "/gates",
    description:
      "The full gate battery: phase-shuffled null test, time-rescaling GoF, held-out deviance skill, PIT calibration. Failing gates surface a named condition — not a blank — alongside the forecast.",
    label: "View gates",
  },
  {
    title: "Sighting check + evidence upload",
    href: "/ask",
    description:
      "Describe what you saw or upload a photo or audio clip. The system returns an encounter likelihood grounded in live gate state, not a yes/no from parametric LLM knowledge.",
    label: "Sighting check",
  },
  {
    title: "Exploration guide + surface planner",
    href: "/explore?planner=1",
    description:
      "A managed AI agent routes through gates, provenance, and evidence panels in sequence. Plan-then-execute: every skill dispatch is logged; the step-log is the audit substrate.",
    label: "Open guide",
  },
];

function InterestForm() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setStatus("sending");
    try {
      await postJSON("/api/be/api/interest", { email, name, source: "orcast" });
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  if (status === "done") {
    return (
      <p style={{ color: "var(--color-success, #2e7d32)", marginTop: "0.5rem" }}>
        Got it — you&apos;ll hear from us when the papers are ready.
      </p>
    );
  }

  return (
    <form onSubmit={submit} style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap", marginTop: "0.75rem" }}>
      <input
        type="text"
        placeholder="Your name (optional)"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{
          flex: "1 1 140px", padding: "0.55rem 0.9rem",
          border: "1px solid var(--color-border, #dde)", borderRadius: "6px",
          fontSize: "0.9rem", background: "var(--color-bg-card, #fff)",
        }}
      />
      <input
        type="email"
        placeholder="your@email.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        style={{
          flex: "2 1 200px", padding: "0.55rem 0.9rem",
          border: "1px solid var(--color-border, #dde)", borderRadius: "6px",
          fontSize: "0.9rem", background: "var(--color-bg-card, #fff)",
        }}
      />
      <button
        type="submit"
        disabled={status === "sending"}
        className="btn"
        style={{ flexShrink: 0 }}
      >
        {status === "sending" ? "Sending…" : "Keep me posted"}
      </button>
      {status === "error" && (
        <p style={{ width: "100%", color: "var(--color-error, #c62828)", fontSize: "0.85rem" }}>
          Something went wrong — try again or email directly.
        </p>
      )}
    </form>
  );
}

function HomePageInner() {
  const searchParams = useSearchParams();
  const initialViewport = parseViewport(searchParams);
  const openProvenance = parseProvenanceFlag(searchParams);
  const [gates, setGates] = useState<GatesResponse | null>(null);
  const [gatesLoaded, setGatesLoaded] = useState(false);
  const [events, setEvents] = useState<EventPoint[]>([]);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    try {
      const g = await getJSON<GatesResponse>("/api/gates");
      setGates(g);
    } catch {
      /* gates may be unfitted */
    } finally {
      setGatesLoaded(true);
    }
    try {
      const ev = await getJSON<{ events: Array<{ id: string; location: { lat: number; lng: number }; source: string }> }>(
        "/api/realtime/events"
      );
      setEvents(
        (ev.events ?? [])
          .filter((e) => e.location)
          .map((e) => ({ id: e.id, lat: e.location.lat, lng: e.location.lng, source: e.source }))
      );
    } catch {
      /* events optional */
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function refit() {
    setRunning(true);
    setMsg(null);
    try {
      const res = await postJSON("/api/orchestrator/run", {});
      setMsg(`Orchestrator started: ${res.execution_arn ?? "ok"}`);
    } catch (e) {
      setMsg(`Re-fit unavailable (${e}). Scheduled jobs refresh source data; model fitting runs through the orchestrator when triggered.`);
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="container">
      <h1 className="hero-title">orcast</h1>
      <p className="hero-subtitle">
        Gate-bounded encounter forecasting for Southern Resident killer whales. Every confidence
        value is earned by the evidence — and traceable back to it.
      </p>

      <div className="card">
        {gatesLoaded ? (
          <ConfidenceMeter
            confidence={gates?.effective_confidence ?? gates?.confidence ?? 0}
            promoted={gates?.promoted}
            caveats={normalizeIntegrityConditions(
              gates?.caveats,
              gates?.level0_detector_qc as { status?: string } | undefined
            )}
          />
        ) : (
          <ConfidenceMeterSkeleton />
        )}
        <div className="row" style={{ marginTop: "1rem" }}>
          <button className="btn" onClick={refit} disabled={running}>
            {running ? "Starting..." : "Run re-fit"}
          </button>
          <a className="btn ghost" href="/gates">View fitness gates</a>
          <a className="btn ghost" href="/ask">Sighting check</a>
          <a className="btn ghost" href="/explore">Exploration guide</a>
        </div>
        {msg && <p className="muted" style={{ marginTop: "0.75rem" }}>{msg}</p>}
      </div>

      <Suspense fallback={<p className="muted">Loading map…</p>}>
        <MapHero
          events={events}
          initialViewport={initialViewport}
          openProvenanceOnLoad={openProvenance}
        />
      </Suspense>

      {/* ── Panel gallery ─────────────────────────────────────────────────── */}
      <section style={{ marginTop: "3rem" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 500, marginBottom: "0.35rem" }}>
          Interactive panels
        </h2>
        <p className="muted" style={{ marginBottom: "1.5rem" }}>
          Each panel is a live view into a different layer of the evidence chain.
        </p>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1rem",
        }}>
          {PANELS.map((p) => (
            <a
              key={p.title}
              href={p.href}
              style={{
                display: "block",
                textDecoration: "none",
                borderRadius: "10px",
                border: "1px solid var(--color-border, #dde)",
                padding: "1.2rem 1.3rem",
                background: "var(--color-bg-card, #fafafa)",
                transition: "box-shadow 0.15s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 4px 18px rgba(0,0,0,0.08)")}
              onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
            >
              {/* Placeholder slot: swap this div for an <img> or <video> once GIFs are captured */}
              <div style={{
                width: "100%", aspectRatio: "16/9", borderRadius: "6px",
                background: "var(--color-bg, #f0f2f6)",
                marginBottom: "0.9rem",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "0.78rem", color: "var(--color-muted, #888)",
              }}>
                demo coming
              </div>
              <h3 style={{ fontSize: "0.97rem", fontWeight: 600, marginBottom: "0.4rem" }}>
                {p.title}
              </h3>
              <p style={{ fontSize: "0.85rem", color: "var(--color-muted, #555)", marginBottom: "0.8rem", lineHeight: 1.5 }}>
                {p.description}
              </p>
              <span style={{
                fontSize: "0.82rem", fontWeight: 600,
                color: "var(--color-accent, #4361ee)",
              }}>
                {p.label} →
              </span>
            </a>
          ))}
        </div>
      </section>

      {/* ── Research + whitepaper ─────────────────────────────────────────── */}
      <section style={{ marginTop: "2.75rem" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 500, marginBottom: "0.35rem" }}>
          Research
        </h2>
        <p className="muted" style={{ marginBottom: "1rem" }}>
          Two papers document the architecture and the grounding quality benchmark.
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div className="card" style={{ padding: "1rem 1.2rem" }}>
            <p style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.2rem" }}>
              Evidence-bounded encounter forecasting
            </p>
            <p className="muted" style={{ fontSize: "0.83rem", marginBottom: "0.4rem" }}>
              Honest-model architecture for effort-biased wildlife observation data · Gil Raitses, aimez.ai · 2026
            </p>
            <a href="https://github.com/gilraitses/orcast" style={{ fontSize: "0.82rem" }}>
              arXiv bundle (forthcoming) →
            </a>
          </div>
          <div className="card" style={{ padding: "1rem 1.2rem" }}>
            <p style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.2rem" }}>
              Grounding quality measurement for orchestrated AI reasoning chains
            </p>
            <p className="muted" style={{ fontSize: "0.83rem", marginBottom: "0.4rem" }}>
              Evidence-binding rate as an evaluation primitive for world model systems · Gil Raitses, aimez.ai · 2026
            </p>
            <a href="https://github.com/gilraitses/orcast" style={{ fontSize: "0.82rem" }}>
              arXiv bundle (forthcoming) →
            </a>
          </div>
        </div>
      </section>

      {/* ── Email capture ─────────────────────────────────────────────────── */}
      <section style={{ marginTop: "2.75rem", marginBottom: "3rem" }}>
        <div className="card" style={{ padding: "1.5rem 1.6rem" }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.3rem" }}>
            Stay in the loop
          </h2>
          <p className="muted" style={{ fontSize: "0.88rem", marginBottom: "0.1rem" }}>
            Leave your email and you&apos;ll get the whitepapers and updates as the project develops.
            No newsletter — just the papers.
          </p>
          <InterestForm />
        </div>
      </section>
    </main>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<main className="container"><p className="muted">Loading…</p></main>}>
      <HomePageInner />
    </Suspense>
  );
}

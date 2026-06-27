"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps";
import { postJSON, getJSON, SightingAssistResponse, SightingAssistStatus } from "@/lib/api";

const SAN_JUAN_CENTER = { lat: 48.55, lng: -123.05 };
const EXAMPLE_PROMPTS = [
  "I saw a black dorsal fin from shore. Could it have been an orca?",
  "Heard a ping on the hydrophone network. How often are those false alarms?",
  "Kayaking in Haro Strait at sunset. Are encounters likely today?",
];

interface UploadedAsset {
  id: string;
  kind: "image" | "audio" | "other";
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_uri: string;
}

function fmtBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

function renderReply(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && !part.startsWith("**")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <span key={i}>{part}</span>;
  });
}

export default function SightingCheckPanel() {
  const key = process.env.NEXT_PUBLIC_MAPS_KEY;
  const [pick, setPick] = useState<{ lat: number; lng: number } | null>({
    lat: 48.5465,
    lng: -123.03,
  });
  const [message, setMessage] = useState("");
  const [when, setWhen] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState<SightingAssistResponse | null>(null);
  const [llm, setLlm] = useState<SightingAssistStatus | null>(null);

  // Cycling ghost prompt: examples fade through the empty composer; Enter sends
  // whichever is showing. Stops cycling once the user types.
  const [promptIdx, setPromptIdx] = useState(0);
  const [ghostVisible, setGhostVisible] = useState(true);
  const [showWhen, setShowWhen] = useState(false);
  const [focused, setFocused] = useState(false);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (message || focused) return;
    const t = setInterval(() => {
      setGhostVisible(false);
      setTimeout(() => {
        setPromptIdx((i) => (i + 1) % EXAMPLE_PROMPTS.length);
        setGhostVisible(true);
      }, 380);
    }, 3800);
    return () => clearInterval(t);
  }, [message, focused]);

  // Evidence upload state
  const [assets, setAssets] = useState<UploadedAsset[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getJSON<SightingAssistStatus>("/api/sighting-assist/status")
      .then(setLlm)
      .catch(() => setLlm(null));
  }, []);

  async function uploadFile(file: File, kind: "image" | "audio" | "other") {
    setUploading(true);
    setUploadError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("kind", kind);
      const res = await fetch("/api/be/api/evidence/assets", {
        method: "POST",
        body: form,
        // Do NOT set Content-Type — let the browser set it with the boundary.
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail || `Upload failed (${res.status})`);
      }
      const data = await res.json();
      const asset: UploadedAsset = data.asset;
      setAssets((prev) => [...prev, asset]);
    } catch (e) {
      setUploadError(String(e));
    } finally {
      setUploading(false);
    }
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>, kind: "image" | "audio" | "other") {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ""; // reset so same file can be re-selected
    uploadFile(file, kind);
  }

  function removeAsset(id: string) {
    setAssets((prev) => prev.filter((a) => a.id !== id));
  }

  async function ask(textOverride?: string) {
    const msg = (textOverride ?? message).trim() || EXAMPLE_PROMPTS[promptIdx];
    if (!pick || !msg) return;
    if (!message) setMessage(msg);
    setBusy(true);
    setError(null);
    try {
      const res = await postJSON<SightingAssistResponse>("/api/sighting-assist", {
        lat: pick.lat,
        lng: pick.lng,
        message: msg,
        when: when || undefined,
        evidence_assets: assets.map((a) => ({
          id: a.id,
          kind: a.kind,
          filename: a.filename,
          content_type: a.content_type,
          size_bytes: a.size_bytes,
          storage_uri: a.storage_uri,
        })),
      });
      setReply(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Tab on an empty box accepts the showing suggestion (un-mutes it), so you
    // can edit or press Enter to run it.
    if (e.key === "Tab" && !e.shiftKey && !message) {
      e.preventDefault();
      setMessage(EXAMPLE_PROMPTS[promptIdx]);
      return;
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (busy || !pick) return;
      ask(message.trim() || EXAMPLE_PROMPTS[promptIdx]);
    }
  }

  return (
    <div className="ask-layout">
      <div className="card ask-map-card">
        {key ? (
          <APIProvider apiKey={key}>
            <Map
              mapId="orcast-forecast"
              defaultCenter={SAN_JUAN_CENTER}
              defaultZoom={10}
              gestureHandling="greedy"
              onClick={(e) => {
                const ll = e.detail.latLng;
                if (ll) setPick({ lat: ll.lat, lng: ll.lng });
              }}
              style={{ width: "100%", height: 320 }}
            >
              {pick && (
                <AdvancedMarker
                  position={pick}
                  title="Your observation point"
                />
              )}
            </Map>
          </APIProvider>
        ) : (
          <div className="ask-map-fallback">
            <p className="muted">Set NEXT_PUBLIC_MAPS_KEY for the map. Enter coordinates manually:</p>
            <div className="row">
              <label>
                Lat{" "}
                <input
                  type="number"
                  step="0.0001"
                  value={pick?.lat ?? 48.55}
                  onChange={(e) =>
                    setPick({ lat: Number(e.target.value), lng: pick?.lng ?? -123.05 })
                  }
                />
              </label>
              <label>
                Lng{" "}
                <input
                  type="number"
                  step="0.0001"
                  value={pick?.lng ?? -123.05}
                  onChange={(e) =>
                    setPick({ lat: pick?.lat ?? 48.55, lng: Number(e.target.value) })
                  }
                />
              </label>
            </div>
          </div>
        )}
        <p className="muted" style={{ fontSize: "0.85rem", margin: "0.75rem 0 0" }}>
          {pick
            ? `Pin ${pick.lat.toFixed(4)}, ${pick.lng.toFixed(4)}. Click the map to move it.`
            : "Click the map where you were observing."}
        </p>
      </div>

      <div className="card ask-chat-card">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h2 style={{ marginTop: 0 }}>Was that an orca?</h2>
            <p className="muted" style={{ marginBottom: 0, fontSize: "0.92rem" }}>
              Evidence-backed interpretation, not a yes/no oracle. Answers cite gates, provenance, and Level 0 QC.
            </p>
          </div>
          {llm && (
            <span
              className={`badge ${
                llm.narration_backend === "bedrock"
                  ? "pass"
                  : llm.narration_backend === "template"
                    ? "warn"
                    : "pass"
              }`}
              title={llm.setup_hint}
            >
              {llm.narration_backend === "bedrock"
                ? `Bedrock · ${(llm.bedrock_model ?? "haiku").split(".").pop()?.split("-")[2] ?? "haiku"}`
                : llm.narration_backend === "ollama"
                  ? `local ${llm.llm_model}`
                  : "template fallback"}
            </span>
          )}
        </div>

        <div className="chat-composer">
          <textarea
            ref={taRef}
            className="chat-input"
            rows={3}
            maxLength={2000}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            aria-label="Describe your sighting"
          />
          {!message && (
            <div className={`chat-ghost ${ghostVisible ? "visible" : ""}`} aria-hidden="true">
              {EXAMPLE_PROMPTS[promptIdx]}
            </div>
          )}
          <button
            type="button"
            className="chat-send"
            data-demo="sighting-check"
            aria-label="Check sighting"
            disabled={busy || !pick}
            onClick={() => ask()}
          >
            {busy ? "…" : "↑"}
          </button>
        </div>
        <p className="chat-hint">
          <kbd>Tab</kbd> to use the suggestion · <kbd>Enter</kbd> to ask · <kbd>Shift</kbd>+<kbd>Enter</kbd> for a new line
        </p>

        {/* ── Media upload section ─────────────────────────────────── */}
        <div style={{ marginBottom: "0.9rem" }}>
          <p className="ask-label" style={{ marginBottom: "0.5rem" }}>
            Evidence (optional)
          </p>
          <div className="row" style={{ gap: "0.6rem", flexWrap: "wrap" }}>
            {/* Image / camera */}
            <input
              ref={imageInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              style={{ display: "none" }}
              onChange={(e) => handleFileInput(e, "image")}
            />
            <button
              type="button"
              className="btn ghost"
              style={{ fontSize: "0.88rem" }}
              disabled={uploading}
              onClick={() => imageInputRef.current?.click()}
            >
              {uploading ? "Uploading…" : "📷 Upload image / take photo"}
            </button>

            {/* Audio / microphone */}
            <input
              ref={audioInputRef}
              type="file"
              accept="audio/*"
              capture="user"
              style={{ display: "none" }}
              onChange={(e) => handleFileInput(e, "audio")}
            />
            <button
              type="button"
              className="btn ghost"
              style={{ fontSize: "0.88rem" }}
              disabled={uploading}
              onClick={() => audioInputRef.current?.click()}
            >
              {uploading ? "Uploading…" : "🎙 Upload sound / record audio"}
            </button>
          </div>

          {uploadError && (
            <p className="badge fail" style={{ display: "inline-block", marginTop: "0.5rem" }}>
              {uploadError}
            </p>
          )}

          {/* Asset chips */}
          {assets.length > 0 && (
            <div className="row" style={{ flexWrap: "wrap", gap: "0.4rem", marginTop: "0.6rem" }}>
              {assets.map((a) => (
                <div
                  key={a.id}
                  className="chip"
                  style={{ display: "flex", alignItems: "center", gap: "0.3rem", padding: "0.25rem 0.55rem" }}
                >
                  <span style={{ fontSize: "0.82rem" }}>
                    {a.kind === "image" ? "🖼" : a.kind === "audio" ? "🔊" : "📄"}{" "}
                    {a.filename} ({fmtBytes(a.size_bytes)})
                  </span>
                  <button
                    type="button"
                    onClick={() => removeAsset(a.id)}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "inherit",
                      padding: "0 0 0 0.2rem",
                      fontSize: "0.82rem",
                      lineHeight: 1,
                    }}
                    aria-label={`Remove ${a.filename}`}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="chat-footer">
          {showWhen ? (
            <label className="ask-label chat-when">
              When (optional)
              <input
                type="datetime-local"
                className="ask-input"
                value={when}
                onChange={(e) => setWhen(e.target.value)}
              />
            </label>
          ) : (
            <button type="button" className="chat-link" onClick={() => setShowWhen(true)}>
              + add time
            </button>
          )}
          <Link className="chat-link" href="/moderation">
            Submit a shore report →
          </Link>
        </div>

        {error && <p className="badge fail" style={{ display: "inline-block" }}>{error}</p>}

        {reply && (
          <div className="ask-reply">
            <p className="ask-reply-meta">
              Narration: <strong>{reply.source}</strong>
              {reply.model ? ` · ${reply.model}` : ""}
              {reply.llm_error ? ` · LLM unavailable (${reply.llm_error})` : ""}
            </p>
            <div className="ask-reply-body">{renderReply(reply.reply)}</div>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              Glossary:{" "}
              {(reply.glossary_links ?? []).map((href, i) => (
                <span key={href}>
                  {i > 0 ? " · " : ""}
                  <Link href={href}>{href.replace("/glossary#", "")}</Link>
                </span>
              ))}
            </p>
          </div>
        )}

        {llm && llm.narration_backend === "template" && !llm.bedrock_enabled && (
          <details className="explainer" style={{ marginTop: "1rem" }}>
            <summary>Enable Bedrock narration on AWS</summary>
            <p className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.5rem" }}>
              Production uses Amazon Bedrock Claude Haiku via IAM, no public LLM URL, pay-per-request.
              Set <code>ORCAST_ENABLE_BEDROCK=true</code> on App Runner and redeploy.
            </p>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              Until then, the template fallback still cites live gates and provenance.
            </p>
          </details>
        )}
      </div>
    </div>
  );
}

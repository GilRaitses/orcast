"use client";

import { Suspense } from "react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps";
import ProvenanceModal from "@/app/components/ProvenanceModal";
import ActiveSurfaceHost from "@/app/components/ActiveSurfaceHost";
import {
  parseViewport,
  provenanceHref,
  viewportQuery,
  type MapViewport,
} from "@/lib/viewport";
import {
  postJSON,
  getJSON,
  ExploreStatus,
  InteractionAnnotation,
  InteractionResponse,
  InteractionStep,
  ExploreSessionResponse,
} from "@/lib/api";
import { mapViewportFromIntent, type PlanResponse, type UiIntent } from "@/lib/uiIntent";

const SAN_JUAN_CENTER = { lat: 48.55, lng: -123.05 };
const CAST_AGENT_ID = "explore-guide-v1";
const PLANNER_AGENT_ID = "surface-planner-v1";
const STARTER_PROMPTS = [
  "Which gates block promotion right now?",
  "Explain effective confidence vs raw confidence.",
  "What does provenance show for this map pin?",
];

interface GatewayConfig {
  ai_gateway_enabled: boolean;
  models: string[];
  default_model: string;
  default_agent_id?: string;
  narration_path: string;
}

interface AssistantTurn {
  role: "assistant";
  content: string;
  deep_links?: InteractionResponse["deep_links"];
  managed_agent_id?: string;
  hydration_mode?: string;
  skills_invoked?: string[];
  steps?: InteractionStep[];
  annotations?: InteractionAnnotation[];
}

interface UserTurn {
  role: "user";
  content: string;
}

type TurnEntry = UserTurn | AssistantTurn;

function renderReply(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && !part.startsWith("**")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const [, label, href] = linkMatch;
      return (
        <Link key={i} href={href}>
          {label}
        </Link>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function parseMapLink(href: string): MapViewport | null {
  try {
    const url = new URL(href, "https://orcast-h0.vercel.app");
    return parseViewport(url.searchParams);
  } catch {
    return null;
  }
}

function annotationLabel(a: InteractionAnnotation): string {
  const prefix =
    a.type === "gate_citation"
      ? "Gate"
      : a.type === "provenance_citation"
        ? "Provenance"
        : a.type === "evidence_citation"
          ? "Evidence"
          : a.type.replace(/_/g, " ");
  return a.label || prefix;
}

function ExploreGuidePanelInner() {
  const key = process.env.NEXT_PUBLIC_MAPS_KEY;
  const router = useRouter();
  const searchParams = useSearchParams();
  const plannerMode = searchParams.get("planner") === "1";
  const initial = parseViewport(searchParams);
  const [pick, setPick] = useState<MapViewport | null>(
    initial ?? { lat: 48.5465, lng: -123.03 }
  );
  const [message, setMessage] = useState(STARTER_PROMPTS[0]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<TurnEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<ExploreStatus | null>(null);
  const [gateway, setGateway] = useState<GatewayConfig | null>(null);
  const [model, setModel] = useState("");
  const [provenancePick, setProvenancePick] = useState<MapViewport | null>(null);
  const [activeIntent, setActiveIntent] = useState<UiIntent | null>(null);
  const [activePrepare, setActivePrepare] = useState<PlanResponse["prepare"] | null>(null);

  useEffect(() => {
    getJSON<ExploreStatus>("/api/explore/status")
      .then(setStatus)
      .catch(() => setStatus(null));
    fetch("/api/interactions", { cache: "no-store" })
      .then((r) => r.json())
      .then((cfg: GatewayConfig) => {
        setGateway(cfg);
        setModel(cfg.default_model);
      })
      .catch(() =>
        fetch("/api/explore", { cache: "no-store" })
          .then((r) => r.json())
          .then((cfg: GatewayConfig) => {
            setGateway(cfg);
            setModel(cfg.default_model);
          })
          .catch(() => setGateway(null))
      );
  }, []);

  useEffect(() => {
    const vp = parseViewport(searchParams);
    if (vp) setPick(vp);
  }, [searchParams]);

  function syncViewport(vp: MapViewport) {
    setPick(vp);
    router.replace(`/explore?${viewportQuery(vp)}`, { scroll: false });
  }

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await postJSON<ExploreSessionResponse>("/api/explore/sessions", {
      title: "H0 exploration",
    });
    setSessionId(res.session_id);
    return res.session_id;
  }

  async function sendTurn() {
    if (!message.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      const payload = {
        session_id: sid,
        message: message.trim(),
        agent_id: plannerMode ? PLANNER_AGENT_ID : CAST_AGENT_ID,
        viewport: pick ? { lat: pick.lat, lng: pick.lng, zoom: pick.zoom ?? 10 } : undefined,
        focus: pick ? { cell: `${pick.lat},${pick.lng}` } : undefined,
      };

      if (plannerMode) {
        const planResp = await fetch("/api/interactions/plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!planResp.ok) {
          if (planResp.status === 401) throw new Error("Reviewer sign-in required for surface planner");
          throw new Error(`Surface planner -> ${planResp.status}`);
        }
        const plan: PlanResponse = await planResp.json();
        setActiveIntent(plan.ui_intent);
        setActivePrepare(plan.prepare);
        const vp = mapViewportFromIntent(plan.ui_intent);
        if (vp) syncViewport(vp);
        setTurns((prev) => [
          ...prev,
          { role: "user", content: message.trim() },
          {
            role: "assistant",
            content: `Surface plan: ${plan.ui_intent.panels.map((p) => p.id).join(", ")}`,
            managed_agent_id: plan.ui_intent.planner_agent_id,
            hydration_mode: plan.hydration_mode,
            skills_invoked: plan.ui_intent.skill_plan,
            steps: plan.prepare.steps,
            annotations: plan.prepare.annotations,
            deep_links: plan.ui_intent.deep_links,
          },
        ]);
        return;
      }

      let res: InteractionResponse;
      if (gateway?.ai_gateway_enabled) {
        const gw = await fetch("/api/interactions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...payload, model }),
        });
        if (!gw.ok) throw new Error(`AI Gateway interactions -> ${gw.status}`);
        res = await gw.json();
      } else {
        res = await postJSON<InteractionResponse>("/api/interactions", payload);
      }

      setTurns((prev) => [
        ...prev,
        { role: "user", content: message.trim() },
        {
          role: "assistant",
          content: res.reply,
          deep_links: res.deep_links,
          managed_agent_id: res.managed_agent_id ?? CAST_AGENT_ID,
          hydration_mode: res.hydration_mode,
          skills_invoked: res.skills_invoked,
          steps: res.steps,
          annotations: res.annotations,
        },
      ]);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  function openDeepLink(href: string) {
    const vp = parseMapLink(href);
    if (vp) {
      setProvenancePick(vp);
      return;
    }
    if (href.startsWith("/")) {
      router.push(href);
    }
  }

  const auroraReady = status?.aurora_enabled && status?.aurora_connected;
  const narrationLabel = gateway?.ai_gateway_enabled
    ? `Vercel AI Gateway (${model}) · Cast ${CAST_AGENT_ID}`
    : `${status?.narration_backend ?? "template"}${status?.bedrock_enabled ? " (Bedrock)" : ""} · Cast ${CAST_AGENT_ID}`;

  return (
    <div className="ask-layout">
      <div className="card ask-map-card">
        {key ? (
          <APIProvider apiKey={key}>
            <Map
              mapId="orcast-forecast"
              defaultCenter={pick ?? SAN_JUAN_CENTER}
              defaultZoom={pick?.zoom ?? 10}
              gestureHandling="greedy"
              onClick={(e) => {
                const ll = e.detail.latLng;
                if (ll) syncViewport({ lat: ll.lat, lng: ll.lng, zoom: 10 });
              }}
              style={{ width: "100%", height: 280 }}
            >
              {pick && <AdvancedMarker position={pick} title="Exploration map context" />}
            </Map>
          </APIProvider>
        ) : (
          <p className="muted">Set NEXT_PUBLIC_MAPS_KEY for map context, or ask gate questions without a pin.</p>
        )}
        <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.75rem" }}>
          Pin optional — adds cell provenance to the guide context. Same gates as the forecast.{" "}
          {pick && (
            <Link href={provenanceHref(pick)} className="chip">
              Trace provenance on map →
            </Link>
          )}
        </p>
      </div>

      <div className="card">
        <p className="cast-badge" style={{ marginBottom: "0.75rem" }}>
          Cast: {plannerMode ? "surface-planner-v1 (keyed)" : CAST_AGENT_ID}
        </p>
        {plannerMode && (
          <p className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.75rem" }}>
            Surface planner mode — requires reviewer sign-in. Renders active panels from{" "}
            <code>ui_intent</code>.
          </p>
        )}
        {gateway?.ai_gateway_enabled && gateway.models.length > 0 && (
          <label style={{ display: "block", marginBottom: "0.75rem" }}>
            Model (AI Gateway)
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {gateway.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
        )}
        <div className="row" style={{ flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
          {STARTER_PROMPTS.map((p) => (
            <button key={p} type="button" className="chip" onClick={() => setMessage(p)}>
              {p.slice(0, 42)}…
            </button>
          ))}
        </div>
        <label>
          Question
          <textarea
            rows={3}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Navigate gates and provenance…"
          />
        </label>
        <div className="row" style={{ marginTop: "0.75rem" }}>
          <button type="button" data-demo="explore-send" onClick={sendTurn} disabled={busy || !message.trim()}>
            {busy ? "Thinking…" : "Continue exploration"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {activeIntent && activePrepare && (
          <ActiveSurfaceHost
            uiIntent={activeIntent}
            prepare={activePrepare}
            onDeepLink={openDeepLink}
          />
        )}
        {status && !auroraReady && (
          <p className="muted" style={{ marginTop: "0.75rem" }}>
            Session store: {status.exploration_backend ?? "disabled"}. Guide replies may be unavailable until Postgres
            is connected.
          </p>
        )}
        {status && (
          <p className="muted" style={{ fontSize: "0.8rem", marginTop: "0.5rem" }}>
            Narration: {narrationLabel}
          </p>
        )}
      </div>

      {turns.length > 0 && (
        <div className="card ask-replies">
          <h2 style={{ fontSize: "1.1rem" }}>Turn history</h2>
          {turns.map((t, i) =>
            t.role === "user" ? (
              <div key={i} className="ask-user">
                <strong>You</strong>
                <div>{t.content}</div>
              </div>
            ) : (
              <div key={i} className="ask-assistant">
                <span className="cast-badge">
                  Cast: {t.managed_agent_id ?? CAST_AGENT_ID}
                  {t.hydration_mode ? ` · ${t.hydration_mode}` : ""}
                </span>
                <strong style={{ display: "block" }}>Guide</strong>
                <div>{renderReply(t.content)}</div>
                {t.annotations && t.annotations.length > 0 && (
                  <div className="cast-annotations">
                    {t.annotations.map((a, j) =>
                      a.href ? (
                        <button
                          key={`${a.type}-${j}`}
                          type="button"
                          className="cast-annotation chip"
                          onClick={() => openDeepLink(a.href!)}
                        >
                          {annotationLabel(a)}
                        </button>
                      ) : (
                        <span key={`${a.type}-${j}`} className="cast-annotation">
                          {annotationLabel(a)}
                        </span>
                      )
                    )}
                  </div>
                )}
                {t.deep_links && t.deep_links.length > 0 && (
                  <div className="row" style={{ flexWrap: "wrap", gap: "0.35rem", marginTop: "0.5rem" }}>
                    {t.deep_links.map((d) => (
                      <button
                        key={d.href}
                        type="button"
                        className="chip"
                        onClick={() => openDeepLink(d.href)}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                )}
                {t.steps && t.steps.length > 0 && (
                  <details className="cast-trace">
                    <summary>
                      Interaction steps ({t.steps.length})
                      {t.skills_invoked?.length ? ` · ${t.skills_invoked.join(", ")}` : ""}
                    </summary>
                    <ol>
                      {t.steps.map((step, j) => (
                        <li key={j}>
                          <code>{step.type}</code>
                          {step.skill ? ` · ${step.skill}` : ""}
                          {step.output_status ? ` · ${step.output_status}` : ""}
                          {step.duration_ms != null ? ` · ${step.duration_ms}ms` : ""}
                          {step.grounding_refs?.length ? ` · refs: ${step.grounding_refs.join(", ")}` : ""}
                        </li>
                      ))}
                    </ol>
                  </details>
                )}
              </div>
            )
          )}
        </div>
      )}

      {provenancePick && (
        <ProvenanceModal
          lat={provenancePick.lat}
          lng={provenancePick.lng}
          onClose={() => setProvenancePick(null)}
        />
      )}
    </div>
  );
}

export default function ExploreGuidePanel() {
  return (
    <Suspense fallback={<p className="muted">Loading exploration guide…</p>}>
      <ExploreGuidePanelInner />
    </Suspense>
  );
}

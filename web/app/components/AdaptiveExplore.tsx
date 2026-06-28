"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import SceneHost from "@/app/components/scene/SceneHost";
import ActiveSurfaceHost from "@/app/components/ActiveSurfaceHost";
import InterestForm from "@/app/components/InterestForm";
import { parseViewport, type MapViewport } from "@/lib/viewport";
import type { EventPoint } from "@/app/components/MapHero";
import { getJSON } from "@/lib/api";
import {
  ensureSession,
  intentToTurn,
  runAdaptiveTurn,
  type TurnContext,
} from "@/lib/adaptiveConsole";
import { mapViewportFromIntent, type PlanResponse, type UiIntentPanel } from "@/lib/uiIntent";
import type { SceneIntent } from "@/lib/sceneIntent";

const STARTER_PROMPTS = [
  "Which gates block promotion right now?",
  "Explain effective confidence vs raw confidence.",
  "Show me today's hotspots.",
];

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

function renderReply(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      return (
        <Link key={i} href={link[2]}>
          {link[1]}
        </Link>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function AdaptiveExploreInner({ signedIn }: { signedIn: boolean }) {
  const searchParams = useSearchParams();
  const [message, setMessage] = useState(STARTER_PROMPTS[0]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [focus, setFocus] = useState<{ lat: number; lng: number } | null>(null);
  const [events, setEvents] = useState<EventPoint[]>([]);
  const hydrophonePanel = useRef<UiIntentPanel | null>(null);

  useEffect(() => {
    const vp = parseViewport(searchParams);
    if (vp) setFocus({ lat: vp.lat, lng: vp.lng });
  }, [searchParams]);

  useEffect(() => {
    getJSON<{ events: Array<{ id: string; location?: { lat: number; lng: number }; source: string }> }>(
      "api/realtime/events",
    )
      .then((res) =>
        setEvents(
          (res.events ?? [])
            .filter((e) => e.location)
            .map((e) => ({ id: e.id, lat: e.location!.lat, lng: e.location!.lng, source: e.source })),
        ),
      )
      .catch(() => setEvents([]));
  }, []);

  const runTurn = useCallback(
    async (ctx: TurnContext, extraPanel?: UiIntentPanel | null) => {
      setBusy(true);
      setError(null);
      try {
        const sid = await ensureSession(sessionId);
        if (sid !== sessionId) setSessionId(sid);
        const resp = await runAdaptiveTurn(sid, ctx);
        if (extraPanel) {
          hydrophonePanel.current = extraPanel;
        }
        if (hydrophonePanel.current) {
          const exists = resp.ui_intent.panels.some((p) => p.id === "hydrophone_signal");
          if (!exists) {
            resp.ui_intent.panels = [hydrophonePanel.current, ...resp.ui_intent.panels];
          }
        }
        setPlan(resp);
        setTurns((prev) => [
          ...prev,
          { role: "user", content: ctx.message },
          { role: "assistant", content: resp.reply ?? "(no narration)" },
        ]);
        if (ctx.viewport) setFocus({ lat: ctx.viewport.lat, lng: ctx.viewport.lng });
        // WS-INTENT seam F (additive): a planner-returned map_viewport closes the
        // planner-to-camera loop. When the planner chose a place, prefer it over
        // the request viewport so SalishScene flies the live camera there. When no
        // map_viewport is present mapViewportFromIntent returns null and the
        // existing request-viewport behavior above is unchanged.
        const plannerViewport = mapViewportFromIntent(resp.ui_intent);
        if (plannerViewport) setFocus({ lat: plannerViewport.lat, lng: plannerViewport.lng });
      } catch (e) {
        setError(String(e));
      } finally {
        setBusy(false);
      }
    },
    [sessionId],
  );

  const onIntent = useCallback(
    (intent: SceneIntent) => {
      const ctx = intentToTurn(intent);
      setMessage(ctx.message);
      const extraPanel: UiIntentPanel | null =
        intent.type === "hydrophone"
          ? {
              id: "hydrophone_signal",
              surface: "sidebar",
              priority: 0,
              props: { station: intent.name ?? null, lat: intent.lat, lng: intent.lng },
            }
          : null;
      void runTurn(ctx, extraPanel);
    },
    [runTurn],
  );

  function submitMessage() {
    if (!message.trim()) return;
    const ctx: TurnContext = {
      message: message.trim(),
      viewport: focus ? { lat: focus.lat, lng: focus.lng, zoom: 11 } : null,
      focus: focus ? { cell: `${focus.lat},${focus.lng}` } : null,
    };
    void runTurn(ctx);
  }

  const fallbackViewport: MapViewport | null = focus
    ? { lat: focus.lat, lng: focus.lng, zoom: 11 }
    : null;

  return (
    <main className="explore-shell">
      <header className="explore-header">
        <h1 className="hero-title">orcast. Explore the Salish Sea</h1>
        <p className="hero-subtitle">
          A 3D, gate-bounded encounter forecast for the Salish Sea. Click the water or a hydrophone
          to ask the orchestrator. Every panel is grounded and every step is traced.
        </p>
        {!signedIn && (
          <p className="muted explore-anon-note">
            You can explore everything here without an account. Sign-in is only needed to submit
            sightings or annotations.
          </p>
        )}
      </header>

      <div className="explore-grid">
        <div className="explore-scene" data-demo="explore-scene">
          <SceneHost
            onIntent={onIntent}
            focus={focus}
            fallbackEvents={events}
            fallbackViewport={fallbackViewport}
          />
        </div>

        <aside className="explore-console" data-demo="explore-console">
          <div className="card">
            <div className="row" style={{ flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.6rem" }}>
              {STARTER_PROMPTS.map((p) => (
                <button key={p} type="button" className="chip" onClick={() => setMessage(p)}>
                  {p.length > 38 ? `${p.slice(0, 38)}…` : p}
                </button>
              ))}
            </div>
            <label>
              Ask the orchestrator
              <textarea
                rows={2}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about gates, provenance, or a hydrophone…"
              />
            </label>
            <div className="row" style={{ marginTop: "0.6rem" }}>
              <button
                type="button"
                data-demo="explore-send"
                onClick={submitMessage}
                disabled={busy || !message.trim()}
              >
                {busy ? "Orchestrating…" : "Send turn"}
              </button>
            </div>
            {error && <p className="error">{error}</p>}
          </div>

          {plan && (
            <ActiveSurfaceHost
              uiIntent={plan.ui_intent}
              prepare={plan.prepare}
              reply={plan.reply}
              signedIn={signedIn}
            />
          )}

          {turns.length > 0 && (
            <div className="card explore-replies">
              {turns
                .slice(-6)
                .map((t, i) =>
                  t.role === "user" ? (
                    <div key={i} className="ask-user">
                      <strong>You</strong>
                      <div>{t.content}</div>
                    </div>
                  ) : (
                    <div key={i} className="ask-assistant">
                      <strong style={{ display: "block" }}>Orchestrator</strong>
                      <div>{renderReply(t.content)}</div>
                    </div>
                  ),
                )}
            </div>
          )}

          <InterestForm />
        </aside>
      </div>
    </main>
  );
}

export default function AdaptiveExplore({ signedIn }: { signedIn: boolean }) {
  return (
    <Suspense fallback={<main className="container"><p className="muted">Loading explore…</p></main>}>
      <AdaptiveExploreInner signedIn={signedIn} />
    </Suspense>
  );
}

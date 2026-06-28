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
  runAdaptiveNarration,
  runAdaptiveNarrationStream,
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

// Orienting question -> trips branch. Selecting one threads focus.branch on the
// turn so the planner runs the matching trip branch (connections / kayak /
// sidequests); "General" clears it and falls back to the keyword planner.
const BRANCH_OPTIONS: Array<{ id: string; label: string; prompt: string }> = [
  { id: "visiting", label: "Planning a visit", prompt: "I'm planning a visit to the San Juans — how do I get there and what should I plan around?" },
  { id: "here-now", label: "I'm here now", prompt: "I'm here now near the water — what's around me and how do connections look?" },
  { id: "kayak", label: "Kayaking", prompt: "I want to kayak — when is the safe tide and current window?" },
  { id: "curious", label: "Just curious", prompt: "I'm just exploring — what can I look at right now?" },
];

interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  content: string;
  // assistant turn whose narration is still arriving (panels already painted)
  pending?: boolean;
  // narration tokens are streaming in: render plain text, defer markdown to end
  streaming?: boolean;
}

let turnSeq = 0;
function nextTurnId(): string {
  turnSeq += 1;
  return `t${turnSeq}`;
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
  const [branch, setBranch] = useState<string | null>(null);
  const [events, setEvents] = useState<EventPoint[]>([]);
  const hydrophonePanel = useRef<UiIntentPanel | null>(null);
  // Turn-generation guard + in-flight stream abort: a new message cancels the
  // previous narration stream and ignores its late tokens.
  const turnGenRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  // Id of the assistant bubble whose narration is still in flight, so a
  // superseding turn can clear its "Narrating…" state instead of stranding it.
  const pendingAssistantRef = useRef<string | null>(null);

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
      // Cancel any in-flight narration stream from a previous turn and bump the
      // generation so its late callbacks are ignored.
      abortRef.current?.abort();
      // m1: clear the superseded turn's "Narrating…" state so it never strands.
      const superseded = pendingAssistantRef.current;
      if (superseded) {
        setTurns((prev) =>
          prev.map((t) =>
            t.id === superseded && (t.pending || t.streaming)
              ? { ...t, pending: false, streaming: false, content: t.content || "(superseded)" }
              : t,
          ),
        );
        pendingAssistantRef.current = null;
      }
      const myGen = ++turnGenRef.current;
      const controller = new AbortController();
      abortRef.current = controller;
      setBusy(true);
      setError(null);
      try {
        const sid = await ensureSession(sessionId);
        if (sid !== sessionId) setSessionId(sid);
        // Phase 1: plan only. Panels paint now; narration is fetched after.
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
        const assistantId = nextTurnId();
        pendingAssistantRef.current = assistantId;
        setTurns((prev) => [
          ...prev,
          { id: nextTurnId(), role: "user", content: ctx.message },
          { id: assistantId, role: "assistant", content: "", pending: true },
        ]);
        if (ctx.viewport) setFocus({ lat: ctx.viewport.lat, lng: ctx.viewport.lng });
        // WS-INTENT seam F (additive): a planner-returned map_viewport closes the
        // planner-to-camera loop. When the planner chose a place, prefer it over
        // the request viewport so SalishScene flies the live camera there. When no
        // map_viewport is present mapViewportFromIntent returns null and the
        // existing request-viewport behavior above is unchanged.
        const plannerViewport = mapViewportFromIntent(resp.ui_intent);
        if (plannerViewport) setFocus({ lat: plannerViewport.lat, lng: plannerViewport.lng });
        // Panels are interactive now; release the send button before narration.
        setBusy(false);

        // Phase 2: narration. Reuses the planned context; its latency does not
        // gate first paint. Tokens stream in progressively (App Runner lane). On
        // any stream error we fall back to the non-streamed JSON path; the panels
        // always stand regardless.
        let acc = "";
        let raf = 0;
        const flush = () => {
          raf = 0;
          if (myGen !== turnGenRef.current) return;
          const text = acc;
          setTurns((prev) =>
            prev.map((t) =>
              t.id === assistantId ? { ...t, content: text, pending: false, streaming: true } : t,
            ),
          );
        };
        const finalize = (replyText: string) => {
          if (raf) cancelAnimationFrame(raf);
          if (pendingAssistantRef.current === assistantId) pendingAssistantRef.current = null;
          setPlan((prev) => (prev ? { ...prev, reply: replyText } : prev));
          setTurns((prev) =>
            prev.map((t) =>
              t.id === assistantId
                ? { ...t, content: replyText, pending: false, streaming: false }
                : t,
            ),
          );
        };
        try {
          const nar = await runAdaptiveNarrationStream(
            sid,
            ctx,
            resp,
            {
              onToken: (chunk) => {
                if (myGen !== turnGenRef.current) return;
                acc += chunk;
                // rAF-batch DOM updates so a fast token stream does not thrash.
                if (!raf) raf = requestAnimationFrame(flush);
              },
            },
            controller.signal,
          );
          if (myGen !== turnGenRef.current) return;
          finalize(nar.reply || acc || "(no narration)");
        } catch {
          // A new turn aborted this one: leave the stale turn alone.
          if (myGen !== turnGenRef.current || controller.signal.aborted) return;
          // Buffered / failed stream -> non-streamed JSON fallback (never hang).
          try {
            const nar = await runAdaptiveNarration(sid, ctx, resp);
            if (myGen !== turnGenRef.current) return;
            finalize(nar.reply || "(no narration)");
          } catch {
            if (myGen !== turnGenRef.current) return;
            finalize("(narration unavailable)");
          }
        }
      } catch (e) {
        setError(String(e));
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
    const focusCtx: { cell?: string; branch?: string } = {};
    if (focus) focusCtx.cell = `${focus.lat},${focus.lng}`;
    if (branch) focusCtx.branch = branch;
    const ctx: TurnContext = {
      message: message.trim(),
      viewport: focus ? { lat: focus.lat, lng: focus.lng, zoom: 11 } : null,
      focus: Object.keys(focusCtx).length ? focusCtx : null,
    };
    void runTurn(ctx);
  }

  function selectBranch(option: { id: string; prompt: string }) {
    const next = branch === option.id ? null : option.id;
    setBranch(next);
    // Seed a natural prompt for the chosen branch so the turn reads well in the
    // trace; the user can edit it before sending.
    if (next) setMessage(option.prompt);
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
            <div className="orienting-question" style={{ marginBottom: "0.6rem" }}>
              <span className="muted" style={{ display: "block", marginBottom: "0.35rem", fontSize: "0.85rem" }}>
                What brings you here?
              </span>
              <div className="row" style={{ flexWrap: "wrap", gap: "0.4rem" }}>
                {BRANCH_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    className="chip"
                    aria-pressed={branch === opt.id}
                    data-active={branch === opt.id ? "true" : undefined}
                    style={
                      branch === opt.id
                        ? { borderColor: "var(--accent, #5aa9e6)", color: "var(--accent, #5aa9e6)" }
                        : undefined
                    }
                    onClick={() => selectBranch(opt)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
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
                .map((t) =>
                  t.role === "user" ? (
                    <div key={t.id} className="ask-user">
                      <strong>You</strong>
                      <div>{t.content}</div>
                    </div>
                  ) : (
                    <div key={t.id} className="ask-assistant">
                      <strong style={{ display: "block" }}>Orchestrator</strong>
                      {t.pending ? (
                        <div className="muted" aria-live="polite">Narrating…</div>
                      ) : t.streaming ? (
                        // Mid-stream: plain text only, so partial **bold** / [links]
                        // never render half-parsed. Markdown applies at stream end.
                        <div aria-live="polite" style={{ whiteSpace: "pre-wrap" }}>
                          {t.content}
                        </div>
                      ) : (
                        <div>{renderReply(t.content)}</div>
                      )}
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

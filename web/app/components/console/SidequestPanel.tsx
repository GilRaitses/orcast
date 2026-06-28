"use client";

import GatedAction from "@/app/components/ui/GatedAction";

// Curiosity-branch sidequest panel (WS-TRIPS Producer D). Presentational only:
// phase-B wires the data (planner props + host renderer). Lists pairing prompts
// such as a hydrophone listen, a sighting replay, or a cell-score explainer,
// each carrying an honesty label and an invite into the trip platform. Shows an
// access-tier chip for the viewer (anonymous-public by default; this route stays
// anonymous-public) and a single inline confirm chip that authorizes a charter or
// wave from within the chat slot. The confirm + invite actions reuse GatedAction
// so anonymous users see why and get a sign-in link rather than a hidden surface.

// Honesty labels travel with every served field. Ordering of trust, strongest
// first: measured > published > modeled > heuristic.
export type HonestyLabel = "measured" | "published" | "modeled" | "heuristic";

// Viewer access tier. T0/T1 stay anonymous-public; T2/T3 are keyed-only. This
// route stays anonymous-public, so the default is "anonymous-public".
export type ViewerTier = "anonymous-public" | "keyed-reviewer" | "keyed-operator";

export type SidequestKind =
  | "hydrophone"
  | "sighting-replay"
  | "cell-score"
  | "explore";

export interface SidequestItem {
  id: string;
  kind?: SidequestKind;
  title: string;
  // The pairing prompt body. Ends by inviting the user into the trip platform.
  prompt: string;
  honestyLabel: HonestyLabel;
  // Invite into the trip platform. Renders as an anonymous-first gated action.
  invite?: { label: string; redirectTo?: string };
}

// Single inline confirm chip that authorizes a charter or wave on this turn.
export interface ConfirmChipSpec {
  label: string;
  reason?: string;
  redirectTo?: string;
  pending?: boolean;
}

export interface SidequestPanelProps {
  items?: SidequestItem[];
  viewerTier?: ViewerTier;
  confirm?: ConfirmChipSpec;
  note?: string;
}

const HONESTY_STYLE: Record<HonestyLabel, { label: string; color: string; background: string }> = {
  measured: { label: "measured", color: "var(--pass)", background: "rgba(70, 192, 138, 0.18)" },
  published: { label: "published", color: "var(--accent)", background: "rgba(79, 184, 216, 0.16)" },
  modeled: { label: "modeled", color: "var(--warn)", background: "rgba(216, 178, 79, 0.18)" },
  heuristic: { label: "heuristic", color: "var(--text-muted)", background: "rgba(139, 151, 167, 0.16)" },
};

type Audience = "public" | "reviewer";

const TIER_STYLE: Record<ViewerTier, { label: string; color: string; background: string }> = {
  "anonymous-public": {
    label: "Public view",
    color: "var(--text-muted)",
    background: "rgba(139, 151, 167, 0.16)",
  },
  "keyed-reviewer": {
    label: "Reviewer view",
    color: "var(--accent)",
    background: "rgba(79, 184, 216, 0.16)",
  },
  "keyed-operator": {
    label: "Operator view",
    color: "var(--pass)",
    background: "rgba(70, 192, 138, 0.18)",
  },
};

function HonestyBadge({ label }: { label: HonestyLabel }) {
  const s = HONESTY_STYLE[label];
  return (
    <span
      className="badge"
      style={{ color: s.color, background: s.background }}
      title={`Honesty label: ${s.label}`}
    >
      {s.label}
    </span>
  );
}

function TierChip({ tier }: { tier: ViewerTier }) {
  const s = TIER_STYLE[tier];
  return (
    <span
      className="badge"
      style={{ color: s.color, background: s.background }}
      data-tier={tier}
      title={s.label}
    >
      {s.label}
    </span>
  );
}

export default function SidequestPanel({
  props,
  signedIn = false,
  audience = "reviewer",
  onConfirm,
  onInvite,
}: {
  props?: SidequestPanelProps;
  signedIn?: boolean;
  // Copy/visibility tier. The anonymous public console hides the internal
  // access-tier chip; reviewer surfaces keep it.
  audience?: Audience;
  // The inline confirm chip emits this auth action on the turn when signed in.
  onConfirm?: () => void;
  // Per-sidequest invite into the trip platform when signed in.
  onInvite?: (id: string) => void;
}) {
  const items = props?.items ?? [];
  const tier = props?.viewerTier ?? "anonymous-public";
  const confirm = props?.confirm;

  return (
    <div className="console-panel" data-panel="sidequests">
      <div
        className="row"
        style={{ justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}
      >
        <h3 className="console-panel-title" style={{ margin: 0 }}>
          Sidequests
        </h3>
        {audience !== "public" && <TierChip tier={tier} />}
      </div>

      {props?.note && (
        <p className="muted" style={{ fontSize: "0.82rem", marginTop: "0.3rem" }}>
          {props.note}
        </p>
      )}

      {items.length === 0 ? (
        <p className="muted" style={{ fontSize: "0.85rem" }}>
          No sidequests for this turn yet. Ask the console or click the scene to surface detours.
        </p>
      ) : (
        <ul
          style={{
            listStyle: "none",
            margin: "0.6rem 0 0",
            padding: 0,
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          {items.map((item) => (
            <li
              key={item.id}
              data-sidequest-kind={item.kind ?? "explore"}
              style={{
                borderTop: "1px solid var(--border)",
                paddingTop: "0.6rem",
              }}
            >
              <div
                className="row"
                style={{ justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}
              >
                <strong style={{ fontSize: "0.9rem" }}>{item.title}</strong>
                <HonestyBadge label={item.honestyLabel} />
              </div>
              <p className="muted" style={{ fontSize: "0.84rem", margin: "0.35rem 0 0", lineHeight: 1.5 }}>
                {item.prompt}
              </p>
              {item.invite && (
                <div className="row" style={{ marginTop: "0.5rem" }}>
                  <GatedAction
                    label={item.invite.label}
                    signedIn={signedIn}
                    reason="Sign in to start planning this in the trip platform"
                    redirectTo={item.invite.redirectTo ?? "/explore"}
                    onAct={onInvite ? () => onInvite(item.id) : undefined}
                  />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {confirm && (
        <div
          className="row"
          style={{
            marginTop: "0.85rem",
            paddingTop: "0.6rem",
            borderTop: "1px solid var(--border)",
            alignItems: "center",
          }}
        >
          <GatedAction
            label={confirm.pending ? `${confirm.label}…` : confirm.label}
            signedIn={signedIn}
            reason={confirm.reason ?? "Sign in to authorize this charter without leaving the scene"}
            redirectTo={confirm.redirectTo ?? "/explore"}
            onAct={onConfirm}
          />
        </div>
      )}
    </div>
  );
}

import Link from "next/link";

export default function PromotionBreadcrumb({
  reprId,
  runId,
  decisionId,
  promoted,
}: {
  reprId?: string | null;
  runId?: string | null;
  decisionId?: string | null;
  promoted?: boolean;
}) {
  return (
    <div className="callout">
      <p className="callout-title">Evidence chain</p>
      <p className="muted" style={{ margin: 0 }}>
        Fit <code>{reprId || "current"}</code> → gates <code>{runId || "current"}</code> →{" "}
        decision <code>{decisionId || "pending"}</code> → {promoted ? "promoted" : "unpromoted"}
      </p>
      <p style={{ marginBottom: 0, marginTop: "0.6rem", fontSize: "0.88rem" }}>
        <Link href="/review-dossier/latest">Open review dossier</Link>
      </p>
    </div>
  );
}

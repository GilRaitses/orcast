import Link from "next/link";

export default function IntegrityConditions({
  items,
  title = "Integrity conditions for this fit",
  compact = false,
}: {
  items: string[];
  title?: string;
  compact?: boolean;
  limit?: number;
}) {
  if (!items.length) return null;
  const shown = compact ? items.slice(0, 3) : items;

  return (
    <div className="integrity-callout">
      <p className="integrity-callout-title">
        {title}{" "}
        <Link href="/glossary#integrity-conditions" className="integrity-glossary-link">
          What are these?
        </Link>
      </p>
      <ul className={compact ? "integrity-list compact" : "integrity-list"}>
        {shown.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
      {compact && items.length > shown.length && (
        <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 0 }}>
          +{items.length - shown.length} more on the{" "}
          <Link href="/gates">Gates</Link> page.
        </p>
      )}
    </div>
  );
}

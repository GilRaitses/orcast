"use client";

import Link from "next/link";
import { GLOSSARY } from "@/lib/glossary";

export default function GlossaryTerm({
  id,
  children,
  asLink = true,
}: {
  id: string;
  children?: React.ReactNode;
  asLink?: boolean;
}) {
  const entry = GLOSSARY[id];
  const label = children ?? entry?.term ?? id;

  if (!entry) {
    return <span>{label}</span>;
  }

  return (
    <span className="glossary-term">
      <span className="glossary-term-label">{label}</span>
      <button
        type="button"
        className="glossary-info"
        aria-label={`Explain ${entry.term}`}
        aria-describedby={`glossary-tip-${id}`}
      >
        ⓘ
      </button>
      <span className="glossary-tip" id={`glossary-tip-${id}`} role="tooltip">
        <strong>{entry.term}</strong>
        <p>{entry.tooltip}</p>
        {asLink && (
          <Link href={`/glossary#${id}`} className="glossary-tip-link">
            Open glossary entry →
          </Link>
        )}
      </span>
    </span>
  );
}

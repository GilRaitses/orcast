import Link from "next/link";
import { GLOSSARY, GLOSSARY_ORDER } from "@/lib/glossary";

export const metadata = {
  title: "Glossary — orcast",
  description: "Ontology, provenance, and plain-language definitions for forecast gates and integrity conditions.",
};

export default function GlossaryPage() {
  return (
    <main className="container glossary-page">
      <div className="card">
        <h1 style={{ marginTop: 0 }}>Glossary &amp; ontology</h1>
        <p className="muted" style={{ maxWidth: "70ch", lineHeight: 1.55 }}>
          Definitions for fitness gates, integrity conditions, and provenance fields used across the forecast,
          gates dashboard, and review dossier. Each entry notes where the term appears in the product and where
          it is computed in the pipeline.
        </p>
        <p className="muted" style={{ fontSize: "0.9rem" }}>
          Quick jump:{" "}
          {GLOSSARY_ORDER.map((id, i) => (
            <span key={id}>
              {i > 0 && " · "}
              <a href={`#${id}`}>{GLOSSARY[id].term}</a>
            </span>
          ))}
        </p>
      </div>

      {GLOSSARY_ORDER.map((id) => {
        const entry = GLOSSARY[id];
        return (
          <article key={id} id={id} className="card glossary-entry">
            <h2 style={{ marginTop: 0 }}>{entry.term}</h2>
            <p className="glossary-lead">{entry.body}</p>
            <dl className="glossary-meta">
              <div>
                <dt>Used in</dt>
                <dd>{entry.usedIn.join(" · ")}</dd>
              </div>
              {entry.provenance && (
                <div>
                  <dt>Provenance</dt>
                  <dd><code>{entry.provenance}</code></dd>
                </div>
              )}
              {entry.seeAlso && entry.seeAlso.length > 0 && (
                <div>
                  <dt>See also</dt>
                  <dd>
                    {entry.seeAlso.map((ref, i) => (
                      <span key={ref}>
                        {i > 0 && ", "}
                        <Link href={`#${ref}`}>{GLOSSARY[ref]?.term ?? ref}</Link>
                      </span>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          </article>
        );
      })}

      <p className="muted" style={{ fontSize: "0.9rem" }}>
        <Link href="/gates">← Back to fitness gates</Link>
      </p>
    </main>
  );
}

export const metadata = {
  title: "About orcast",
  description:
    "What orcast can do today, what it cannot yet do, and where it is headed. An honest capabilities and limits profile for an evidence-bounded whale encounter forecast.",
};

type Item = { label: string; body: string };

const CAPABILITIES: Item[] = [
  {
    label: "An always-on forecast you can question",
    body: "The Salish Sea encounter forecast is visible from the first moment, and its confidence is only as high as the automated fitness gates and a human reviewer have earned. You can tap any water cell to see why it looks the way it does.",
  },
  {
    label: "Provenance on every cell",
    body: "A click traces a cell back to the kernels, the gate verdicts, and a nearby evidence sample. Nothing on the map is asserted without a back-link to the data behind it.",
  },
  {
    label: "A console that turns intent into a plan",
    body: "Tell the console what you are doing, a visit, being here now, or a kayak outing, and it builds the map, gates, and provenance panels for that trip on top of the same forecast.",
  },
  {
    label: "A sighting check",
    body: "Drop a pin and describe what you saw. The check separates how likely an encounter was from whether your observation was actually an orca, grounded in the same gates and provenance as the forecast.",
  },
  {
    label: "A private field journal and a moderated community queue",
    body: "Your notes stay private until you choose to publish. Shore reports are held in a moderation queue until a signed-in reviewer approves them, which attaches attribution and a low reliability weight.",
  },
  {
    label: "A research workbench, in progress",
    body: "Reviewers can annotate hydrophone detections and work the moderation queue today. A modeled terrain and bathymetry 3D twin of the San Juan Islands runs in the research sandbox.",
  },
];

const RATIFIED_LIMITS: Item[] = [
  {
    label: "The acoustic signal is thin",
    body: "Acoustic detection rests on a single hydrophone station and the detections are sparse. A detection is a model confidence score, not a human-reviewed certainty.",
  },
  {
    label: "Sightings are effort-biased",
    body: "Community and citizen-science sightings reflect where people looked as much as where whales were, so the gates downweight them.",
  },
  {
    label: "The forecast does not oversell",
    body: "In the pilot the gates decline to promote high confidence, so the public forecast shows an honest 0% rather than a falsely precise number. This is the point, not a bug.",
  },
  {
    label: "The pilot is one region",
    body: "The forecast is scoped to the San Juan and Salish core. Cells outside it are honest blanks, not predictions.",
  },
  {
    label: "Some research tools are direction, not delivered",
    body: "The 3D twin is modeled in the sandbox rather than shipped as a route, and tag-dive replay and a full annotation workbench are where the build is heading, not what ships today.",
  },
];

const FUTURE: Item[] = [
  {
    label: "More acoustic coverage",
    body: "A multi-station relay with human-reviewed detections, so the acoustic signal stops being a single thin source.",
  },
  {
    label: "More of the picture in the model",
    body: "Effort correction and added environmental covariates, each re-run through the same fitness gates before it can change a confidence number.",
  },
  {
    label: "A shipped research workbench",
    body: "The 3D twin as a real research route, tag-dive replay, and collaborative annotation that advance both the forecast and the behavior analysis behind it.",
  },
  {
    label: "A managed orchestration console",
    body: "An AI orchestration layer that runs the routines across both the visitor and research sides, for the shared benefit of visitors, researchers, and the whales themselves.",
  },
];

function Cards({ items }: { items: Item[] }) {
  return (
    <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: "0.75rem" }}>
      {items.map((it) => (
        <li key={it.label} style={{ lineHeight: 1.55 }}>
          <strong style={{ display: "block" }}>{it.label}</strong>
          <span className="muted">{it.body}</span>
        </li>
      ))}
    </ul>
  );
}

export default function AboutPage() {
  return (
    <main className="container">
      <div className="card">
        <h1 style={{ marginTop: 0 }}>About orcast</h1>
        <p className="muted" style={{ maxWidth: "72ch", lineHeight: 1.55 }}>
          orcast is a two-sided loop around Salish Sea killer whales. An encounter forecast is the grounding
          layer that a public visitor console and a behavior-analysis research workbench both stand on, and an
          AI orchestration layer is being built for the shared benefit of the people who visit, the researchers
          who study whale behavior, and the whales themselves. This page is an honest profile of what orcast can
          do today, what it cannot yet do, and where it is headed.
        </p>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>What it can do today</h2>
        <Cards items={CAPABILITIES} />
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>What it cannot do yet, and why</h2>
        <p className="muted" style={{ maxWidth: "72ch", lineHeight: 1.55 }}>
          These are honest limits of the pilot, most of them scientific or scope rather than engineering. They
          define where the forecast applies today and where it has to be retested as more data arrives.
        </p>
        <Cards items={RATIFIED_LIMITS} />
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Where it is headed</h2>
        <Cards items={FUTURE} />
      </div>
    </main>
  );
}

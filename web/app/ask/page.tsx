import SightingCheckPanel from "@/app/components/SightingCheckPanel";

export default function AskPage() {
  return (
    <main className="container">
      <h1 className="hero-title" style={{ fontSize: "1.75rem" }}>
        Sighting check
      </h1>
      <p className="hero-subtitle">
        Drop a pin where you were, describe what you saw, and see encounter likelihood vs sighting verification grounded in the same gates and provenance as the forecast.
      </p>
      <SightingCheckPanel />
    </main>
  );
}

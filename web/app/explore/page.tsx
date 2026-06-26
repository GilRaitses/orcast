import ExploreGuidePanel from "@/app/components/ExploreGuidePanel";

export default function ExplorePage() {
  return (
    <main className="container">
      <h1 className="hero-title" style={{ fontSize: "1.75rem" }}>
        Exploration guide
      </h1>
      <p className="hero-subtitle">
        Navigate gates and provenance — grounded in the same fitness records as the forecast, not a separate AI oracle.
      </p>
      <ExploreGuidePanel />
    </main>
  );
}

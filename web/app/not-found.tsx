import Link from "next/link";

export default function NotFound() {
  return (
    <main className="container">
      <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
        <div className="brand">orcast</div>
        <h1 className="hero-title" style={{ marginTop: "0.5rem" }}>This page isn&apos;t on the map</h1>
        <p className="hero-subtitle" style={{ margin: "0.5rem auto 1.5rem" }}>
          The forecast you were looking for doesn&apos;t exist here. Let&apos;s get you back to open water.
        </p>
        <Link className="btn" href="/">Back to the forecast</Link>
      </div>
    </main>
  );
}

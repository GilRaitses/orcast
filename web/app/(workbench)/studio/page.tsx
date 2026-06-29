import type { Metadata } from "next";
import Link from "next/link";
import styles from "./studio.module.css";

// Net-new BSS studio landing at /studio. The (workbench) route group adds no URL
// segment, so /studio and its children never collide with the existing
// /workbench slice route (O0 gate 1, Option B).
export const metadata: Metadata = {
  title: "Processing studio",
  description:
    "Annotation studio, reusable tagtools pipeline, and behavior capture for the B-side workbench.",
  robots: { index: false, follow: false },
};

export default function StudioIndexPage() {
  return (
    <main className={styles.root}>
      <h1 className={styles.title}>Processing studio</h1>
      <p className={styles.lede}>
        A reusable processing surface the orchestrated console can invoke. Annotation,
        a tagtools pipeline, and behavior capture, all grounded in real DTAG data.
      </p>
      <div className={styles.grid}>
        <Link href="/studio/annotate" className={styles.card}>
          <h2 className={styles.cardTitle}>Annotate</h2>
          <p className={styles.cardBody}>
            Annotate real DTAG kinematics and round-trip a provenance-tagged annotation.
            Live now.
          </p>
        </Link>
        <div className={styles.cardMuted}>
          <h2 className={styles.cardTitle}>Tagtools pipeline</h2>
          <p className={styles.cardBody}>
            Calibration, orientation, ODBA, dive detection, and stroke and glide steps.
            Served as managed skills. Panels wire in at integration.
          </p>
        </div>
        <div className={styles.cardMuted}>
          <h2 className={styles.cardTitle}>Behavior capture</h2>
          <p className={styles.cardBody}>
            Block, camera test, and screen test a real classified behavior into a 3D capture.
            Served as a managed skill. Panels wire in at integration.
          </p>
        </div>
      </div>
    </main>
  );
}

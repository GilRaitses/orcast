"use client";

import { STATION_POVS, type StationPov } from "@/lib/scene/hydrophone";
import styles from "./povChip.module.css";

// Glass POV control. The segments are data-driven from the reusable POV object
// (STATION_POVS), so the control renders whatever the object defines. The
// active segment uses the accent ink colour. Local .bsw-glass fallback while
// LGC tokens are unbuilt; no classes are added to the convergence globals.css.

const SEGMENTS: Array<{ value: StationPov; label: string }> = STATION_POVS.map((p) => ({
  value: p.id,
  label: p.label,
}));

export default function PovChip({
  value,
  onChange,
}: {
  value: StationPov;
  onChange: (pov: StationPov) => void;
}) {
  return (
    <div className={styles["bsw-glass"]} role="radiogroup" aria-label="Camera point of view">
      {SEGMENTS.map((seg) => {
        const active = seg.value === value;
        return (
          <button
            key={seg.value}
            type="button"
            role="radio"
            aria-checked={active}
            className={
              active
                ? `${styles["bsw-segment"]} ${styles["bsw-segment-active"]}`
                : styles["bsw-segment"]
            }
            onClick={() => onChange(seg.value)}
          >
            {seg.label}
          </button>
        );
      })}
    </div>
  );
}

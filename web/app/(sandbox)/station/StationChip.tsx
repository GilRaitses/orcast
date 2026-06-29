"use client";

import type { StationCatalogEntry } from "@/lib/scene/hydrophone";
import styles from "./povChip.module.css";

// Station-selection glass control for the sandbox. Lists the real Orcasound
// nodes inside the rendered tileset extent (the same set GET /api/live-hydrophones
// serves). Each chip shows the station name, an online/offline dot, and the
// MODELED node class. Same .bsw-glass tokens as the POV control; no globals.css.

export default function StationChip({
  stations,
  value,
  onChange,
}: {
  stations: StationCatalogEntry[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className={styles["bsw-station-rack"]} role="radiogroup" aria-label="Hydrophone station">
      <div className={styles["bsw-station-rack-title"]}>Station</div>
      {stations.map((s) => {
        const active = s.id === value;
        const dotClass = s.status === "online" ? "bsw-station-online" : "bsw-station-offline";
        return (
          <button
            key={s.id}
            type="button"
            role="radio"
            aria-checked={active}
            className={
              active ? `${styles["bsw-station"]} ${styles["bsw-station-active"]}` : styles["bsw-station"]
            }
            onClick={() => onChange(s.id)}
          >
            <span
              className={`${styles["bsw-station-dot"]} ${styles[dotClass]}`}
              aria-hidden="true"
            />
            <span className={styles["bsw-station-meta"]}>
              <span className={styles["bsw-station-name"]}>{s.name}</span>
              <span className={styles["bsw-station-class"]}>
                {s.nodeClass === "mooring" ? "mooring (modeled)" : "cabled (modeled)"}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

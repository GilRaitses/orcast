"use client";

// SSR-safe host (mirrors the verified /slice SliceHost reference): the r3f +
// WebGL + WebAudio + Web Worker composition must never be imported during SSR.

import dynamic from "next/dynamic";
import styles from "./workbench.module.css";

const WorkbenchScene = dynamic(() => import("./WorkbenchScene"), {
  ssr: false,
  loading: () => (
    <div className={styles["bsw-loading"]}>Loading B-side acoustic + behavior workbench…</div>
  ),
});

export default function WorkbenchHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <WorkbenchScene />
    </div>
  );
}

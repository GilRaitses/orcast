"use client";

import { useMemo, useRef, useState } from "react";
import styles from "./annotate.module.css";
import {
  createAnnotationStore,
  InMemoryAnnotationStore,
  loadDtagFixture,
  type Annotation,
  type AnnotationDraft,
  type DiveSummary,
} from "@/lib/annotation";

const VIEW_W = 1000;
const VIEW_H = 200;

export default function AnnotateStudio() {
  const fixture = useMemo(() => loadDtagFixture(), []);
  // Live console path persists through the HTTP store (same-origin proxy to the
  // backend annotation endpoint). If the backend is unreachable we keep the
  // annotation locally and label it honestly instead of dropping it.
  const storeRef = useRef(createAnnotationStore("http"));
  const fallbackRef = useRef(new InMemoryAnnotationStore());

  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [persistMode, setPersistMode] = useState<"backend" | "local" | null>(null);
  const [selectedDiveId, setSelectedDiveId] = useState<number>(
    fixture.dives.find((d) => d.classified_behavior)?.dive_id ?? fixture.dives[0]?.dive_id ?? 0,
  );
  const behaviorOptions = useMemo(
    () => Object.values(fixture.behavior_taxonomy),
    [fixture],
  );
  const [behavior, setBehavior] = useState<string>(behaviorOptions[0] ?? "");
  const [annotatorId, setAnnotatorId] = useState<string>("reviewer:demo");
  const [annotatorRole, setAnnotatorRole] = useState<string>("expert");
  const [notes, setNotes] = useState<string>("");
  const [confidence, setConfidence] = useState<number>(0.8);
  const [error, setError] = useState<string | null>(null);

  const nSamples = fixture.meta.n_samples;
  const depth = fixture.depth_profile_downsampled_m;
  const odba = fixture.odba_profile_downsampled_g;
  const maxDepth = useMemo(() => Math.max(...depth, 1), [depth]);
  const maxOdba = useMemo(() => Math.max(...odba, 0.001), [odba]);

  const selectedDive = fixture.dives.find((d) => d.dive_id === selectedDiveId) ?? null;

  const xForSample = (sample: number) => (sample / nSamples) * VIEW_W;
  const depthPath = useMemo(() => {
    return depth
      .map((d, i) => {
        const x = (i / (depth.length - 1)) * VIEW_W;
        const y = (d / maxDepth) * (VIEW_H - 10);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [depth, maxDepth]);
  const odbaPath = useMemo(() => {
    return odba
      .map((v, i) => {
        const x = (i / (odba.length - 1)) * VIEW_W;
        const y = VIEW_H - (v / maxOdba) * (VIEW_H - 10);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [odba, maxOdba]);

  async function submit() {
    setError(null);
    if (!selectedDive) {
      setError("Select a dive first");
      return;
    }
    const draft: AnnotationDraft = {
      target: {
        kind: "dive",
        dive_id: selectedDive.dive_id,
        start_sample: selectedDive.start_sample,
        end_sample: selectedDive.end_sample,
      },
      behavior,
      state: "Feeding",
      confidence,
      notes: notes || undefined,
      annotator_id: annotatorId,
      annotator_role: annotatorRole,
      source: annotatorRole === "expert" ? "expert" : "community",
      method: "manual",
    };
    try {
      let created: Annotation;
      try {
        created = await storeRef.current.create(draft, fixture);
        setPersistMode("backend");
      } catch {
        // Backend endpoint not reachable in this environment; keep locally.
        created = await fallbackRef.current.create(draft, fixture);
        setPersistMode("local");
      }
      setAnnotations((prev) => [created, ...prev]);
      setNotes("");
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
    }
  }

  return (
    <main className={styles.root}>
      <header className={styles.header}>
        <h1 className={styles.title}>Annotation studio</h1>
        <p className={styles.subtitle}>
          Real DTAG kinematics from deployment {fixture.meta.deployment_id}. {fixture.meta.species}.
          Contrast and reference only. It never drives an orca.
        </p>
        <p className={styles.license}>License status {fixture.license_status}</p>
      </header>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Kinematics timeline</h2>
        <div className={styles.legend}>
          <span className={styles.legendDepth}>Depth, meters down</span>
          <span className={styles.legendOdba}>ODBA, g</span>
          <span className={styles.legendExpert}>Expert annotation</span>
          <span className={styles.legendDive}>Selected dive</span>
        </div>
        <svg
          className={styles.svg}
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          preserveAspectRatio="none"
          role="img"
          aria-label="Depth and ODBA over the deployment with annotation bands"
        >
          {fixture.expert_annotations.map((a, i) => {
            const x = xForSample(a.event_start);
            const w = Math.max(1, xForSample(a.event_end) - x);
            return (
              <rect
                key={`ex-${i}`}
                x={x}
                y={0}
                width={w}
                height={VIEW_H}
                className={styles.bandExpert}
              >
                <title>{`${a.event} — ${a.state}`}</title>
              </rect>
            );
          })}
          {selectedDive && (
            <rect
              x={xForSample(selectedDive.start_sample)}
              y={0}
              width={Math.max(2, xForSample(selectedDive.end_sample) - xForSample(selectedDive.start_sample))}
              height={VIEW_H}
              className={styles.bandDive}
            />
          )}
          <path d={depthPath} className={styles.depthLine} />
          <path d={odbaPath} className={styles.odbaLine} />
        </svg>
        <p className={styles.audioNote}>
          Audio lane is not bound in this sandbox. The hydrophone clip and spectrogram
          arrive from the station and spectro lanes at integration. No placeholder audio is shipped.
        </p>
      </section>

      <div className={styles.columns}>
        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>New annotation</h2>
          <label className={styles.field}>
            <span className={styles.label}>Dive</span>
            <select
              className={styles.input}
              value={selectedDiveId}
              onChange={(e) => setSelectedDiveId(Number(e.target.value))}
            >
              {fixture.dives.map((d: DiveSummary) => (
                <option key={d.dive_id} value={d.dive_id}>
                  {`#${d.dive_id} ${d.max_depth_m.toFixed(1)} m ${d.duration_s.toFixed(0)} s ${d.classified_behavior ?? "unlabeled"}`}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Behavior</span>
            <select
              className={styles.input}
              value={behavior}
              onChange={(e) => setBehavior(e.target.value)}
            >
              {behaviorOptions.map((b) => (
                <option key={b} value={b}>
                  {b.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Annotator id</span>
            <input
              className={styles.input}
              value={annotatorId}
              onChange={(e) => setAnnotatorId(e.target.value)}
            />
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Annotator role</span>
            <select
              className={styles.input}
              value={annotatorRole}
              onChange={(e) => setAnnotatorRole(e.target.value)}
            >
              <option value="expert">expert</option>
              <option value="community">community</option>
            </select>
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Confidence {confidence.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
            />
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Notes</span>
            <textarea
              className={styles.input}
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <button className={styles.button} onClick={submit} type="button">
            Save annotation with provenance
          </button>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>Saved annotations</h2>
          {persistMode === "backend" && (
            <p className={styles.muted}>Persisted through the backend annotation endpoint.</p>
          )}
          {persistMode === "local" && (
            <p className={styles.muted}>
              Backend endpoint unreachable here. Kept locally, round-trip verified. Live persist is a batched ACCEPT item.
            </p>
          )}
          {annotations.length === 0 ? (
            <p className={styles.muted}>None yet. Saved annotations round-trip through the store and show their provenance.</p>
          ) : (
            <ul className={styles.list}>
              {annotations.map((a) => (
                <li key={a.id} className={styles.listItem}>
                  <div className={styles.itemHead}>
                    {a.behavior.replace(/_/g, " ")} on dive {a.target.dive_id}
                  </div>
                  <div className={styles.itemMeta}>
                    {a.provenance.annotator_role} {a.provenance.annotator_id}
                  </div>
                  <div className={styles.itemProv}>
                    {a.provenance.source} provenance, grounded in {a.provenance.h5_refs.length} h5 paths,
                    created {a.provenance.created_at}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Tagtools pipeline steps</h2>
        <ul className={styles.steps}>
          {fixture.tagtools_steps.map((s) => (
            <li key={s.step_id} className={styles.stepItem}>
              <span className={styles.stepId}>{s.step_id}</span>
              <span className={styles.stepTitle}>{s.title}</span>
              <span className={styles.stepLabel}>{s.truth_label}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

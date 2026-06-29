// BSS annotation domain types. Net-new, console-independent. The annotation
// studio reads the real h5-derived fixture (baked by infra/tagtools/bake.py)
// and round-trips a provenance-tagged annotation through an AnnotationStore.

export type AnnotationSource = "expert" | "community" | "model";
export type AnnotationMethod = "manual" | "derived";

// Provenance is first-class: every annotation records who made it, against which
// real dataset, which h5 paths ground it, and the license status of the source.
export interface AnnotationProvenance {
  dataset: string;
  deployment_id: string;
  source: AnnotationSource;
  annotator_id: string;
  annotator_role: string;
  method: AnnotationMethod;
  h5_refs: string[];
  license_status: string;
  tool: string;
  created_at: string;
}

export interface AnnotationTarget {
  kind: "dive" | "time_range";
  dive_id?: number;
  start_sample: number;
  end_sample: number;
}

export interface Annotation {
  id: string;
  target: AnnotationTarget;
  behavior: string;
  state?: string;
  confidence?: number;
  notes?: string;
  provenance: AnnotationProvenance;
}

// A draft carries everything except server-assigned id + creation timestamp.
export interface AnnotationDraft {
  target: AnnotationTarget;
  behavior: string;
  state?: string;
  confidence?: number;
  notes?: string;
  annotator_id: string;
  annotator_role: string;
  source: AnnotationSource;
  method: AnnotationMethod;
}

// ---- Real h5-derived fixture shape (produced by infra/tagtools/bake.py) ----

export interface ExpertAnnotationRecord {
  whale_id: string;
  sample_hz: number;
  event_start: number;
  event_end: number;
  state: string;
  event: string;
}

export interface TagtoolsStepSummary {
  step_id: string;
  title: string;
  truth_label: string;
  reproduces_h5_path: string | null;
  summary: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface DiveSummary {
  dive_id: number;
  start_sample: number;
  max_depth_sample: number;
  end_sample: number;
  max_depth_m: number;
  duration_s: number;
  classified_behavior: string | null;
}

export interface DtagFixture {
  schema_version: string;
  meta: {
    deployment_id: string;
    species: string;
    role: string;
    sample_rate_hz: number;
    n_samples: number;
    duration_s: number;
  };
  behavior_taxonomy: Record<string, string>;
  expert_annotations: ExpertAnnotationRecord[];
  tagtools_steps: TagtoolsStepSummary[];
  step_descriptors: Array<Record<string, unknown>>;
  dives: DiveSummary[];
  depth_profile_downsampled_m: number[];
  odba_profile_downsampled_g: number[];
  provenance: Record<string, string>;
  license: string;
  license_status: string;
  attribution: string;
  source: string;
  privacy_note: string;
}

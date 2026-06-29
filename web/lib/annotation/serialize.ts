import type { Annotation, AnnotationDraft } from "./types";

// Transport payload for persisting an annotation. Shaped to match the existing
// orcast submission contract style (a JSON body the same-origin proxy forwards;
// the server assigns id + status), extended with the first-class provenance
// block. The backend binding is wired at BSS-INTEGRATE (see studio WIRING.md).

export interface AnnotationSubmissionRequest {
  deployment_id: string;
  target: Annotation["target"];
  behavior: string;
  state?: string;
  confidence?: number;
  notes?: string;
  provenance: {
    source: string;
    annotator_id: string;
    annotator_role: string;
    method: string;
    dataset: string;
    h5_refs: string[];
    license_status: string;
    tool: string;
  };
}

export interface AnnotationSubmissionResponse {
  id: string;
  status: string;
}

export function toSubmissionRequest(a: Annotation): AnnotationSubmissionRequest {
  return {
    deployment_id: a.provenance.deployment_id,
    target: a.target,
    behavior: a.behavior,
    state: a.state,
    confidence: a.confidence,
    notes: a.notes,
    provenance: {
      source: a.provenance.source,
      annotator_id: a.provenance.annotator_id,
      annotator_role: a.provenance.annotator_role,
      method: a.provenance.method,
      dataset: a.provenance.dataset,
      h5_refs: a.provenance.h5_refs,
      license_status: a.provenance.license_status,
      tool: a.provenance.tool,
    },
  };
}

export function draftToTarget(draft: AnnotationDraft): Annotation["target"] {
  return draft.target;
}

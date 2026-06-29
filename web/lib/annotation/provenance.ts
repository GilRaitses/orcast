import type {
  Annotation,
  AnnotationDraft,
  AnnotationProvenance,
  DtagFixture,
} from "./types";

export const ANNOTATION_TOOL = "bss-annotation-studio-v1";

// h5 paths an annotation on a dive window is grounded in.
const DIVE_H5_REFS = [
  "depth/values",
  "dives/dive_indices",
  "analysis/animal_frame_metrics/odba",
];

export function buildProvenance(
  draft: AnnotationDraft,
  fixture: DtagFixture,
  now: Date = new Date(),
): AnnotationProvenance {
  return {
    dataset: fixture.provenance.dataset ?? fixture.meta.deployment_id,
    deployment_id: fixture.meta.deployment_id,
    source: draft.source,
    annotator_id: draft.annotator_id,
    annotator_role: draft.annotator_role,
    method: draft.method,
    h5_refs: DIVE_H5_REFS,
    license_status: fixture.license_status,
    tool: ANNOTATION_TOOL,
    created_at: now.toISOString(),
  };
}

// Provenance is required and must be complete: an annotation without a known
// annotator, dataset, and license status is rejected.
export function validateProvenance(p: AnnotationProvenance): string[] {
  const errors: string[] = [];
  if (!p.annotator_id) errors.push("missing annotator_id");
  if (!p.annotator_role) errors.push("missing annotator_role");
  if (!p.dataset) errors.push("missing dataset");
  if (!p.deployment_id) errors.push("missing deployment_id");
  if (!p.license_status) errors.push("missing license_status");
  if (!p.created_at) errors.push("missing created_at");
  return errors;
}

export function provenanceIntact(a: Annotation, b: Annotation): boolean {
  return JSON.stringify(a.provenance) === JSON.stringify(b.provenance);
}

import type { Annotation, AnnotationDraft, DtagFixture } from "./types";
import { buildProvenance, validateProvenance } from "./provenance";
import {
  toSubmissionRequest,
  type AnnotationSubmissionResponse,
} from "./serialize";

// An AnnotationStore round-trips a provenance-tagged annotation: create -> persist
// -> read back. Two implementations:
//   - InMemoryAnnotationStore: deterministic, used by the sandbox round-trip
//     harness and as the studio's local-first store.
//   - HttpAnnotationStore: posts through the same-origin proxy to the backend
//     annotations endpoint (wired at BSS-INTEGRATE).

export interface AnnotationStore {
  create(draft: AnnotationDraft, fixture: DtagFixture): Promise<Annotation>;
  list(deploymentId: string): Promise<Annotation[]>;
  get(id: string): Promise<Annotation | null>;
}

export class AnnotationValidationError extends Error {
  constructor(public readonly errors: string[]) {
    super(`invalid annotation: ${errors.join(", ")}`);
    this.name = "AnnotationValidationError";
  }
}

function assembleAnnotation(
  id: string,
  draft: AnnotationDraft,
  fixture: DtagFixture,
  now: Date,
): Annotation {
  const provenance = buildProvenance(draft, fixture, now);
  const provErrors = validateProvenance(provenance);
  if (provErrors.length > 0) throw new AnnotationValidationError(provErrors);
  if (!draft.behavior) throw new AnnotationValidationError(["missing behavior"]);
  if (draft.target.end_sample < draft.target.start_sample) {
    throw new AnnotationValidationError(["end_sample before start_sample"]);
  }
  return {
    id,
    target: draft.target,
    behavior: draft.behavior,
    state: draft.state,
    confidence: draft.confidence,
    notes: draft.notes,
    provenance,
  };
}

let _counter = 0;
function localId(): string {
  _counter += 1;
  return `ann_local_${Date.now().toString(36)}_${_counter}`;
}

export class InMemoryAnnotationStore implements AnnotationStore {
  private readonly byId = new Map<string, Annotation>();

  constructor(private readonly clock: () => Date = () => new Date()) {}

  async create(draft: AnnotationDraft, fixture: DtagFixture): Promise<Annotation> {
    const annotation = assembleAnnotation(localId(), draft, fixture, this.clock());
    this.byId.set(annotation.id, annotation);
    return annotation;
  }

  async list(deploymentId: string): Promise<Annotation[]> {
    return [...this.byId.values()].filter(
      (a) => a.provenance.deployment_id === deploymentId,
    );
  }

  async get(id: string): Promise<Annotation | null> {
    return this.byId.get(id) ?? null;
  }
}

// Posts to the backend through the same-origin proxy (web/app/api/be/[...path]).
// The exact backend route is confirmed and allow-listed at BSS-INTEGRATE.
export class HttpAnnotationStore implements AnnotationStore {
  constructor(
    private readonly basePath = "/api/be/api/dtag/annotations",
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  async create(draft: AnnotationDraft, fixture: DtagFixture): Promise<Annotation> {
    const staged = assembleAnnotation("pending", draft, fixture, new Date());
    const res = await this.fetchImpl(this.basePath, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toSubmissionRequest(staged)),
    });
    if (!res.ok) throw new Error(`annotation_persist_failed:${res.status}`);
    const body = (await res.json()) as AnnotationSubmissionResponse;
    return { ...staged, id: body.id };
  }

  async list(deploymentId: string): Promise<Annotation[]> {
    const res = await this.fetchImpl(
      `${this.basePath}?deployment_id=${encodeURIComponent(deploymentId)}`,
    );
    if (!res.ok) throw new Error(`annotation_list_failed:${res.status}`);
    return (await res.json()) as Annotation[];
  }

  async get(id: string): Promise<Annotation | null> {
    const res = await this.fetchImpl(`${this.basePath}/${encodeURIComponent(id)}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`annotation_get_failed:${res.status}`);
    return (await res.json()) as Annotation;
  }
}

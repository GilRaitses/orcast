import type { AnnotationStore } from "./store";
import { HttpAnnotationStore, InMemoryAnnotationStore } from "./store";

export type AnnotationStoreKind = "http" | "memory";

// The live console path uses the HTTP store, which posts through the same-origin
// proxy to the backend annotation endpoint. Tests and the offline sandbox use
// the in-memory store. The backend route allow-listing is finalized at ACCEPT.
export function createAnnotationStore(kind: AnnotationStoreKind = "http"): AnnotationStore {
  return kind === "memory" ? new InMemoryAnnotationStore() : new HttpAnnotationStore();
}

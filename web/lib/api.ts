// Client helpers. Everything goes through the same-origin /api/be proxy so the
// backend API key stays server-side.

const PROXY = "/api/be";

export async function getJSON<T = any>(backendPath: string): Promise<T> {
  const res = await fetch(`${PROXY}/${backendPath.replace(/^\//, "")}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${backendPath} -> ${res.status}`);
  return res.json();
}

// Non-throwing variant: callers inspect status/ok and branch (e.g. 422 = out of
// modeled region) instead of catching a thrown error.
export interface FetchResult<T> {
  ok: boolean;
  status: number;
  data: T | null;
}

export async function getJSONResult<T = any>(backendPath: string): Promise<FetchResult<T>> {
  const res = await fetch(`${PROXY}/${backendPath.replace(/^\//, "")}`, { cache: "no-store" });
  let data: T | null = null;
  try {
    data = (await res.json()) as T;
  } catch {
    data = null;
  }
  return { ok: res.ok, status: res.status, data };
}

export async function postJSON<T = any>(backendPath: string, body: unknown): Promise<T> {
  const res = await fetch(`${PROXY}/${backendPath.replace(/^\//, "")}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) throw new Error(`POST ${backendPath} -> ${res.status}`);
  return res.json();
}

// Backend response shapes (partial, just what the UI reads).
export interface GatesResponse {
  status: string;
  confidence: number | null;
  effective_confidence?: number | null;
  promoted?: boolean;
  pending_approval?: {
    has_task_token?: boolean;
    recommendation?: { recommendation?: string; rationale?: string; cited_gates?: string[] };
  } | null;
  caveats?: string[];
  generated_at?: string;
  fit_plan_id?: string | null;
  dataset_snapshot_id?: string | null;
  snap_id?: string | null;
  repr_id?: string | null;
  run_id?: string | null;
  artifact_uris?: Record<string, string | null | undefined>;
  promotion?: Record<string, unknown> | null;
  data_inventory?: Record<string, unknown>;
  level0_detector_qc?: Record<string, unknown>;
  baseline_scorecard?: Record<string, unknown>;
  gates?: {
    level1_psth?: Record<string, { modulation: number; null_z: number; null_p: number; beats_null: boolean }>;
    cross_validation?: { n_pass?: number; n_folds?: number; mean_deviance_skill?: number; gate_pass?: boolean };
    time_rescaling?: { pooled_pass_exp?: boolean | null; pooled_ks_exp_pval?: number };
    pit?: { calibrated?: boolean; ks_pval?: number };
    consistency?: Record<string, { correlation?: number; agrees?: boolean }>;
  };
  metrics?: { mcfadden_r2?: number; deviance?: number };
  covariates_fit?: string[];
}

export interface SightingAssistStatus {
  status: string;
  bedrock_enabled?: boolean;
  bedrock_model?: string;
  narration_backend?: "bedrock" | "template" | "ollama" | string;
  fallback: string;
  setup_hint?: string;
  llm_enabled?: boolean;
  llm_reachable?: boolean;
  llm_model?: string;
  error?: string | null;
}

export interface SightingAssistResponse {
  status: string;
  reply: string;
  source: "bedrock" | "ollama" | "template" | string;
  model?: string | null;
  llm_error?: string;
  glossary_links?: string[];
  submit_path?: string;
  cell?: { lat: number; lng: number; when?: string };
  context_summary?: Record<string, unknown>;
}

export interface ExploreStatus extends SightingAssistStatus {
  aurora_enabled?: boolean;
  aurora_connected?: boolean;
  exploration_backend?: string;
}

export interface ExploreSessionResponse {
  status: string;
  session_id: string;
}

export interface ExploreTurnResponse {
  status: string;
  reply: string;
  citations: Array<{ label: string; href: string }>;
  deep_links: Array<{ label: string; href: string }>;
  source: string;
  model?: string | null;
  tools_used?: string[];
  llm_error?: string;
}

export interface InteractionAnnotation {
  type: string;
  label: string;
  href?: string;
  lat?: number;
  lng?: number;
  artifact?: Record<string, unknown> | null;
}

export interface InteractionStep {
  type: string;
  skill?: string;
  managed_agent_id?: string;
  agent_version?: string;
  resolved_spec_hash?: string;
  input?: Record<string, unknown>;
  output_status?: string;
  duration_ms?: number;
  grounding_refs?: string[];
  provider?: string;
  model?: string | null;
  text_preview?: string;
  annotations?: InteractionAnnotation[];
}

export interface InteractionResponse {
  status: string;
  interaction_id?: string;
  reply: string;
  citations: Array<{ label: string; href: string }>;
  deep_links: Array<{ label: string; href: string }>;
  source: string;
  model?: string | null;
  tools_used?: string[];
  llm_error?: string;
  managed_agent_id?: string;
  agent_version?: string;
  resolved_spec_hash?: string;
  hydration_mode?: string;
  skills_invoked?: string[];
  steps?: InteractionStep[];
  annotations?: InteractionAnnotation[];
  narration_path?: string;
}

export interface ProvenanceResponse {
  status: string;
  intensity: number;
  confidence: number;
  effective_confidence?: number | null;
  caveats?: string[];
  spatial?: { modeled: boolean; note?: string };
  kernel_contributions: Array<{
    kernel: string;
    available: boolean;
    phase?: number;
    log_rate_contribution?: number;
    beats_null?: boolean | null;
    null_p?: number | null;
  }>;
  nearby_sample: Array<{ sighting_id: string; distance_km: number; source: string; timestamp: string }>;
  trace_note: string;
}

export interface DecisionRecord {
  id: string;
  kernel_version?: string | null;
  verdict: "promote" | "hold" | "reject";
  reviewer?: string;
  reviewer_id?: string | null;
  reviewer_email?: string | null;
  reviewer_role?: string | null;
  reason?: string;
  gates_summary?: Record<string, unknown> | null;
  supervisor_recommendation?: {
    recommendation?: string;
    rationale?: string;
    cited_gates?: string[];
  } | null;
  created_at?: string;
}

export interface DecisionRecordsResponse {
  status: string;
  total_count: number;
  records: DecisionRecord[];
}

export interface ReviewDossier {
  dossier_id: string;
  workflow_stage: string;
  provenance: {
    snap_id?: string | null;
    repr_id?: string | null;
    run_id?: string | null;
    kernel_version?: string | null;
    artifact_refs?: Record<string, string | null | undefined>;
  };
  model_card: {
    confidence_raw?: number | null;
    confidence_effective?: number | null;
    promoted?: boolean;
    caveats?: string[];
    covariates_fit?: string[];
    covariates_excluded?: Record<string, unknown>;
  };
  gate_decision: {
    gate_pass_eligible?: boolean;
    gates?: Record<string, unknown>;
  };
  supervisor_recommendation?: {
    recommendation?: string;
    rationale?: string;
    cited_gates?: string[];
  } | null;
  human_decision?: DecisionRecord | null;
  prov?: {
    entities?: Array<Record<string, unknown>>;
    activities?: Array<Record<string, unknown>>;
    agents?: Array<Record<string, unknown>>;
    edges?: Array<Record<string, unknown>>;
  };
  replay?: {
    replay_status?: string;
  };
}

export interface ReviewDossierResponse {
  status: string;
  dossier: ReviewDossier;
}

export interface JournalEntry {
  id: string;
  user_id: string;
  user_email?: string | null;
  kind: string;
  title: string;
  place?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  observed_at?: string | null;
  body?: string | null;
  behavior: string;
  count?: number | null;
  community_submission_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JournalEntriesResponse {
  status: string;
  total_count: number;
  entries: JournalEntry[];
}

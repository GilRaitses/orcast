export interface ExploreViewport {
  lat: number;
  lng: number;
  zoom?: number;
}

export interface ExploreTurnRequest {
  session_id: string;
  message: string;
  viewport?: ExploreViewport;
  focus?: { cell?: string; gate_id?: string };
}

export interface ExploreCitation {
  label: string;
  href: string;
}

export interface ExploreTurnResponse {
  status: string;
  reply: string;
  citations: ExploreCitation[];
  deep_links: ExploreCitation[];
  source: string;
  model?: string | null;
  tools_used?: string[];
  llm_error?: string;
}

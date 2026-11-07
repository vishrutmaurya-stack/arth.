export type ApiStatus = "checking" | "online" | "offline";

export interface SourceInfo {
  id: string;
  type: string;
  title: string;
  url: string;
  chunks: number;
}

export interface Meta {
  chunk_count: number;
  source_count: number;
  sources: SourceInfo[];
  embedding_model: string;
  embedding_dimension: number | null;
  collection: string;
  retrieval_k: number;
  retrieval_min_score: number;
  api_version: string;
}

export interface Hit {
  chunk_id: string;
  score: number;
  distance: number;
  text: string;
  url: string;
  title: string;
  section: string;
  page_id: string;
  page_type: string;
  scraped_at: string;
}

export interface AskResult {
  query_id: string;
  decision: string;
  answer: string;
  citation_url: string | null;
  last_updated: string | null;
  educational_link: string | null;
  hits: Hit[];
}

export interface Turn {
  question: string;
  result: AskResult;
}

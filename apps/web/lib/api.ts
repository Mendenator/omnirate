export const API_BASE = process.env.OMNIRATE_API_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T | null> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export interface EntitySummary {
  entity_id: string;
  name: string;
  branch_slug: string;
  category_slug: string;
  location_slug?: string | null;
  score?: number;
  n_verified?: number;
}

export interface EntityDetail {
  id: string;
  name: string;
  branch_slug: string;
  category_slug: string;
  location_slug: string | null;
  lat: number | null;
  lon: number | null;
  attributes: Record<string, unknown>;
  verified: boolean;
  score: number;
  review_count: number;
  verified_review_count: number;
  criteria_breakdown: Record<string, number>;
}

export interface ReviewListItem {
  id: string;
  poe_level: string;
  overall_score: number;
  criteria_scores: Record<string, number>;
  body: string | null;
  owner_reply_body: string | null;
  owner_reply_at: string | null;
  created_at: string;
}

export interface CategorySchema {
  category_slug: string;
  version: number;
  json_schema: object;
  search_config: { facets?: { field: string; type: string; label_mn: string; order: number }[] };
  display_config: { sections: string[] };
}

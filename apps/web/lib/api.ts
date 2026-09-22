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
}

export interface EntityDetail {
  id: string;
  name: string;
  branch_slug: string;
  category_slug: string;
  location_slug: string | null;
  attributes: Record<string, unknown>;
  verified: boolean;
}

export interface CategorySchema {
  category_slug: string;
  version: number;
  json_schema: object;
  search_config: { facets?: { field: string; type: string; label_mn: string; order: number }[] };
  display_config: { sections: string[] };
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface EntitySummary {
  entity_id: string;
  name: string;
  branch_slug: string;
  category_slug: string;
}

interface SearchResponse {
  total: number;
  results: EntitySummary[];
  facets: Record<string, { buckets: { key: string; doc_count: number }[] }>;
}

// S-09: results page with facet panel + list. Debounced query -> autocomplete
// (K8 <=80ms) is a separate endpoint from the full search (K9 <=150ms) so the
// two latency budgets stay independently measurable.
export default function SearchClient() {
  const [q, setQ] = useState("");
  const [data, setData] = useState<SearchResponse | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (activeCategory) params.set("category_slug", activeCategory);
      fetch(`/api/backend/v1/search?${params}`)
        .then((r) => (r.ok ? r.json() : null))
        .then(setData);
    }, 200);
    return () => clearTimeout(handle);
  }, [q, activeCategory]);

  return (
    <div style={{ display: "flex", gap: 24, maxWidth: 960, margin: "0 auto", padding: 24 }}>
      <aside style={{ width: 200 }}>
        <h2>Салбар</h2>
        {data?.facets?.category_slug?.buckets.map((b) => (
          <label key={b.key} style={{ display: "block" }}>
            <input
              type="radio"
              name="category"
              checked={activeCategory === b.key}
              onChange={() => setActiveCategory(b.key)}
            />
            {b.key} ({b.doc_count})
          </label>
        ))}
        {activeCategory && <button onClick={() => setActiveCategory(null)}>Цэвэрлэх</button>}
      </aside>

      <main style={{ flex: 1 }}>
        <input
          autoFocus
          placeholder="Хайх..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ width: "100%", padding: 8, fontSize: 18 }}
        />

        {data && data.total === 0 && (
          <p>
            Илэрц олдсонгүй. Та ижил төстэй үгээр хайж үзнэ үү? (K11: zero-result fallback — S-15-д
            бүрэн хэрэгжинэ)
          </p>
        )}

        <ul>
          {data?.results.map((e) => (
            <li key={e.entity_id}>
              <Link href={`/entities/${e.entity_id}`}>{e.name}</Link> — {e.category_slug}
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}

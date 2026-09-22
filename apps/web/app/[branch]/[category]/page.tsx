import Link from "next/link";

import { apiGet, type CategorySchema, type EntitySummary } from "../../../lib/api";

interface SearchResponse {
  total: number;
  results: EntitySummary[];
  facets: Record<string, unknown>;
}

// S-10: branch/category landing page. Breadcrumb + facet-ready shell; the
// facet *values* come from search_config (S-04) so a schema change alone
// (no code, no deploy) changes what filters show here (K7).
export default async function CategoryPage({
  params,
}: {
  params: { branch: string; category: string };
}) {
  const { branch, category } = params;

  const [schema, results] = await Promise.all([
    apiGet<CategorySchema>(`/api/v1/schemas/${category}/latest`),
    apiGet<SearchResponse>(`/api/v1/search?branch_slug=${branch}&category_slug=${category}`),
  ]);

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: 24 }}>
      <nav aria-label="breadcrumb">
        <Link href="/">Нүүр</Link> / <Link href={`/${branch}`}>{branch}</Link> / {category}
      </nav>

      <h1>{category}</h1>

      {schema?.search_config.facets && (
        <aside>
          <h2>Шүүлтүүр</h2>
          <ul>
            {schema.search_config.facets
              .sort((a, b) => a.order - b.order)
              .map((f) => (
                <li key={f.field}>
                  {f.label_mn} ({f.type})
                </li>
              ))}
          </ul>
        </aside>
      )}

      <section>
        <h2>Жагсаалт ({results?.total ?? 0})</h2>
        <ul>
          {(results?.results ?? []).map((e) => (
            <li key={e.entity_id}>
              <Link href={`/entities/${e.entity_id}`}>{e.name}</Link>
            </li>
          ))}
        </ul>
        {results && results.total === 0 && <p>Илэрц олдсонгүй.</p>}
      </section>
    </main>
  );
}

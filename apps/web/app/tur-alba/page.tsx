import Link from "next/link";

import { apiGet } from "../../lib/api";

interface PoliticianRow {
  id: string;
  name: string;
  tovrog_slug: string | null;
  party: string | null;
}

/**
 * S-18: constituency-based browsing for political entities, ordered
 * тойрог -> нэр (never by score — see app/api/v1/political_search.py for why
 * that's enforced server-side, not just a frontend default).
 *
 * This is a grouped-list view, not a choropleth map — a real map needs
 * constituency GeoJSON polygons, which aren't sourced yet (see
 * docs/PROGRESS.md). The list is grouped by тойрог so "100% тойрог ... хүрэгдэх"
 * (every constituency reachable) holds today; swapping in an actual map
 * component later doesn't change the API contract this page already uses.
 */
export default async function PoliticalSearchPage() {
  const rows = await apiGet<PoliticianRow[]>("/api/v1/political/by-district");
  const byDistrict = new Map<string, PoliticianRow[]>();
  for (const row of rows ?? []) {
    const key = row.tovrog_slug ?? "тодорхойгүй";
    if (!byDistrict.has(key)) byDistrict.set(key, []);
    byDistrict.get(key)!.push(row);
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>Төрийн алба — тойргоор</h1>
      {[...byDistrict.entries()].map(([tovrog, politicians]) => (
        <section key={tovrog}>
          <h2>{tovrog}</h2>
          <ul>
            {politicians.map((p) => (
              <li key={p.id}>
                <Link href={`/entities/${p.id}`}>{p.name}</Link>
                {p.party && ` — ${p.party}`}
              </li>
            ))}
          </ul>
        </section>
      ))}
      {(rows ?? []).length === 0 && <p>Одоогоор бүртгэлтэй байхгүй.</p>}
    </main>
  );
}

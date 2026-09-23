import Link from "next/link";

import { apiGet, type CategorySchema, type EntityDetail } from "../../../lib/api";

// P1-10 / S-11: uniform entity page — every category renders the *same*
// section order (SOW §5.2: нэр → badge → оноо → шалгуур → үнэлгээ → мэдээлэл
// → газрын зураг → эзэмшигчийн хариу), driven entirely by display_config so
// this file never branches on category_slug.
const SECTION_LABELS: Record<string, string> = {
  summary: "Товч мэдээлэл",
  criteria_breakdown: "Шалгуур бүрийн оноо",
  reviews: "Үнэлгээнүүд",
  attributes: "Мэдээлэл",
  map: "Газрын зураг",
  owner_reply: "Эзэмшигчийн хариу",
};

export default async function EntityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const entity = await apiGet<EntityDetail>(`/api/v1/entities/${id}`);
  if (!entity) {
    return <main style={{ padding: 24 }}>Олдсонгүй.</main>;
  }

  const schema = await apiGet<CategorySchema>(`/api/v1/schemas/${entity.category_slug}/latest`);
  const sections = schema?.display_config.sections ?? ["summary", "reviews"];

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <nav aria-label="breadcrumb">
        <Link href="/">Нүүр</Link> /{" "}
        <Link href={`/${entity.branch_slug}/${entity.category_slug}`}>{entity.category_slug}</Link>{" "}
        / {entity.name}
      </nav>

      <h1>
        {entity.name} {entity.verified && <span title="Баталгаажсан">✅</span>}
      </h1>

      {sections.map((section) => (
        <section key={section}>
          <h2>{SECTION_LABELS[section] ?? section}</h2>
          {section === "attributes" && (
            <dl>
              {Object.entries(entity.attributes).map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{String(v)}</dd>
                </div>
              ))}
            </dl>
          )}
          {section === "reviews" && (
            <p>
              <Link href={`/entities/${entity.id}/review`}>+ Үнэлгээ бичих</Link>
            </p>
          )}
        </section>
      ))}
    </main>
  );
}

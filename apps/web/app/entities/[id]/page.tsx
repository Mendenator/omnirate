import Link from "next/link";

import {
  apiGet,
  type CategorySchema,
  type EntityDetail,
  type ReviewListItem,
} from "../../../lib/api";

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

const POE_LABELS: Record<string, string> = {
  L0: "Баталгаажаагүй",
  L1: "Утас баталгаажсан",
  L2: "GPS-ээр баталгаажсан",
  L3: "Баримтаар баталгаажсан",
  L4: "э-баримтаар баталгаажсан",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("mn-MN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default async function EntityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const entity = await apiGet<EntityDetail>(`/api/v1/entities/${id}`);
  if (!entity) {
    return <main style={{ padding: 24 }}>Олдсонгүй.</main>;
  }

  const [schema, reviews] = await Promise.all([
    apiGet<CategorySchema>(`/api/v1/schemas/${entity.category_slug}/latest`),
    apiGet<ReviewListItem[]>(`/api/v1/entities/${id}/reviews`),
  ]);
  const sections = schema?.display_config.sections ?? ["summary", "reviews"];
  const reviewList = reviews ?? [];
  const ownerReplies = reviewList.filter((r) => r.owner_reply_body);

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

          {section === "summary" && (
            <p>
              <strong>{entity.score.toFixed(1)} / 5</strong> — {entity.review_count} үнэлгээ
              {entity.review_count > 0 && ` (${entity.verified_review_count} баталгаажсан)`}
            </p>
          )}

          {section === "criteria_breakdown" &&
            (Object.keys(entity.criteria_breakdown).length > 0 ? (
              <ul>
                {Object.entries(entity.criteria_breakdown).map(([key, value]) => (
                  <li key={key}>
                    {key}: {value.toFixed(1)} / 5
                  </li>
                ))}
              </ul>
            ) : (
              <p>Шалгуур тус бүрийн оноо одоогоор алга.</p>
            ))}

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

          {section === "map" &&
            (entity.lat != null && entity.lon != null ? (
              <p>
                <a
                  href={`https://www.openstreetmap.org/?mlat=${entity.lat}&mlon=${entity.lon}#map=17/${entity.lat}/${entity.lon}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Газрын зураг дээр харах ({entity.lat}, {entity.lon})
                </a>
              </p>
            ) : (
              <p>Байршлын мэдээлэл алга.</p>
            ))}

          {section === "owner_reply" &&
            (ownerReplies.length > 0 ? (
              <ul>
                {ownerReplies.map((r) => (
                  <li key={r.id}>
                    {r.owner_reply_body}
                    {r.owner_reply_at && <> — {formatDate(r.owner_reply_at)}</>}
                  </li>
                ))}
              </ul>
            ) : (
              <p>Эзэмшигч хараахан хариу өгөөгүй байна.</p>
            ))}

          {section === "reviews" && (
            <>
              <p>
                <Link href={`/entities/${entity.id}/review`}>+ Үнэлгээ бичих</Link>
              </p>
              {reviewList.length === 0 ? (
                <p>Одоогоор үнэлгээ алга. Эхнийх нь болоорой!</p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0 }}>
                  {reviewList.map((r) => (
                    <li key={r.id} style={{ borderTop: "1px solid #ddd", padding: "12px 0" }}>
                      <p>
                        <strong>{r.overall_score.toFixed(1)} / 5</strong> —{" "}
                        {POE_LABELS[r.poe_level] ?? r.poe_level} — {formatDate(r.created_at)}
                      </p>
                      {r.body && <p>{r.body}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </section>
      ))}
    </main>
  );
}

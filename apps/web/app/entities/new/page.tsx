import Link from "next/link";

import { apiGet, type CategorySchema, type CategorySummary } from "../../../lib/api";
import NewEntityForm from "./NewEntityForm";

export default async function NewEntityPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; branch?: string }>;
}) {
  const { category, branch } = await searchParams;
  const categories = (await apiGet<CategorySummary[]>("/api/v1/schemas")) ?? [];

  const initial = categories.find((c) => c.category_slug === category);
  const initialSchema = initial
    ? await apiGet<CategorySchema>(`/api/v1/schemas/${initial.category_slug}/latest`)
    : null;

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>Шинэ газар нэмэх</h1>
      {categories.length === 0 ? (
        <p>
          Одоогоор категори алга. Эхлээд <Link href="/admin/schemas">категори үүсгэнэ үү</Link>.
        </p>
      ) : (
        <NewEntityForm
          categories={categories}
          initialSchema={initialSchema}
          initialBranch={branch ?? ""}
        />
      )}
    </main>
  );
}

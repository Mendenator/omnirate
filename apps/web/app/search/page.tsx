import SearchClient from "./SearchClient";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string }>;
}) {
  const { q, category } = await searchParams;
  return <SearchClient initialQuery={q ?? ""} initialCategory={category ?? null} />;
}

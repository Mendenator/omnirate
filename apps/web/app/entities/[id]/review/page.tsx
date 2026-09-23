import ReviewForm from "./ReviewForm";

export default async function ReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>Үнэлгээ бичих</h1>
      <ReviewForm entityId={id} />
    </main>
  );
}

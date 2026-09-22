import ReviewForm from "./ReviewForm";

export default function ReviewPage({ params }: { params: { id: string } }) {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>Үнэлгээ бичих</h1>
      <ReviewForm entityId={params.id} />
    </main>
  );
}

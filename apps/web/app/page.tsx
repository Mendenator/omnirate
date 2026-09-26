import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>OmniRate</h1>
      <p>
        Салбарын нүүр хуудсууд (S-10), хайлтын үр дүн (S-09) энд P1 үе шатанд нэмэгдэнэ. Одоогоор
        зөвхөн <Link href="/admin/schemas">/admin/schemas</Link> (P0-09/P0-10) ажиллаж байна.
      </p>
      <p>
        <Link href="/login">Нэвтрэх</Link>
      </p>
    </main>
  );
}

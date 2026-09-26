import { safeNextPath } from "../../lib/auth";
import LoginForm from "./LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  return (
    <main style={{ maxWidth: 420, margin: "0 auto", padding: 24 }}>
      <h1>Нэвтрэх</h1>
      <LoginForm next={safeNextPath(next)} />
    </main>
  );
}

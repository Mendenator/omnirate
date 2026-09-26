"use client";

import { useRouter } from "next/navigation";
import { useState, useSyncExternalStore, type FormEvent } from "react";

import { clearToken, getToken, setToken, subscribeToken } from "../../lib/auth";

// L1 login (SOW §7 fallback): phone + OTP against POST /api/v1/auth/otp/verify.
// The backend does not send or verify SMS codes yet (see app/api/v1/auth.py),
// so this page is only as trustworthy as that endpoint.
export default function LoginForm({ next }: { next: string }) {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const loggedIn = useSyncExternalStore(
    subscribeToken,
    () => getToken() !== null,
    () => false,
  );

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setStatus(null);
    try {
      const res = await fetch("/api/backend/v1/auth/otp/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: phone.trim(), otp_code: otp.trim() }),
      });
      if (!res.ok) {
        setStatus(`❌ Нэвтэрч чадсангүй (${res.status})`);
        return;
      }
      const body: { access_token: string } = await res.json();
      setToken(body.access_token);
      router.push(next);
    } catch {
      setStatus("❌ Сервертэй холбогдож чадсангүй");
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    clearToken();
    setStatus("Гарлаа.");
  }

  return (
    <>
      {loggedIn && (
        <p>
          Та нэвтэрсэн байна. <button onClick={logout}>Гарах</button>
        </p>
      )}
      <form onSubmit={submit}>
        <p>
          <label htmlFor="phone">Утасны дугаар</label>
          <br />
          <input
            id="phone"
            type="tel"
            inputMode="numeric"
            autoComplete="tel"
            required
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </p>
        <p>
          <label htmlFor="otp">Баталгаажуулах код</label>
          <br />
          <input
            id="otp"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
          />
        </p>
        <button type="submit" disabled={busy}>
          {busy ? "Илгээж байна..." : "Нэвтрэх"}
        </button>
      </form>
      {status && <p role="status">{status}</p>}
    </>
  );
}

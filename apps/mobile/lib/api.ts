import { getToken } from "./tokenStorage";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

async function authHeader(): Promise<Record<string, string>> {
  const token = await getToken("omnirate_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function submitReview(entityId: string, overallScore: number, body: string) {
  const idempotencyKey = crypto.randomUUID();
  const res = await fetch(`${API_BASE_URL}/api/v1/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey, ...(await authHeader()) },
    body: JSON.stringify({ entity_id: entityId, overall_score: overallScore, body }),
  });
  if (!res.ok) throw new Error(`Review submit failed: ${res.status}`);
  return (await res.json()) as { id: string };
}

export async function attachEBarimtEvidence(reviewId: string, qrPayload: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/reviews/${reviewId}/evidence/e-barimt`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
    body: JSON.stringify({ qr_payload: qrPayload }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message ?? `e-barimt verify failed: ${res.status}`);
  }
  return (await res.json()) as { poe_level: string; ddtd: string };
}

export async function verifyOtp(phone: string, otpCode: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/otp/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp_code: otpCode }),
  });
  if (!res.ok) throw new Error(`OTP verify failed: ${res.status}`);
  return (await res.json()) as { access_token: string; poe_level: string };
}

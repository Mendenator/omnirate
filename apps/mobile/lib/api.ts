import { getToken } from "./tokenStorage";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export interface CategorySummary {
  category_slug: string;
  version: number;
}

export interface CategorySchema {
  category_slug: string;
  version: number;
  json_schema: { properties?: Record<string, { type?: string; title?: string }> };
}

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

export async function listCategories(): Promise<CategorySummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schemas`);
  if (!res.ok) throw new Error(`Category list failed: ${res.status}`);
  return (await res.json()) as CategorySummary[];
}

export async function getCategorySchema(slug: string): Promise<CategorySchema> {
  const res = await fetch(`${API_BASE_URL}/api/v1/schemas/${slug}/latest`);
  if (!res.ok) throw new Error(`Category schema load failed: ${res.status}`);
  return (await res.json()) as CategorySchema;
}

export interface NewEntityInput {
  categorySlug: string;
  schemaVersion: number;
  name: string;
  branchSlug: string;
  locationSlug?: string;
  lat?: number;
  lon?: number;
  attributes: Record<string, unknown>;
}

// 401 is handled by the caller (AuthScreen redirect), not thrown as an Error
// here, since it needs a different response than every other failure.
export async function createEntity(input: NewEntityInput): Promise<{ id: string } | { unauthorized: true }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/entities`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
    body: JSON.stringify({
      category_slug: input.categorySlug,
      schema_version: input.schemaVersion,
      name: input.name,
      branch_slug: input.branchSlug,
      location_slug: input.locationSlug || undefined,
      lat: input.lat,
      lon: input.lon,
      attributes: input.attributes,
    }),
  });
  if (res.status === 401) return { unauthorized: true };
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Entity create failed: ${res.status}`);
  }
  return (await res.json()) as { id: string };
}

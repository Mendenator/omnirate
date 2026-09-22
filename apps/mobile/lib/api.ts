const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export async function verifyOtp(phone: string, otpCode: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/otp/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp_code: otpCode }),
  });
  if (!res.ok) throw new Error(`OTP verify failed: ${res.status}`);
  return (await res.json()) as { access_token: string; poe_level: string };
}

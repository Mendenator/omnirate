"use client";

import { useState } from "react";

// P1-11: review submission, target <=4 steps (score -> criteria -> text ->
// optional e-barimt evidence). Idempotency-Key is client-generated once per
// form mount so a double-tap on submit can't create two reviews.
const IDEMPOTENCY_KEY = crypto.randomUUID();

export default function ReviewForm({ entityId }: { entityId: string }) {
  const [step, setStep] = useState(1);
  const [overallScore, setOverallScore] = useState(5);
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  async function submit() {
    setStatus("Илгээж байна...");
    const res = await fetch("/api/backend/v1/reviews", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": IDEMPOTENCY_KEY,
        Authorization: `Bearer ${localStorage.getItem("omnirate_access_token") ?? ""}`,
      },
      body: JSON.stringify({ entity_id: entityId, overall_score: overallScore, body }),
    });
    setStatus(res.ok ? "✅ Үнэлгээ илгээгдлээ. Дараагийн алхам: e-barimt баримт хавсаргах." : `❌ Алдаа (${res.status})`);
    if (res.ok) setStep(4);
  }

  return (
    <div style={{ maxWidth: 480 }}>
      {step === 1 && (
        <>
          <h2>1. Ерөнхий оноо</h2>
          <input type="range" min={0} max={5} step={0.5} value={overallScore} onChange={(e) => setOverallScore(Number(e.target.value))} />
          <span> {overallScore} / 5</span>
          <div>
            <button onClick={() => setStep(2)}>Дараах</button>
          </div>
        </>
      )}
      {step === 2 && (
        <>
          <h2>2. Тайлбар (заавал биш)</h2>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} maxLength={4000} rows={5} />
          <div>
            <button onClick={() => setStep(3)}>Дараах</button>
          </div>
        </>
      )}
      {step === 3 && (
        <>
          <h2>3. Баталгаажуулах</h2>
          <p>Оноо: {overallScore} / 5</p>
          <button onClick={submit}>Илгээх</button>
        </>
      )}
      {step === 4 && <p>4. e-barimt QR баримт хавсаргах (P1-01 evidence endpoint) — удахгүй.</p>}
      {status && <p>{status}</p>}
    </div>
  );
}

"use client";

import { useState } from "react";

/**
 * P2-06: shown when a review is rejected by moderation (P2-05's LLM/heuristic
 * pipeline) with a suggested rewrite. Acceptance is tracked via an analytics
 * event (SOW: "Санал хүлээн авсан хувийг хэмжих event") so P2's moderation
 * tuning can see how often a suggestion actually gets used vs. discarded.
 */

interface Props {
  originalText: string;
  suggestedText: string;
  onAccept: (finalText: string) => void;
}

function trackRewriteEvent(action: "accepted" | "edited" | "dismissed") {
  // Real implementation posts to the analytics pipeline that feeds
  // infra/observability's Grafana dashboards. Kept as a single call site so
  // swapping the sink (segment/plausible/custom) touches one line.
  fetch("/api/backend/v1/analytics/rewrite-suggestion", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, at: new Date().toISOString() }),
  }).catch(() => {
    /* analytics failures must never block the user's flow */
  });
}

export default function RewriteSuggestion({ originalText, suggestedText, onAccept }: Props) {
  const [editedText, setEditedText] = useState(suggestedText);
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div style={{ border: "1px solid #e0a800", borderRadius: 4, padding: 12, marginTop: 12 }}>
      <p>
        Таны сэтгэгдэл зохицуулалтын шалгуурт таарахгүй байна. Дараах засмал хувилбарыг санал болгож
        байна:
      </p>
      <p style={{ color: "#888" }}>
        <s>{originalText}</s>
      </p>
      <textarea
        value={editedText}
        onChange={(e) => setEditedText(e.target.value)}
        rows={4}
        style={{ width: "100%" }}
      />
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <button
          onClick={() => {
            trackRewriteEvent(editedText === suggestedText ? "accepted" : "edited");
            onAccept(editedText);
          }}
        >
          Энэ хувилбараар илгээх
        </button>
        <button
          onClick={() => {
            trackRewriteEvent("dismissed");
            setDismissed(true);
          }}
        >
          Цуцлах
        </button>
      </div>
    </div>
  );
}

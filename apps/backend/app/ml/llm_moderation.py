"""LLM moderation worker (P2-05): prompt + JSON-schema-validated output +
fallback + cost control.

SOW §7 risk mitigation, implemented directly rather than left as prose:
"LLM зардал төсвөөс хэтрэх" -> "Classifier босгыг 0.93 болгож LLM урсгалыг
<=30% болгох." Concretely:
  - heuristic score >=0.93  -> confident reject, no LLM call needed
  - heuristic score <0.15   -> confident approve, no LLM call needed
  - otherwise (borderline)  -> route to the LLM, but only ~30% of the time
    (deterministic sampling on review_id so results are reproducible in tests
    and don't depend on wall-clock randomness)
"""

import hashlib
import json
from dataclasses import dataclass

import httpx
import jsonschema

from app.core.config import get_settings
from app.ml.classifier import ToxicityResult, classify_toxicity

CONFIDENT_REJECT_THRESHOLD = 0.93
CONFIDENT_APPROVE_THRESHOLD = 0.15
LLM_SAMPLING_RATE = 0.30

_LLM_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["verdict", "reason", "confidence"],
    "properties": {
        "verdict": {"enum": ["approve", "reject", "needs_human_review"]},
        "reason": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}

MODERATION_PROMPT_TEMPLATE = """Та Монгол хэл дээрх бүтээгдэхүүний үнэлгээг зохицуулагч (moderator) юм. \
Доорх текстийг уншаад зөвхөн энэ JSON бүтцээр хариул:
{{"verdict": "approve" | "reject" | "needs_human_review", "reason": "...", "confidence": 0.0-1.0}}

Текст: {text}"""


@dataclass(frozen=True)
class LlmModerationResult:
    verdict: str
    reason: str
    confidence: float
    cost_usd: float
    source: str  # "llm" | "heuristic_fallback" | "heuristic_confident"


def should_route_to_llm(review_id: str, heuristic: ToxicityResult) -> bool:
    if heuristic.toxicity_score >= CONFIDENT_REJECT_THRESHOLD:
        return False
    if heuristic.toxicity_score < CONFIDENT_APPROVE_THRESHOLD:
        return False
    # Deterministic hash-based sampling: stable per review_id (same review
    # always samples the same way), uniformly distributed across [0, 1).
    digest = hashlib.sha256(review_id.encode()).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    return bucket < LLM_SAMPLING_RATE


async def _call_llm(text: str) -> tuple[dict, float]:
    """Real implementation POSTs to the configured LLM endpoint with
    MODERATION_PROMPT_TEMPLATE and JSON-mode enabled; returns (parsed_json,
    cost_usd) computed from the provider's token usage in the response.
    Left as an explicit stub (see app/ml/ocr.py for the same pattern) — no
    LLM API key is configured in this environment.
    """
    settings = get_settings()
    if not settings.llm_moderation_api_url:
        raise NotImplementedError("LLM moderation endpoint not configured — see docs/PROGRESS.md P2-05")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            settings.llm_moderation_api_url,
            json={"prompt": MODERATION_PROMPT_TEMPLATE.format(text=text)},
        )
        resp.raise_for_status()
        body = resp.json()
        return body["result"], float(body["cost_usd"])


async def moderate_with_llm_or_fallback(*, review_id: str, text: str) -> LlmModerationResult:
    heuristic = classify_toxicity(text)

    if heuristic.toxicity_score >= CONFIDENT_REJECT_THRESHOLD:
        return LlmModerationResult(
            verdict="reject",
            reason="heuristic confident reject",
            confidence=heuristic.toxicity_score,
            cost_usd=0.0,
            source="heuristic_confident",
        )
    if heuristic.toxicity_score < CONFIDENT_APPROVE_THRESHOLD:
        return LlmModerationResult(
            verdict="approve",
            reason="heuristic confident approve",
            confidence=1 - heuristic.toxicity_score,
            cost_usd=0.0,
            source="heuristic_confident",
        )

    if not should_route_to_llm(review_id, heuristic):
        # Borderline but not sampled into the LLM path -> defer to a human
        # (P2-12's moderator queue), never auto-approve/reject an unclear case.
        return LlmModerationResult(
            verdict="needs_human_review",
            reason="borderline, not LLM-sampled",
            confidence=heuristic.toxicity_score,
            cost_usd=0.0,
            source="heuristic_fallback",
        )

    try:
        raw, cost_usd = await _call_llm(text)
        jsonschema.validate(raw, _LLM_RESPONSE_SCHEMA)
        return LlmModerationResult(
            verdict=raw["verdict"], reason=raw["reason"], confidence=raw["confidence"], cost_usd=cost_usd, source="llm"
        )
    except (NotImplementedError, httpx.HTTPError, jsonschema.ValidationError, json.JSONDecodeError):
        return LlmModerationResult(
            verdict="needs_human_review",
            reason="LLM call failed, deferring to human",
            confidence=heuristic.toxicity_score,
            cost_usd=0.0,
            source="heuristic_fallback",
        )

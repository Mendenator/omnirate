"""Toxicity/moderation classifier — stage 2 of the moderation pipeline
(P1-08), running after PII redaction (app/domain/moderation.py, stage 1).

⛔ The real XLM-R fine-tune needs the labeled dataset from P0-12 (external,
see docs/PROGRESS.md) — target F1 >=0.88 can't be claimed without it. This
module defines the inference interface every caller (moderation worker,
P2-05's LLM fallback) codes against, backed today by a keyword-heuristic
placeholder so the pipeline runs end-to-end before the trained model exists.
Swapping `_classify_heuristic` for a real `transformers` pipeline call is the
only change needed once the model is trained.
"""

from dataclasses import dataclass

# Deliberately short and coarse — a real classifier replaces this entirely;
# it exists only so the pipeline has *something* to call before P0-12 lands.
_TOXIC_KEYWORDS = {"новш", "новшнууд", "новшрах"}

TOXICITY_THRESHOLD = 0.5


@dataclass(frozen=True)
class ToxicityResult:
    toxicity_score: float
    is_toxic: bool
    model: str  # "heuristic-v0" until the fine-tuned model replaces it


def _classify_heuristic(text: str) -> float:
    lowered = text.lower()
    hits = sum(1 for kw in _TOXIC_KEYWORDS if kw in lowered)
    return min(1.0, hits * 0.6)


def classify_toxicity(text: str) -> ToxicityResult:
    score = _classify_heuristic(text)
    return ToxicityResult(toxicity_score=score, is_toxic=score >= TOXICITY_THRESHOLD, model="heuristic-v0")

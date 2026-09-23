from app.ml.classifier import ToxicityResult
from app.ml.llm_moderation import moderate_with_llm_or_fallback, should_route_to_llm


def test_confident_reject_never_routes_to_llm():
    high = ToxicityResult(toxicity_score=0.95, is_toxic=True, model="heuristic-v0")
    assert should_route_to_llm("review-1", high) is False


def test_confident_approve_never_routes_to_llm():
    low = ToxicityResult(toxicity_score=0.05, is_toxic=False, model="heuristic-v0")
    assert should_route_to_llm("review-1", low) is False


def test_sampling_rate_is_roughly_30_percent_over_many_ids():
    borderline = ToxicityResult(toxicity_score=0.5, is_toxic=False, model="heuristic-v0")
    sampled = sum(1 for i in range(2000) if should_route_to_llm(f"review-{i}", borderline))
    ratio = sampled / 2000
    assert 0.24 < ratio < 0.36  # 30% +/- tolerance for hash distribution noise


def test_sampling_is_deterministic_per_review_id():
    borderline = ToxicityResult(toxicity_score=0.5, is_toxic=False, model="heuristic-v0")
    first = should_route_to_llm("stable-id", borderline)
    second = should_route_to_llm("stable-id", borderline)
    assert first == second


async def test_confident_reject_short_circuits_without_llm_call():
    # classify_toxicity counts *distinct* matched keyword families present in
    # the text (existence, not occurrence count) — repeating one word doesn't
    # raise the score, so this needs two distinct family matches to clear the
    # 0.93 confident-reject threshold ("новш" and "новшнууд" both match here).
    result = await moderate_with_llm_or_fallback(review_id="r1", text="чи новшнууд хүн байна")
    assert result.source == "heuristic_confident"
    assert result.cost_usd == 0.0


async def test_clean_text_short_circuits_to_approve():
    result = await moderate_with_llm_or_fallback(review_id="r2", text="Маш сайн үйлчилгээ байсан")
    assert result.verdict == "approve"
    assert result.source == "heuristic_confident"


async def test_borderline_text_always_defers_to_human_when_llm_unconfigured():
    # "новш" (one keyword hit) scores 0.6 on the heuristic -> borderline
    # (between the confident-approve and confident-reject thresholds).
    # Whether or not this review_id happens to sample into the LLM path,
    # the outcome converges to needs_human_review because no LLM endpoint
    # is configured in this environment (app/core/config.py default None).
    result = await moderate_with_llm_or_fallback(review_id="borderline-1", text="энэ чинь новш байна")
    assert result.verdict == "needs_human_review"
    assert result.cost_usd == 0.0

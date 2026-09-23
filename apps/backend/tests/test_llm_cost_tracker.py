import fakeredis

from app.ml.llm_cost_tracker import get_month_to_date_cost, is_over_budget, record_llm_cost


async def test_month_to_date_cost_starts_at_zero():
    redis = fakeredis.FakeAsyncRedis()
    assert await get_month_to_date_cost(redis) == 0.0


async def test_record_llm_cost_accumulates():
    redis = fakeredis.FakeAsyncRedis()
    await record_llm_cost(redis, 1.50)
    total = await record_llm_cost(redis, 2.25)
    assert total == 3.75
    assert await get_month_to_date_cost(redis) == 3.75


async def test_is_over_budget_false_when_under(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("OMNIRATE_LLM_MONTHLY_BUDGET_USD", "500")
    get_settings.cache_clear()
    redis = fakeredis.FakeAsyncRedis()
    await record_llm_cost(redis, 10.0)

    assert await is_over_budget(redis) is False
    get_settings.cache_clear()


async def test_is_over_budget_true_when_at_or_above_limit(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("OMNIRATE_LLM_MONTHLY_BUDGET_USD", "5")
    get_settings.cache_clear()
    redis = fakeredis.FakeAsyncRedis()
    await record_llm_cost(redis, 5.0)

    assert await is_over_budget(redis) is True
    get_settings.cache_clear()

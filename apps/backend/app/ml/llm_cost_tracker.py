"""LLM spend guardrail (P2-05 "зардлын хяналт"), separate from the routing
logic in llm_moderation.py so the budget check can wrap *any* LLM call site
(moderation today, future features later) with one Redis-backed counter per
calendar month.
"""

from datetime import UTC, datetime

from redis.asyncio import Redis

from app.core.config import get_settings


def _month_key() -> str:
    return f"llm:cost:{datetime.now(UTC):%Y-%m}"


async def get_month_to_date_cost(redis: Redis) -> float:
    raw = await redis.get(_month_key())
    return float(raw) if raw is not None else 0.0


async def record_llm_cost(redis: Redis, cost_usd: float) -> float:
    key = _month_key()
    new_total: float = await redis.incrbyfloat(key, cost_usd)
    await redis.expire(key, 60 * 60 * 24 * 40)  # outlive the month, cheap to let it roll off
    return new_total


async def is_over_budget(redis: Redis) -> bool:
    settings = get_settings()
    spent = await get_month_to_date_cost(redis)
    return spent >= settings.llm_monthly_budget_usd

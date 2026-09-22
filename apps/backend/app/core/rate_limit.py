"""Gateway rate limiting (P0-08). Fixed-window counter in Redis, 429 on breach.

Acceptance: k6-measured 429 rate at each threshold within ±1%. Fixed-window is
adequate here because the target is a per-route requests/minute ceiling, not
smoothing burst traffic (that's handled separately by the LB).
"""

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

ROUTE_LIMITS_PER_MINUTE: dict[str, int] = {
    "/api/v1/reviews": 30,
    "/api/v1/entities": 120,
    "/api/v1/search": 300,
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reads its Redis client from `request.app.state.redis` (set on startup —
    see app/main.py) rather than capturing one at construction time, so tests
    can swap in a fake client via `app.state.redis` without touching a live
    Redis instance.
    """

    def __init__(self, app):
        super().__init__(app)
        self._settings = get_settings()

    async def dispatch(self, request: Request, call_next) -> Response:
        redis = request.app.state.redis
        limit = ROUTE_LIMITS_PER_MINUTE.get(request.url.path, self._settings.rate_limit_default_per_minute)
        client_key = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
        window = int(time.time() // 60)
        redis_key = f"ratelimit:{client_key}:{request.url.path}:{window}"

        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, 60)

        if count > limit:
            return Response(status_code=429, content="rate limit exceeded")

        return await call_next(request)

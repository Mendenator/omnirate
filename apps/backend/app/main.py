from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.observability import configure_logging, configure_tracing
from app.core.rate_limit import RateLimitMiddleware

configure_logging()
settings = get_settings()

app = FastAPI(title="OmniRate API", version="0.1.0")
app.add_middleware(RateLimitMiddleware)
app.include_router(api_router)

configure_tracing(app)


@app.on_event("startup")
async def _init_redis() -> None:
    # Skipped when a test (or other caller) has already injected a client —
    # see tests/conftest.py, which sets app.state.redis to a fake before the
    # app ever starts handling requests.
    if not hasattr(app.state, "redis"):
        app.state.redis = Redis.from_url(settings.redis_url)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "env": settings.env}

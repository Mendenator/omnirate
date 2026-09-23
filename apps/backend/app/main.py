from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.observability import configure_logging, configure_sentry, configure_tracing
from app.core.rate_limit import RateLimitMiddleware
from app.search.client import ensure_entities_index, get_opensearch_client

configure_logging()
configure_sentry()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skipped when a test (or other caller) has already injected a client —
    # see tests/conftest.py, which sets app.state.redis to a fake before the
    # app ever starts handling requests.
    if not hasattr(app.state, "redis"):
        app.state.redis = Redis.from_url(settings.redis_url)
    if not hasattr(app.state, "arq_pool"):
        app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    if not hasattr(app.state, "opensearch"):
        app.state.opensearch = get_opensearch_client()
        await ensure_entities_index(app.state.opensearch)
    yield


app = FastAPI(title="OmniRate API", version="0.1.0", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)
# apps/mobile (Expo web target) calls this API cross-origin directly, unlike
# apps/web which proxies same-origin through Next.js — without this, every
# request from Expo web fails at the browser's CORS preflight before it ever
# reaches a route (found by actually running the Expo web build against
# this backend, not by inspection).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

configure_tracing(app)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "env": settings.env}

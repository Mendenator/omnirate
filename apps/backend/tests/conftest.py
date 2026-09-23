import uuid

import fakeredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.domain import models  # noqa: F401
from app.domain.models import User
from app.main import app


@pytest_asyncio.fixture
async def engine():
    settings = get_settings()
    eng = create_async_engine(settings.database_url)
    async with eng.begin() as conn:
        # Unit tests exercise ORM constraints (unique/check), not the
        # pg_jsonschema trigger from the migration — that needs the
        # infra/postgres custom image and is covered by the docker-compose
        # integration profile, not plain CI service containers.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
def test_session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(test_session_factory):
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with session_factory() as session:
            yield session

    fake_user = CurrentUser(user_id=uuid.uuid4(), rd_hash="test-rd-hash", poe_level="L2")

    # A live Postgres enforces reviews.user_id / complaints.reporter_id /
    # takedown_requests.requester_id -> users.id — fake_user has to actually
    # exist as a row, not just as the CurrentUser Python object the auth
    # dependency override hands back, or any test that performs a real
    # insert (not just an error-path 4xx) hits a FK violation. Invisible
    # under sqlite-style/no-FK test setups; only surfaced once tests ran
    # against real Postgres for the first time.
    async with session_factory() as seed_session:
        seed_session.add(
            User(
                id=fake_user.user_id, rd_hash=fake_user.rd_hash, display_name="Test User", poe_level=fake_user.poe_level
            )
        )
        await seed_session.commit()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    # Rate-limit middleware reads request.app.state.redis (see app/main.py) —
    # inject an in-memory fake so tests don't need a live Redis instance.
    app.state.redis = fakeredis.FakeAsyncRedis()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.fake_user = fake_user  # convenience for tests that need the id
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
def worker_db(test_session_factory, monkeypatch):
    """Points every arq worker module's module-level `async_session_factory`
    at this test's engine instead of app.db.session's process-global one.

    Worker functions open their own session via `async_session_factory()`
    rather than taking a session as a parameter (they're arq entry points,
    not FastAPI dependencies) — that global engine is created once at import
    time and its pooled connections get bound to whatever event loop was
    running then. pytest-asyncio gives each test function its own event
    loop, so a pooled connection from an earlier test's loop is dead by the
    time a later test's worker call tries to reuse it (intermittent
    'Event loop is closed' / asyncpg protocol errors, not a real app bug).
    Repointing at the per-test engine sidesteps that entirely.
    """
    for module_name in (
        "app.workers.moderation",
        "app.workers.indexer",
        "app.workers.attendance",
        "app.workers.transparency",
    ):
        monkeypatch.setattr(f"{module_name}.async_session_factory", test_session_factory)

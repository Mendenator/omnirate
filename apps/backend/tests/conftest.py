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
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():
        async with session_factory() as session:
            yield session

    fake_user = CurrentUser(user_id=uuid.uuid4(), rd_hash="test-rd-hash", poe_level="L2")

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

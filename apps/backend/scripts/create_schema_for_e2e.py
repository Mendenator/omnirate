#!/usr/bin/env python
"""Create the ORM schema directly, bypassing Alembic.

Alembic's migration 0001 unconditionally does CREATE EXTENSION for postgis
and pg_jsonschema (neither of which app/ actually uses — postgis is
unused, and pg_jsonschema only backs a DB-level trigger, not the ORM
schema itself) — those aren't available on lightweight CI service
images, only the full infra/postgres custom build. tests/conftest.py's
`engine` fixture already uses Base.metadata.create_all() for exactly this
reason; this script is the same approach for contexts (like CI's
web-e2e job) that need a working schema outside of pytest.

Not a substitute for real migration testing — that's what the
docker-compose integration profile (infra/postgres) is for.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.domain import models  # noqa: F401  (registers ORM models onto Base.metadata)


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Schema created.")


if __name__ == "__main__":
    asyncio.run(main())

"""Idempotency-Key support shared by mutating POST endpoints (P0-06)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import IdempotencyKey


async def get_cached_response(db: AsyncSession, *, key: str, route: str) -> tuple[int, dict[str, Any]] | None:
    row = await db.scalar(select(IdempotencyKey).where(IdempotencyKey.key == key, IdempotencyKey.route == route))
    if row is None:
        return None
    return row.response_status, row.response_body


async def store_response(db: AsyncSession, *, key: str, route: str, status: int, body: dict[str, Any]) -> None:
    stmt = insert(IdempotencyKey).values(key=key, route=route, response_status=status, response_body=body)
    stmt = stmt.on_conflict_do_nothing(index_elements=["key", "route"])
    await db.execute(stmt)
    await db.commit()

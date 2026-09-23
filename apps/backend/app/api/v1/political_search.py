"""Political-entity browsing (S-18): тойрог -> нэр, never by score. A scored
default ranking for elected officials is the exact thing the SOW's neutral-
default requirement (§5.4: "Төрийн албан тушаалтны хайлтын анхдагч эрэмбэ:
тойрог → нэр... оноогоор эрэмбэлэх нь зөвхөн хэрэглэгч сонговол") rules out,
so this endpoint hardcodes the ORDER BY rather than routing through
app/search/ranking.py at all — there's no ranking formula to misconfigure if
the code path never calls one.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.models import Entity

router = APIRouter(prefix="/api/v1/political", tags=["political-search"])

POLITICAL_BRANCH = "tur-alba"


@router.get("/by-district")
async def list_by_district(tovrog_slug: str | None = None, db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    query = select(Entity).where(Entity.branch_slug == POLITICAL_BRANCH)
    if tovrog_slug:
        query = query.where(Entity.attributes["tovrog_slug"].astext == tovrog_slug)

    entities = (await db.execute(query)).scalars().all()
    # Sort in Python on the JSONB attribute + name — neutral, deterministic,
    # and independent of whatever indexes exist (this endpoint is low-QPS,
    # civic-browsing traffic, not the high-RPS search path).
    ordered = sorted(entities, key=lambda e: (e.attributes.get("tovrog_slug") or "", e.name))

    return [
        {
            "id": str(e.id),
            "name": e.name,
            "tovrog_slug": e.attributes.get("tovrog_slug"),
            "party": e.attributes.get("party"),
        }
        for e in ordered
    ]

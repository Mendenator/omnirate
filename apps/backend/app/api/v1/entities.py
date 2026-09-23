from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import EntityCreateRequest, EntityResponse
from app.db.session import get_db
from app.domain.models import Entity

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(req: EntityCreateRequest, db: AsyncSession = Depends(get_db)) -> Entity:
    entity = Entity(**req.model_dump())
    db.add(entity)
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=422, detail=f"entity rejected: {exc}") from exc
    await db.refresh(entity)
    return entity


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str, db: AsyncSession = Depends(get_db)) -> Entity:
    entity = await db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")
    return entity

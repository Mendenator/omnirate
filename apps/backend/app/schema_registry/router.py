from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.models import SchemaRegistryEntry
from app.schema_registry.models import CategorySchemaPublishRequest, CategorySchemaResponse, CategorySummary
from app.schema_registry.service import get_latest_schema, list_categories, publish_category_schema

router = APIRouter(prefix="/api/v1/schemas", tags=["schema-registry"])


@router.post("", response_model=CategorySchemaResponse, status_code=201)
async def publish(req: CategorySchemaPublishRequest, db: AsyncSession = Depends(get_db)) -> SchemaRegistryEntry:
    return await publish_category_schema(db, req)


@router.get("", response_model=list[CategorySummary])
async def list_all(db: AsyncSession = Depends(get_db)) -> list[CategorySummary]:
    return [CategorySummary(category_slug=slug, version=version) for slug, version in await list_categories(db)]


@router.get("/{category_slug}/latest", response_model=CategorySchemaResponse)
async def latest(category_slug: str, db: AsyncSession = Depends(get_db)) -> SchemaRegistryEntry:
    entry = await get_latest_schema(db, category_slug)
    if entry is None:
        raise HTTPException(status_code=404, detail="category not found")
    return entry

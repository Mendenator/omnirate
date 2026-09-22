"""Schema registry: publish / version / validate (P0-05), with search+display
config validation (S-04).

Acceptance:
- Publishing a version that already exists -> 409 (immutability).
- An invalid JSON Schema (or invalid search/display block) -> rejected before write.
"""

import jsonschema
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import SchemaRegistryEntry
from app.schema_registry.models import CategorySchemaPublishRequest

_SEARCH_CONFIG_META_SCHEMA = {
    "type": "object",
    "properties": {
        "facets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["field", "type", "label_mn", "order"],
                "properties": {
                    "field": {"type": "string"},
                    "type": {"enum": ["multi", "range", "bool"]},
                    "label_mn": {"type": "string"},
                    "order": {"type": "integer"},
                },
            },
        },
        "synonyms": {"type": "array", "items": {"type": "string"}},
        "default_sort": {"type": "string"},
    },
}

_DISPLAY_CONFIG_META_SCHEMA = {
    "type": "object",
    "required": ["sections"],
    "properties": {"sections": {"type": "array", "items": {"type": "string"}}},
}


def _validate_json_schema_itself(schema: dict) -> None:
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        raise HTTPException(status_code=422, detail=f"invalid json_schema: {exc.message}") from exc


def _validate_config_block(name: str, value: dict, meta_schema: dict) -> None:
    try:
        jsonschema.validate(value, meta_schema)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"invalid {name}: {exc.message}") from exc


async def publish_category_schema(
    db: AsyncSession, req: CategorySchemaPublishRequest
) -> SchemaRegistryEntry:
    _validate_json_schema_itself(req.json_schema)
    _validate_config_block("search_config", req.search_config, _SEARCH_CONFIG_META_SCHEMA)
    _validate_config_block("display_config", req.display_config, _DISPLAY_CONFIG_META_SCHEMA)

    existing = await db.scalar(
        select(SchemaRegistryEntry).where(
            SchemaRegistryEntry.category_slug == req.category_slug,
            SchemaRegistryEntry.version == req.version,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"category '{req.category_slug}' version {req.version} already published (immutable)",
        )

    entry = SchemaRegistryEntry(
        category_slug=req.category_slug,
        version=req.version,
        json_schema=req.json_schema,
        search_config=req.search_config,
        display_config=req.display_config,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_latest_schema(db: AsyncSession, category_slug: str) -> SchemaRegistryEntry | None:
    return await db.scalar(
        select(SchemaRegistryEntry)
        .where(SchemaRegistryEntry.category_slug == category_slug)
        .order_by(SchemaRegistryEntry.version.desc())
        .limit(1)
    )

from typing import Any

from pydantic import BaseModel, Field


class CategorySchemaPublishRequest(BaseModel):
    category_slug: str = Field(examples=["restoran"])
    version: int = Field(ge=1)
    json_schema: dict[str, Any]
    search_config: dict[str, Any] = Field(default_factory=dict)
    display_config: dict[str, Any] = Field(default_factory=dict)


class CategorySchemaResponse(BaseModel):
    category_slug: str
    version: int
    json_schema: dict[str, Any]
    search_config: dict[str, Any]
    display_config: dict[str, Any]

    model_config = {"from_attributes": True}

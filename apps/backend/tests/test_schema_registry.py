RESTORAN_SCHEMA = {
    "type": "object",
    "properties": {
        "cuisine": {"type": "string"},
        "price_band": {"type": "integer", "minimum": 1, "maximum": 4},
    },
}


async def _publish(client, version=1, json_schema=None, search_config=None, display_config=None):
    return await client.post(
        "/api/v1/schemas",
        json={
            "category_slug": "restoran",
            "version": version,
            "json_schema": json_schema if json_schema is not None else RESTORAN_SCHEMA,
            "search_config": search_config
            if search_config is not None
            else {
                "facets": [
                    {"field": "cuisine", "type": "multi", "label_mn": "Хоолны төрөл", "order": 1}
                ],
                "synonyms": ["ресторан, зоогийн газар"],
                "default_sort": "relevance",
            },
            "display_config": display_config if display_config is not None else {"sections": ["summary", "reviews"]},
        },
    )


async def test_publish_schema_succeeds(client):
    resp = await _publish(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["category_slug"] == "restoran"
    assert body["version"] == 1


async def test_republish_same_version_is_409(client):
    first = await _publish(client, version=2)
    assert first.status_code == 201
    second = await _publish(client, version=2)
    assert second.status_code == 409


async def test_new_version_is_allowed(client):
    assert (await _publish(client, version=1)).status_code == 201
    assert (await _publish(client, version=2)).status_code == 201


async def test_invalid_json_schema_is_rejected(client):
    resp = await _publish(client, json_schema={"type": "not-a-real-type"})
    assert resp.status_code == 422


async def test_invalid_search_config_is_rejected(client):
    resp = await _publish(client, search_config={"facets": [{"field": "cuisine"}]})  # missing required keys
    assert resp.status_code == 422


async def test_get_latest_returns_highest_version(client):
    await _publish(client, version=1)
    await _publish(client, version=3)
    await _publish(client, version=2)

    resp = await client.get("/api/v1/schemas/restoran/latest")
    assert resp.status_code == 200
    assert resp.json()["version"] == 3


async def test_get_latest_unknown_category_is_404(client):
    resp = await client.get("/api/v1/schemas/unknown-category/latest")
    assert resp.status_code == 404

async def _create_politician(client, name, tovrog_slug):
    resp = await client.post(
        "/api/v1/entities",
        json={
            "branch_slug": "tur-alba",
            "category_slug": "uikh-gishuun",
            "schema_version": 1,
            "name": name,
            "attributes": {"tovrog_slug": tovrog_slug, "party": "Тест нам"},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_by_district_orders_by_tovrog_then_name(client):
    await _create_politician(client, "Бат", "ub-6")
    await _create_politician(client, "Ану", "ub-3")
    await _create_politician(client, "Дорж", "ub-3")

    resp = await client.get("/api/v1/political/by-district")
    assert resp.status_code == 200
    body = resp.json()

    tovrogs = [row["tovrog_slug"] for row in body]
    assert tovrogs == sorted(tovrogs)  # grouped by district first

    ub3_names = [row["name"] for row in body if row["tovrog_slug"] == "ub-3"]
    assert ub3_names == sorted(ub3_names)  # name-ordered within a district


async def test_by_district_filters_to_one_district(client):
    await _create_politician(client, "Бат", "ub-6")
    await _create_politician(client, "Ану", "ub-3")

    resp = await client.get("/api/v1/political/by-district?tovrog_slug=ub-6")
    assert resp.status_code == 200
    body = resp.json()
    assert all(row["tovrog_slug"] == "ub-6" for row in body)
    assert len(body) == 1


async def test_by_district_excludes_non_political_branches(client):
    resp = await client.post(
        "/api/v1/entities",
        json={"branch_slug": "hool-zoog", "category_slug": "restoran", "schema_version": 1, "name": "Хаан буудал"},
    )
    assert resp.status_code == 201

    resp = await client.get("/api/v1/political/by-district")
    assert resp.json() == []

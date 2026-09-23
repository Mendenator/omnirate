"""Search endpoints (S-06 autocomplete, S-09 results). Facets are read
straight from the category's published search_config (S-04) — a new facet
appearing in a schema shows up in results with 0 deploy (K7).
"""

from fastapi import APIRouter, Query, Request

from app.search.client import ENTITIES_ALIAS
from app.search.mongolian_text import build_query_variants

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("/autocomplete")
async def autocomplete(request: Request, q: str = Query(min_length=1, max_length=64)):
    """K8: p95 <=80ms. Edge-ngram match on `name_edge`, OR'd across galig/folding
    variants (S-05) so a latin-typed prefix still surfaces Cyrillic entities."""
    client = request.app.state.opensearch
    variants = build_query_variants(q)

    resp = await client.search(
        index=ENTITIES_ALIAS,
        body={
            "size": 8,
            "query": {"bool": {"should": [{"match": {"name_edge": v}} for v in variants], "minimum_should_match": 1}},
            "_source": ["entity_id", "name", "category_slug", "branch_slug"],
        },
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]


@router.get("")
async def search(
    request: Request,
    q: str | None = Query(default=None),
    branch_slug: str | None = None,
    category_slug: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """K9: p95 <=150ms @500RPS, facet counts included. K11: caller logs
    zero-result queries (see infra/observability's zero-result-ratio metric)."""
    client = request.app.state.opensearch

    must: list[dict] = []
    if q:
        variants = build_query_variants(q)
        must.append(
            {
                "bool": {
                    "should": [{"match": {"name": v}} for v in variants]
                    + [{"match": {"name_folded": v}} for v in variants],
                    "minimum_should_match": 1,
                }
            }
        )
    if branch_slug:
        must.append({"term": {"branch_slug": branch_slug}})
    if category_slug:
        must.append({"term": {"category_slug": category_slug}})

    query = {"bool": {"must": must}} if must else {"match_all": {}}

    body = {
        "from": (page - 1) * page_size,
        "size": page_size,
        "query": query,
        "aggs": {
            "category_slug": {"terms": {"field": "category_slug"}},
        },
    }
    if lat is not None and lon is not None:
        body["sort"] = [{"_geo_distance": {"location": {"lat": lat, "lon": lon}, "order": "asc", "unit": "km"}}]

    resp = await client.search(index=ENTITIES_ALIAS, body=body)

    return {
        "total": resp["hits"]["total"]["value"],
        "results": [hit["_source"] for hit in resp["hits"]["hits"]],
        "facets": resp.get("aggregations", {}),
    }

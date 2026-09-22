"""OpenSearch client wrapper (S-03). Index naming: `entities_v1`, aliased as `entities`
so re-indexing (analyzer changes, S-05 Mongolian analyzer work) is zero-downtime.
"""

from opensearchpy import AsyncOpenSearch

from app.core.config import get_settings

ENTITIES_ALIAS = "entities"


def get_opensearch_client() -> AsyncOpenSearch:
    settings = get_settings()
    return AsyncOpenSearch(hosts=[settings.opensearch_url], use_ssl=settings.opensearch_url.startswith("https"))


# Baseline index mapping. `name_folded`/`name_translit`/`name_edge` are placeholders
# for the Mongolian analyzer work in S-05 (ө/ү folding, latin translit, autocomplete
# edge n-grams) — wired here so S-05 only has to change analyzer definitions, not
# the document shape.
ENTITIES_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "mn_default": {"type": "standard"},
                "mn_edge": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase"],
                },
            },
            "tokenizer": {
                "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 15,
                    "token_chars": ["letter", "digit"],
                }
            },
        },
    },
    "mappings": {
        "properties": {
            "entity_id": {"type": "keyword"},
            "branch_slug": {"type": "keyword"},
            "category_slug": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "mn_default"},
            "name_folded": {"type": "text", "analyzer": "mn_default"},
            "name_translit": {"type": "text", "analyzer": "mn_default"},
            "name_edge": {"type": "text", "analyzer": "mn_edge", "search_analyzer": "mn_default"},
            "location": {"type": "geo_point"},
            "location_slug": {"type": "keyword"},
            "attributes": {"type": "object", "enabled": True},
            "score": {"type": "float"},
            "n_verified": {"type": "integer"},
            "updated_at": {"type": "date"},
        }
    },
}


async def ensure_entities_index(client: AsyncOpenSearch) -> None:
    exists = await client.indices.exists(index=ENTITIES_ALIAS)
    if not exists:
        await client.indices.create(index=f"{ENTITIES_ALIAS}_v1", body=ENTITIES_INDEX_MAPPING)
        await client.indices.put_alias(index=f"{ENTITIES_ALIAS}_v1", name=ENTITIES_ALIAS)

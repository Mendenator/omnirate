"""Cosine-similarity clustering over review_embeddings (P2-10).

Acceptance: cosine>=0.92 clusters found, single-review lookup <=200ms.
pgvector's `<=>` operator returns cosine *distance* (1 - similarity), so a
similarity threshold of 0.92 is a distance threshold of 0.08 — the conversion
is centralized here rather than left for every caller to get backwards.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ReviewEmbedding

SIMILARITY_THRESHOLD = 0.92
DISTANCE_THRESHOLD = 1 - SIMILARITY_THRESHOLD


async def upsert_review_embedding(db: AsyncSession, *, review_id: str, embedding: list[float]) -> None:
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(ReviewEmbedding).values(review_id=review_id, embedding=embedding)
    stmt = stmt.on_conflict_do_update(index_elements=["review_id"], set_={"embedding": embedding})
    await db.execute(stmt)
    await db.commit()


async def find_similar_reviews(db: AsyncSession, *, embedding: list[float], limit: int = 20) -> list[tuple[str, float]]:
    """Returns (review_id, cosine_similarity) pairs above SIMILARITY_THRESHOLD,
    most-similar first."""
    rows = (
        await db.execute(
            text(
                """
                SELECT review_id, 1 - (embedding <=> :query_embedding) AS similarity
                FROM review_embeddings
                WHERE (embedding <=> :query_embedding) <= :max_distance
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
                """
            ),
            {"query_embedding": str(embedding), "max_distance": DISTANCE_THRESHOLD, "limit": limit},
        )
    ).all()
    return [(str(row.review_id), float(row.similarity)) for row in rows]

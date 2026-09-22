"""e5 embeddings for near-duplicate review clustering (P2-10).

⛔ `intfloat/e5-small` model weights need a HuggingFace download, which this
sandbox has no network access for (same shape of blocker as PaddleOCR in
app/ml/ocr.py — explicit NotImplementedError rather than a silent fake
embedding). The pgvector storage/query layer below (app/domain/models.py's
ReviewEmbedding, app/domain/embedding_service.py) is fully wired and doesn't
change when the real model is swapped in.
"""

EMBEDDING_DIM = 384  # intfloat/e5-small output dimension


def embed_text(text: str) -> list[float]:
    raise NotImplementedError(
        "e5 embedding model not installed in this environment — see docs/PROGRESS.md P2-10. "
        "Once available: SentenceTransformer('intfloat/e5-small').encode('query: ' + text)."
    )

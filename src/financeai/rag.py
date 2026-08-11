"""Week 7 reference code: document chunking, embeddings, and retrieval logic."""

from __future__ import annotations

from math import sqrt
from typing import Protocol
from uuid import uuid4

from .models import DocumentChunk


class EmbeddingProvider(Protocol):
    """Minimal protocol for an embedding model."""

    def embed(self, text: str) -> list[float]:
        """Embed text into a numeric vector."""


def split_markdown_into_chunks(
    source_name: str,
    markdown: str,
    chunk_size: int = 280,
) -> list[DocumentChunk]:
    """Chunk markdown content without relying on a specific ingestion library."""

    cleaned = " ".join(markdown.split())
    chunks: list[DocumentChunk] = []
    for start in range(0, len(cleaned), chunk_size):
        content = cleaned[start : start + chunk_size]
        chunks.append(
            DocumentChunk(
                document_id=uuid4(),
                source_name=source_name,
                content=content,
                metadata={"start_offset": str(start)},
            )
        )
    return chunks


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two vectors."""

    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def rank_chunks(
    *,
    query_embedding: list[float],
    chunk_embeddings: dict[str, list[float]],
    top_k: int = 7,
) -> list[tuple[str, float]]:
    """Rank stored embeddings the same way a vector search would."""

    scored = [
        (chunk_id, cosine_similarity(query_embedding, embedding))
        for chunk_id, embedding in chunk_embeddings.items()
    ]
    return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]

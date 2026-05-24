"""
Semantic retrieval — cosine similarity search over an in-memory vector database.
"""

import numpy as np
from typing import List, Dict, Optional
from app.services.embeddings import get_embedding
from app.config import TOP_K_DEFAULT


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Cosine similarity between two embedding vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def search(
    query: str,
    database: List[Dict],
    top_k: int = TOP_K_DEFAULT,
) -> List[Dict]:
    """
    Embed *query* and return the *top_k* most similar chunks from *database*.

    Each result dict: {id, text, similarity}
    Returns [] if the embedding API fails or database is empty.
    """
    if not database:
        return []

    query_embedding = get_embedding(query)
    if not query_embedding:
        return []

    scored = [
        {
            "id": chunk["id"],
            "text": chunk["text"],
            "similarity": cosine_similarity(query_embedding, chunk["embedding"]),
        }
        for chunk in database
    ]
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def estimate_page(chunk_id, total_pages: int = 300) -> int:
    """Rough page estimate from chunk ID (evenly distributed assumption)."""
    try:
        return max(1, min(int((int(chunk_id) / 100) * total_pages), total_pages))
    except (ValueError, TypeError):
        return 1

"""
Embedding service — single source of truth for vector generation.

Replaces the duplicate get_embedding() in core/ingestion.py and core/query.py.
Exposes `last_error` so callers can surface the real exception without
catching it themselves.
"""

from typing import List, Optional
from app.config import EMBEDDING_MODEL
from app.services.openai_client import get_client

# Last exception message — read by app.py to show real errors
last_error: Optional[str] = None


def get_embedding(text: str) -> Optional[List[float]]:
    """
    Generate an embedding vector for *text*.

    Returns the vector on success, None on failure.
    Sets `embeddings.last_error` with the exception string so callers
    can surface the real error without re-raising.
    """
    global last_error
    try:
        client = get_client()
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        last_error = None
        return response.data[0].embedding
    except Exception as exc:
        last_error = f"{type(exc).__name__}: {exc}"
        return None


def batch_embed(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Embed a list of texts, returning None for any that fail.
    Useful for bulk ingestion — keeps going even if individual chunks fail.
    """
    return [get_embedding(t) for t in texts]

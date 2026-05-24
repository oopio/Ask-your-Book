"""
Text chunking strategies.
Returns plain dicts — no embeddings, no I/O.
"""

import re
from typing import List, Dict
from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_by_sentences(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:
    """
    Split text at sentence boundaries, targeting *chunk_size* words per chunk
    with *overlap* words carried over to the next chunk.

    Returns: [{id, text, word_count}, ...]
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[Dict] = []
    current: List[str] = []
    current_wc = 0
    chunk_id = 1

    for sentence in sentences:
        words = sentence.split()
        wc = len(words)

        if current_wc + wc > chunk_size and current:
            chunk_text = " ".join(current)
            chunks.append({"id": chunk_id, "text": chunk_text, "word_count": current_wc})
            overlap_words = " ".join(current).split()[-overlap:]
            current = [" ".join(overlap_words), sentence]
            current_wc = len(overlap_words) + wc
            chunk_id += 1
        else:
            current.append(sentence)
            current_wc += wc

    if current:
        chunks.append({"id": chunk_id, "text": " ".join(current), "word_count": current_wc})

    return chunks


def chunk_fixed_size(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:
    """
    Split text into fixed-size word windows with overlap.
    Simpler than sentence-aware chunking; useful for dense technical text.
    """
    words = text.split()
    chunks: List[Dict] = []
    chunk_id = 1
    i = 0

    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunks.append({
            "id": chunk_id,
            "text": " ".join(chunk_words),
            "word_count": len(chunk_words),
        })
        i += chunk_size - overlap
        chunk_id += 1

    return chunks

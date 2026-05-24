"""
Vector database — CSV-backed storage for chunk embeddings.

Two files per document:
  book_db_<name>.csv        — id, text, word_count, embedding (JSON)
  book_db_<name>_chunks.csv — id, text, word_count  (text-only, always written)

The chunks file is the source of truth for text; the embeddings file can be
regenerated at any time without re-uploading the PDF.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Optional
from app.config import BOOKS_DIR


# ── write ──────────────────────────────────────────────────────────────────

def save(chunks: List[Dict], name: str) -> Path:
    """
    Persist *chunks* to disk.

    Always writes the text-only _chunks.csv.
    Writes embeddings to the main CSV only for chunks that have an 'embedding' key.

    Returns the path to the embeddings CSV.
    """
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    emb_path   = BOOKS_DIR / f"book_db_{name}.csv"
    chunk_path = BOOKS_DIR / f"book_db_{name}_chunks.csv"

    # Text-only file — always complete
    with open(chunk_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "word_count"])
        for c in chunks:
            w.writerow([c["id"], c["text"], c["word_count"]])

    # Embeddings file — only rows that have a vector
    with open(emb_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "word_count", "embedding"])
        for c in chunks:
            if c.get("embedding"):
                w.writerow([c["id"], c["text"], c["word_count"], json.dumps(c["embedding"])])

    return emb_path


def save_embeddings(chunks: List[Dict], emb_path: Path) -> None:
    """Overwrite the embeddings CSV with *chunks* (used during regeneration)."""
    with open(emb_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "word_count", "embedding"])
        for c in chunks:
            w.writerow([c["id"], c["text"], c["word_count"], json.dumps(c["embedding"])])


# ── read ───────────────────────────────────────────────────────────────────

def load(emb_path: str | Path) -> List[Dict]:
    """
    Load the embeddings CSV.  Returns [] if the file is empty or missing.
    Each dict: {id, text, word_count, embedding, [pages], [page_numbers]}
    """
    path = Path(emb_path)
    if not path.exists():
        return []

    database: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                chunk = {
                    "id":         row["id"],
                    "text":       row["text"],
                    "word_count": row["word_count"],
                    "embedding":  json.loads(row["embedding"]),
                }
                if "pages" in row:
                    chunk["pages"] = row["pages"]
                if "page_numbers" in row:
                    chunk["page_numbers"] = json.loads(row["page_numbers"])
                database.append(chunk)
            except (KeyError, json.JSONDecodeError):
                continue   # skip malformed rows

    return database


def load_chunks(emb_path: str | Path) -> List[Dict]:
    """
    Load the text-only _chunks.csv (no embeddings).
    Returns [] if the file doesn't exist.
    """
    chunk_path = Path(str(emb_path).replace(".csv", "_chunks.csv"))
    if not chunk_path.exists():
        return []

    chunks: List[Dict] = []
    with open(chunk_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            chunks.append({
                "id":         row["id"],
                "text":       row["text"],
                "word_count": int(row["word_count"]),
            })
    return chunks


def has_chunks_file(emb_path: str | Path) -> bool:
    """True when the text-only chunks file exists."""
    return Path(str(emb_path).replace(".csv", "_chunks.csv")).exists()


# ── scan ───────────────────────────────────────────────────────────────────

def list_databases() -> List[Path]:
    """Return all embeddings CSV paths in BOOKS_DIR (excludes _chunks files)."""
    if not BOOKS_DIR.exists():
        return []
    return sorted(
        p for p in BOOKS_DIR.glob("book_db_*.csv")
        if "_chunks" not in p.name
    )

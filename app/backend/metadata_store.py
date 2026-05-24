"""
Metadata storage and LLM-based auto-categorisation.

Each document gets a _metadata.json sidecar next to its embeddings CSV.
Schema is stable — see METADATA_SCHEMA below.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from app.config import BOOKS_DIR, CHAT_MODEL, METADATA_VERSION, METADATA_WORDS
from app.services.llm import chat_complete
from app.utils.text_utils import first_n_words


METADATA_SCHEMA = {
    "document_name": str,
    "file_path":     str,
    "categories":    list,   # max 3
    "tags":          list,   # max 10
    "summary":       str,
    "upload_date":   str,    # YYYY-MM-DD
    "processing_date": str,  # ISO 8601
    "page_count":    int,
    "word_count":    int,
    "file_size_mb":  float,
    "version":       str,
}


# ── generate ───────────────────────────────────────────────────────────────

def generate(
    document_text: str,
    document_name: str,
    page_count: int,
    word_count: int,
    csv_path: str | Path,
    file_size_mb: float = 0.0,
) -> Dict:
    """
    Use the LLM to generate categories, tags, and a summary.
    Falls back to safe defaults if the API call fails.
    """
    prompt = f"""Analyze this document and provide structured metadata.

Document: {document_name}
Content (first {METADATA_WORDS} words):
{document_text}

Return ONLY valid JSON:
{{
  "categories": ["category1", "category2"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "summary": "Brief 2-3 sentence summary..."
}}"""

    categories = ["Uncategorized"]
    tags       = ["document", "pdf"]
    summary    = ""

    try:
        content = chat_complete(
            messages=[
                {"role": "system", "content": "You are a document analysis expert. Return only valid JSON."},
                {"role": "user",   "content": prompt},
            ],
            model=CHAT_MODEL,
            temperature=0.3,
            max_tokens=500,
        )
        if content:
            # Strip markdown code fences if present
            raw = content.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            parsed     = json.loads(raw)
            categories = parsed.get("categories", categories)[:3]
            tags       = parsed.get("tags",       tags)[:10]
            summary    = parsed.get("summary",    summary)
    except Exception:
        pass   # keep fallback values

    return {
        "document_name":    document_name,
        "file_path":        str(csv_path),
        "categories":       categories,
        "tags":             tags,
        "summary":          summary,
        "upload_date":      datetime.now().strftime("%Y-%m-%d"),
        "processing_date":  datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "page_count":       page_count,
        "word_count":       word_count,
        "file_size_mb":     round(file_size_mb, 2),
        "version":          METADATA_VERSION,
    }


def make_fallback(
    document_name: str,
    csv_path: str | Path,
    page_count: int,
    word_count: int,
    file_size_mb: float = 0.0,
) -> Dict:
    """Return a minimal metadata dict without calling the API."""
    return {
        "document_name":    document_name,
        "file_path":        str(csv_path),
        "categories":       ["Uncategorized"],
        "tags":             ["document", "pdf"],
        "summary":          "",
        "upload_date":      datetime.now().strftime("%Y-%m-%d"),
        "processing_date":  datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "page_count":       page_count,
        "word_count":       word_count,
        "file_size_mb":     round(file_size_mb, 2),
        "version":          METADATA_VERSION,
    }


# ── persist ────────────────────────────────────────────────────────────────

def save(metadata: Dict, csv_path: str | Path) -> Path:
    """Write metadata to <csv_path>_metadata.json."""
    json_path = Path(str(csv_path).replace(".csv", "_metadata.json"))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    return json_path


def load(csv_path: str | Path) -> Optional[Dict]:
    """Load metadata from <csv_path>_metadata.json. Returns None if missing."""
    json_path = Path(str(csv_path).replace(".csv", "_metadata.json"))
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ── query ──────────────────────────────────────────────────────────────────

def all_categories() -> List[str]:
    """Sorted unique categories across all documents in BOOKS_DIR."""
    cats: set = set()
    for p in BOOKS_DIR.glob("book_db_*_metadata.json"):
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            cats.update(m.get("categories", []))
        except Exception:
            pass
    return sorted(cats)


def all_tags() -> List[str]:
    """Sorted unique tags across all documents in BOOKS_DIR."""
    tags: set = set()
    for p in BOOKS_DIR.glob("book_db_*_metadata.json"):
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            tags.update(m.get("tags", []))
        except Exception:
            pass
    return sorted(tags)



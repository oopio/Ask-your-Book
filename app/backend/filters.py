"""
Document filter engine.
Pure functions — no I/O, no Streamlit, no OpenAI.
"""

from datetime import datetime
from typing import List, Dict, Optional


def apply(documents: List[Dict], filters: Dict) -> List[Dict]:
    """
    Apply all active filters to *documents* and return the matching subset.

    *filters* keys (all optional):
        search      : str   — case-insensitive substring on document_name
        categories  : list  — OR match on doc['categories']
        tags        : list  — OR match on doc['tags']
        date_start  : str   — YYYY-MM-DD lower bound on upload_date
        date_end    : str   — YYYY-MM-DD upper bound on upload_date
        page_min    : int   — minimum page_count
        page_max    : int   — maximum page_count
    """
    result = documents[:]

    if filters.get("search"):
        result = _by_search(result, filters["search"])
    if filters.get("categories"):
        result = _by_categories(result, filters["categories"])
    if filters.get("tags"):
        result = _by_tags(result, filters["tags"])
    if filters.get("date_start") or filters.get("date_end"):
        result = _by_date(result, filters.get("date_start"), filters.get("date_end"))
    if filters.get("page_min") is not None or filters.get("page_max") is not None:
        result = _by_pages(result, filters.get("page_min", 0), filters.get("page_max", 999_999))

    return result


def is_active(filters: Dict) -> bool:
    """True when at least one filter criterion is set."""
    return bool(
        filters.get("search")
        or filters.get("categories")
        or filters.get("tags")
        or filters.get("date_start")
        or filters.get("date_end")
        or (filters.get("page_min", 0) > 0)
        or (filters.get("page_max", 999_999) < 999_999)
    )


# ── private ────────────────────────────────────────────────────────────────

def _by_search(docs: List[Dict], query: str) -> List[Dict]:
    q = query.lower()
    return [d for d in docs if q in d.get("document_name", "").lower()]


def _by_categories(docs: List[Dict], cats: List[str]) -> List[Dict]:
    return [d for d in docs if any(c in d.get("categories", []) for c in cats)]


def _by_tags(docs: List[Dict], tags: List[str]) -> List[Dict]:
    return [d for d in docs if any(t in d.get("tags", []) for t in tags)]


def _by_date(docs: List[Dict], start: Optional[str], end: Optional[str]) -> List[Dict]:
    result = []
    for d in docs:
        raw = d.get("upload_date", "")
        if not raw:
            continue
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d")
            if start and dt < datetime.strptime(start, "%Y-%m-%d"):
                continue
            if end and dt > datetime.strptime(end, "%Y-%m-%d"):
                continue
            result.append(d)
        except ValueError:
            continue
    return result


def _by_pages(docs: List[Dict], mn: int, mx: int) -> List[Dict]:
    return [d for d in docs if mn <= d.get("page_count", 0) <= mx]

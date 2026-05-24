"""
Miscellaneous text helpers used across the app.
No external dependencies beyond the stdlib.
"""


def first_n_words(text: str, n: int = 2000) -> str:
    """Return the first *n* words of *text*."""
    return " ".join(text.split()[:n])


def estimate_page(chunk_id, total_pages: int = 300) -> int:
    """Rough page estimate from a chunk ID (evenly-distributed assumption)."""
    try:
        return max(1, min(int((int(chunk_id) / 100) * total_pages), total_pages))
    except (ValueError, TypeError):
        return 1


def safe_filename(name: str) -> str:
    """Strip file extension and keep only filesystem-safe characters."""
    from pathlib import Path
    stem = Path(name).stem
    cleaned = "".join(c for c in stem if c.isalnum() or c in (" ", "-", "_")).rstrip()
    return cleaned or "document"

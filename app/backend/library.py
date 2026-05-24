"""
Document library — discovers all processed books on disk and returns
a unified list of book-info dicts consumed by the UI.

Each dict:
{
    name            : str
    path            : str          # absolute path to embeddings CSV
    pdf_path        : str | None   # absolute path to PDF (for viewer)
    chunks          : int          # embedded chunks (0 = needs embedding)
    words           : int
    pages           : int
    needs_embedding : bool
    metadata        : dict | None
}
"""

from pathlib import Path
from typing import List, Dict, Optional

from app.config import BOOKS_DIR, PDFS_DIR
from app.backend import vector_db, metadata_store


def list_books() -> List[Dict]:
    """Scan BOOKS_DIR and return a book-info dict for every processed document."""
    books: List[Dict] = []

    for csv_path in vector_db.list_databases():
        try:
            database   = vector_db.load(csv_path)
            total_words = sum(int(c["word_count"]) for c in database)
            book_name  = _name_from_path(csv_path.name)
            pdf_path   = _find_pdf(book_name)
            meta       = metadata_store.load(csv_path)

            # Page count: metadata is authoritative; fall back to word estimate
            if meta and meta.get("page_count", 0) > 0:
                page_count = meta["page_count"]
            elif total_words > 0:
                page_count = total_words // 250
            else:
                raw = vector_db.load_chunks(csv_path)
                page_count = sum(c["word_count"] for c in raw) // 250 if raw else 0

            books.append({
                "name":            book_name,
                "path":            str(csv_path.resolve()),
                "pdf_path":        pdf_path,
                "chunks":          len(database),
                "words":           total_words,
                "pages":           page_count,
                "needs_embedding": len(database) == 0 and vector_db.has_chunks_file(csv_path),
                "metadata":        meta,
            })
        except Exception:
            continue

    return books


# ── helpers ────────────────────────────────────────────────────────────────

def _name_from_path(filename: str) -> str:
    """book_db_ExerciseBook.csv  →  'ExerciseBook'"""
    name = filename.replace("book_db_", "").replace(".csv", "")
    for ext in ("pdf", "epub", "txt"):
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
    return name.replace("_", " ").strip()


def _find_pdf(book_name: str) -> Optional[str]:
    """
    Search data/pdfs/, Book PDFs/, and the project root for a matching PDF.
    Uses exact → substring → word-overlap matching.
    """
    search_dirs = [PDFS_DIR, Path("Book PDFs"), Path(".")]
    clean = book_name.lower().replace("_", " ").replace("-", " ").strip()

    for d in search_dirs:
        if not d.exists():
            continue
        pdfs = list(d.glob("*.pdf"))

        # exact
        for p in pdfs:
            if p.stem.lower().replace("_", " ").replace("-", " ").strip() == clean:
                return str(p.resolve())
        # substring
        for p in pdfs:
            fc = p.stem.lower().replace("_", " ").replace("-", " ").strip()
            if clean in fc or fc in clean:
                return str(p.resolve())
        # word overlap
        book_words = {w for w in clean.split() if len(w) > 2}
        best, best_score = None, 0
        for p in pdfs:
            fc = p.stem.lower().replace("_", " ").replace("-", " ").strip()
            score = len(book_words & {w for w in fc.split() if len(w) > 2})
            if score > best_score:
                best_score, best = score, p
        if best and best_score >= 1:
            return str(best.resolve())

    return None

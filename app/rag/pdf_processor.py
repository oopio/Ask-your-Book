"""
PDF / document text extraction.
Supports PDF, TXT, EPUB.  Returns plain text only — no embeddings here.
"""

import re
from pathlib import Path
from typing import Optional


def extract_text(file_path: str) -> str:
    """Auto-detect format and extract raw text."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        return _from_pdf(file_path)
    elif ext == ".txt":
        return _from_txt(file_path)
    elif ext == ".epub":
        return _from_epub(file_path)
    else:
        raise ValueError(f"Unsupported format: {ext}. Supported: .pdf .txt .epub")


def get_page_count(file_path: str) -> int:
    """Return the real page count for a PDF (0 for other formats)."""
    if not file_path.lower().endswith(".pdf"):
        return 0
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            return len(PyPDF2.PdfReader(f).pages)
    except Exception:
        return 0


def clean_text(text: str) -> str:
    """Normalise whitespace and strip null bytes."""
    text = text.replace("\x00", "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# ── private helpers ────────────────────────────────────────────────────────

def _from_pdf(file_path: str) -> str:
    try:
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except ImportError:
        raise ImportError("PyPDF2 is required: pip install PyPDF2")


def _from_txt(file_path: str) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode {file_path}")


def _from_epub(file_path: str) -> str:
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup

        book = epub.read_epub(file_path)
        parts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            parts.append(soup.get_text())
        return "\n".join(parts)
    except ImportError:
        raise ImportError("ebooklib + beautifulsoup4 required: pip install ebooklib beautifulsoup4")

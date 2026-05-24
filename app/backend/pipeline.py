"""
Document processing pipeline — orchestrates the full ingest flow.

Upload → extract → clean → chunk → embed → save → metadata

This is the only place that calls pdf_processor, chunker, embeddings,
vector_db, and metadata_store together.  app.py calls process() and
load_book() — nothing else.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.config import BOOKS_DIR, PDFS_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.rag.pdf_processor import extract_text, get_page_count, clean_text
from app.rag.chunker import chunk_by_sentences
from app.services.embeddings import get_embedding
from app.backend import vector_db, metadata_store
from app.utils.text_utils import first_n_words


# ── public API ─────────────────────────────────────────────────────────────

def process(uploaded_file) -> Tuple[List[Dict], Dict, Optional[str]]:
    """
    Full silent pipeline for a Streamlit UploadedFile.

    Returns (database, stats, pdf_dest_path).
    - database  : list of embedded chunks (may be [] if API failed)
    - stats     : dict with filename, page_count, word_count, etc.
    - pdf_dest_path : absolute path to the saved PDF copy (or None)

    Never raises — returns (None, None, None) on unrecoverable error.
    """
    # Write upload to a temp file so pdf_processor can open it
    suffix = Path(uploaded_file.name).suffix
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
    except Exception:
        return None, None, None

    try:
        # 1. Extract + clean
        text = extract_text(tmp_path)
        if not text:
            return None, None, None

        real_pages = get_page_count(tmp_path)
        text = clean_text(text)

        # 2. Chunk
        chunks = chunk_by_sentences(text, CHUNK_SIZE, CHUNK_OVERLAP)
        raw_words = sum(c["word_count"] for c in chunks)
        page_count = real_pages if real_pages > 0 else max(1, raw_words // 250)

        # 3. Embed (silent — failures tracked in embeddings.last_error)
        processed: List[Dict] = []
        for chunk in chunks:
            emb = get_embedding(chunk["text"])
            if emb:
                processed.append({**chunk, "embedding": emb})

        # 4. Save (always writes _chunks.csv; embeddings CSV only for successes)
        safe_name = _safe_name(uploaded_file.name)
        merged = []
        emb_by_id = {c["id"]: c["embedding"] for c in processed}
        for chunk in chunks:
            entry = {k: chunk[k] for k in ("id", "text", "word_count")}
            if chunk["id"] in emb_by_id:
                entry["embedding"] = emb_by_id[chunk["id"]]
            merged.append(entry)

        csv_path = vector_db.save(merged, safe_name)

        # 5. Metadata (silent fallback)
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        try:
            sample = first_n_words(text)
            meta = metadata_store.generate(
                document_text=sample,
                document_name=Path(uploaded_file.name).stem,
                page_count=page_count,
                word_count=raw_words,
                csv_path=csv_path,
                file_size_mb=file_size_mb,
            )
        except Exception:
            meta = metadata_store.make_fallback(
                document_name=Path(uploaded_file.name).stem,
                csv_path=csv_path,
                page_count=page_count,
                word_count=raw_words,
                file_size_mb=file_size_mb,
            )
        metadata_store.save(meta, csv_path)

        # 6. Copy PDF to data/pdfs for the viewer
        pdf_dest = _copy_pdf(uploaded_file)

        stats = {
            "filename":     uploaded_file.name,
            "total_chunks": len(processed),
            "total_words":  raw_words,
            "page_count":   page_count,
            "csv_path":     str(csv_path),
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        return processed, stats, pdf_dest

    except Exception:
        return None, None, None

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def load_book(csv_path: str | Path, book_name: str) -> Tuple[Optional[List[Dict]], Optional[Dict]]:
    """
    Load an existing book from its embeddings CSV.

    Returns (database, stats) — database may be [] if embeddings are missing.
    Returns (None, None) on I/O error.
    """
    try:
        database = vector_db.load(csv_path)
        total_words = sum(int(c["word_count"]) for c in database)

        meta = metadata_store.load(csv_path)
        page_count = (
            meta["page_count"]
            if meta and meta.get("page_count", 0) > 0
            else max(1, total_words // 250)
        )

        stats = {
            "filename":     book_name,
            "total_chunks": len(database),
            "total_words":  total_words,
            "page_count":   page_count,
            "csv_path":     str(csv_path),
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        return database, stats

    except Exception:
        return None, None


def regenerate_embeddings(csv_path: str | Path) -> Tuple[List[Dict], int, int]:
    """
    Re-embed all chunks from the text-only _chunks.csv and overwrite the
    embeddings CSV.

    Returns (database, n_success, n_failed).
    database is [] if all embeddings failed.
    """
    chunks = vector_db.load_chunks(csv_path)
    if not chunks:
        return [], 0, 0

    processed: List[Dict] = []
    failed = 0

    for chunk in chunks:
        emb = get_embedding(chunk["text"])
        if emb:
            processed.append({**chunk, "embedding": emb})
        else:
            failed += 1

    if processed:
        vector_db.save_embeddings(processed, Path(csv_path))

    return processed, len(processed), failed


# ── helpers ────────────────────────────────────────────────────────────────

def _safe_name(filename: str) -> str:
    """Strip extension, keep only safe characters."""
    stem = Path(filename).stem
    return "".join(c for c in stem if c.isalnum() or c in (" ", "-", "_")).rstrip() or "document"


def _copy_pdf(uploaded_file) -> Optional[str]:
    """Copy the uploaded PDF to data/pdfs/ and return the absolute path."""
    if not uploaded_file.name.lower().endswith(".pdf"):
        return None
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    dest = PDFS_DIR / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getvalue())
    return str(dest.resolve())

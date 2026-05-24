"""
Central configuration — all tuneable constants in one place.
Import from here instead of scattering magic strings across modules.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = ROOT_DIR / "data"
BOOKS_DIR  = DATA_DIR / "books"
PDFS_DIR   = DATA_DIR / "pdfs"
EMBEDS_DIR = DATA_DIR / "embeddings"   # reserved for future vector-DB migration

# ── OpenAI models ──────────────────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL      = "gpt-4o-mini"

# ── RAG pipeline ──────────────────────────────────────────────────────────
CHUNK_SIZE      = 500   # words per chunk
CHUNK_OVERLAP   = 50    # word overlap between chunks
TOP_K_DEFAULT   = 5     # default retrieval depth
METADATA_WORDS  = 2000  # words sampled for LLM categorisation

# ── Storage ────────────────────────────────────────────────────────────────
METADATA_VERSION = "1.0"

# ── UI ─────────────────────────────────────────────────────────────────────
DEFAULT_VIEW_MODE   = "split"   # 'pdf' | 'chat' | 'split'
DEFAULT_DARK_MODE   = True
PDF_VIEWER_HEIGHT   = {"pdf": 700, "split": 600}

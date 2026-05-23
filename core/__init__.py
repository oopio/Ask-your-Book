"""
Core RAG System Modules
"""

from .ingestion import (
    extract_text_from_book,
    clean_text,
    chunk_text_by_sentences,
    get_embedding,
    ingest_book,
    get_book_stats
)

from .query import (
    load_book_database,
    search_book,
    generate_answer,
    query_book
)

from .metadata import (
    generate_metadata,
    save_metadata,
    load_metadata,
    get_all_categories,
    get_all_tags
)

from .filters import (
    apply_filters,
    filter_by_category,
    filter_by_tags,
    filter_by_search,
    is_filter_active
)

__all__ = [
    # Ingestion
    'extract_text_from_book',
    'clean_text',
    'chunk_text_by_sentences',
    'get_embedding',
    'ingest_book',
    'get_book_stats',
    # Query
    'load_book_database',
    'search_book',
    'generate_answer',
    'query_book',
    # Metadata
    'generate_metadata',
    'save_metadata',
    'load_metadata',
    'get_all_categories',
    'get_all_tags',
    # Filters
    'apply_filters',
    'filter_by_category',
    'filter_by_tags',
    'filter_by_search',
    'is_filter_active',
]
